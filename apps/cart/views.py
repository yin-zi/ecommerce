from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from django_redis import get_redis_connection
from goods.models import GoodsSKU, GoodsImage
from django.contrib.auth.mixins import LoginRequiredMixin


# 添加到购物车
# 1.请求方式，采用ajax,post
# 涉及数据的修改（增删改查），采用post
# 涉及数据的获取，采用get
# 2.传递参数：商品id（sku_id） 商品数量（count）
# ajax发起的请求都在后台，在浏览器中看不到效果，因此不能使用mixin

class CartInfoView(LoginRequiredMixin, View):
    """购物车页面显示"""

    def get(self, request):
        # 获取登录的用户
        user = request.user

        # 获取用户购物车中商品的信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 返回字典{'商品id': 商品数量}
        cart_dict = conn.hgetall(cart_key)

        # 遍历获取商品的信息
        skus = list()
        # 保存用户购物车中商品的总数目和总价格
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id, is_delete=False)
            sku.images = GoodsImage.objects.filter(sku=sku, is_delete=False)
            # 计算商品的小计 动态给sku对象增加一个属性amount
            sku.amount = sku.price * int(count)
            print(sku.amount)
            # 动态给sku对象增加一个属性count,保存购物车中对应商品的数量
            sku.count = int(count)
            skus.append(sku)
            # 累计商品的总数目和总价格
            total_count += int(count)
            total_price += sku.amount

        # 组织参数
        context = {
            'total_count': total_count,
            'total_price': total_price,
            'skus': skus,
        }

        return render(request, 'cart.html', context)


class CartAddView(View):
    """购物车记录添加"""

    def post(self, request):
        """购物车记录添加"""
        # 检验用户是否登录
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # if count <= 0:
        #     return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id, is_delete=False)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理 添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 先尝试获取sku_id的值-> hget(name,value)
        # 如果sku_id在hash中不存在，hget返回none
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            # 累加购物车商品的数目
            count += int(cart_count)
        # 检验商品库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        conn.hset(cart_key, sku_id, count)
        # 设置hash中sku_id对应的值  hset(name,key,value)
        # hset->如果sku_id已经存在，更新数据，如果sku_id不存在，添加数据
        # 计算用户购物车商品的条目数
        total_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'message': '添加成功'})


# 采用ajax post请求
# 前端需要传递的参数：商品id(sku_id),更新的商品数量(amount)
class CartUpdateView(View):
    """购物车记录更新"""

    def post(self, request):
        # 检验用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        if count < 0:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理 更新购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        # 更新
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'message': '添加成功'})

# 采用ajax post请求
# 前端需要传递的参数：商品id(sku_id)
class CartDeleteView(View):
    """购物车记录删除"""

    def post(self, request):
        # 校验用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 数据的校验
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的商品id'})

        # 校验商品是否存在
        try:
            GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 业务处理 删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 删除 hdel
        conn.hdel(cart_key, sku_id)

        # 计算用户购物车中商品的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 3, 'total_count': total_count, 'message': '删除成功'})
