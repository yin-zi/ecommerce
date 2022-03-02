from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.views.generic import View
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django_redis import get_redis_connection
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous.exc import SignatureExpired
import re
from .tasks import send_register_active_email
from .models import User, Address
from goods.models import GoodsSKU, GoodsImage
from order.models import OrderInfo, OrderGoods


class RegisterView(View):
    """注册类视图"""

    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """进行注册处理"""
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_pwd = request.POST.get('confirm_pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据的校验
        if not all([username, password, email]):  # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if password != confirm_pwd:
            return render(request, 'register.html', {'errmsg': '两次输入的密码不一致'})
        # 邮箱校验
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请勾选同意协议'})
        # 检验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:  # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 进行业务处理 进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0  # 将用户设置为未激活状态
        user.save()
        # 发送激活邮件到/user/active/包含用户身份的加密token
        # 加密用户的身份信息 生成激活token
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        token = serializer.dumps(user.id)
        # 异步发送邮件
        send_register_active_email.delay(email, username, token)
        # 返回应答
        return redirect(reverse('goods:index'))


class ActiveView(View):
    """用户激活视图"""

    def get(self, request, token):
        # 进行解密，获取激活的用户信息
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        try:  # 获取激活用户id
            user_id = serializer.loads(token, max_age=3600)  # 一小时激活链接过期
            user = User.objects.get(id=user_id)
        except SignatureExpired:
            return HttpResponse('激活链接过期')
        except User.DoesNotExist:
            return HttpResponse('激活链接失效')
        user.is_active = 1
        user.save()
        login(request, user)
        # 跳转到网站首页
        return redirect(reverse('goods:index'))


class LoginView(View):
    """登录视图"""

    def get(self, request):
        """显示登录页面"""
        # 判断是否记住用户名
        username = ''
        checked = ''
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录校验"""
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 校验数据 条件成立 数据不完整
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '请输入用户名和密码'})
        # 业务处理
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                # 用户已激活
                login(request, user)  # 记住用户的登录状态
                # 获取登录后所要跳转的地址 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到next_url
                response = redirect(next_url)
                if request.POST.get('remember') == 'on':  # 记住用户名
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:  # 用户未激活
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'login.html', {'errmsg': '请先激活用户'})
        return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# /user/logout
class LogoutView(View):
    """退出登录视图"""

    def get(self, request):
        logout(request)  # 清除用户的session信息
        return redirect(reverse('goods:index'))  # 跳转到首页


# /user
class ProfileView(LoginRequiredMixin, View):
    """用户中心-信息页"""

    # login_url = '/user/login/'
    # redirect_field_name = 'next'

    def get(self, request):
        """显示用户信息"""
        # request.user.is_authenticate()
        # 如果用户未登录->AnonymousUser类的一个实例
        # 如果用户登录->User类的一个实例
        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传递给模板
        # 获取用户个人信息
        user = request.user
        address = Address.objects.get_default_address(user)
        # 获取用户最近浏览记录
        con = get_redis_connection('history')
        history_key = 'history_%d' % user.id
        # 获取用户最近浏览的5个商品id，使用connection的lrange的方法
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库中查询用户浏览的商品的具体信息
        goods_li = []
        for sku_id in sku_ids:
            try:
                goods = GoodsSKU.objects.get(id=sku_id, is_delete=False)
            except GoodsSKU.DoesNotExist:
                pass
            else:
                goods_li.append(goods)
        # 组织上下文
        context = {
            'user': user,
            'address': address,
            'goods_li': goods_li,
        }
        return render(request, 'user_center_info.html', context)

    def post(request):
        return HttpResponse('post 用户信息')


class UserOrderView(LoginRequiredMixin, View):
    """/user/order 用户中心-订单页"""

    def get(self, request, page=1):
        # 获取用户订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取商品订单信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计 动态给order_sku增加amount属性,保存订单商品的小计
                order_sku.amount = order_sku.count * order_sku.price
                order_sku.image = GoodsImage.objects.filter(sku=order_sku.sku, is_delete=False)[0]

            # 动态给order增加amount属性, 保存订单商品的信息
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.order_skus = order_skus
            order.total_pay = order.total_price + order.transit_price

        # 分页
        paginator = Paginator(orders, 4)
        if page > paginator.num_pages:
            page = 1
        # 获取page页的Page实列对象
        order_page = paginator.page(page)
        # 进行页码控制 页面上最多显示5个页码
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            'order_page': order_page,
            'pages': pages,
        }
        # 使用模板
        return render(request, 'user_center_order.html', context)


class AddressView(LoginRequiredMixin, View):
    """/user/address 用户中心-地址页"""

    def get(self, request):
        # 获取用户的默认收获地址
        # 获取登录用户对应的User对象
        user = request.user
        address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        """地址的添加"""
        # 接收数据
        receiver = request.POST.get('receiver')
        address = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 校验数据 判断数据完整性
        if not all([receiver, address, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'^1[356789]\d{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '请填写正确的手机号'})
        # 业务处理 地址添加 如果用户已存在默认地址 不作为默认地址添加 反之作为默认地址添加
        user = request.user
        if Address.objects.get_default_address(user):
            is_default = False
        else:
            is_default = True
        # 添加地址
        print(user, receiver, address, zip_code, phone, is_default)
        Address.objects.create(user=user,
                               receiver=receiver,
                               address=address,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答，刷新页面地址
        return redirect(reverse('user:address'))


class FavoriteView(LoginRequiredMixin, View):
    def get(request):
        return HttpResponse('get 用户收藏')

    def post(request):
        return HttpResponse('post 用户收藏')


class UsernameCountView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code': 0, 'count': count, 'msg': 'ok'})

class View(View):
    pass
