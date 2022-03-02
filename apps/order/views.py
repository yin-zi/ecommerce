from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse
from django.views.generic import View
from django_redis import get_redis_connection
from datetime import datetime
from .models import OrderInfo, OrderGoods
from alipay import AliPay
from django.contrib.auth.mixins import LoginRequiredMixin
from goods.models import GoodsSKU, GoodsImage
from user.models import Address


class OrderPlaceView(LoginRequiredMixin, View):
    """提交订单页面显示"""

    def post(self, request):
        # 获取登录的用户
        user = request.user

        # 获取参数sku_ids, getlist()一个参数对应多个值
        sku_ids = request.POST.getlist('sku_ids')

        # 检验参数
        if not sku_ids:
            # 跳转到购物车页面
            return redirect(reverse('cart:show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = list()
        total_count = 0
        total_price = 0
        # 遍历sku_ids获取用户要购买的商品信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            sku.image = GoodsImage.objects.filter(sku=sku, is_delete=False)[0]
            # 获取用户所要购买的商品数量
            count = conn.hget(cart_key, sku_id)
            count = int(count)
            # 计算商品的小计
            amount = sku.price * count
            # 动态给sku增加属性count，保存购买商品的数量
            sku.count = count
            sku.amount = amount
            # 累加计算商品的总件数和总价格
            total_count += count
            total_price += amount
            # 追加
            skus.append(sku)

        # 运费 实际开发的时候 属于一个子系统
        transit_price = 5  # 此处写死

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        sku_ids = ','.join(sku_ids)

        # 组织上下文
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'addrs': addrs,
            'sku_ids': sku_ids,
        }

        # 使用模板
        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredMixin, View):
    """订单创建
    mysql事务,一组sql操作,要么都成功,要么都失败
    乐观锁,查询数据的时候不加锁，在更新时进行判断
    """

    @transaction.atomic
    def post(self, request):
        # 校验用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数,addr_id,pay_method,sku_ids
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整，请确认是否有收货地址'})

        # 校验支付方式
        if int(pay_method) not in OrderInfo.PAY_METHOD.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址是否存在
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 创建订单核心业务

        # 组织参数
        # 订单id 年+月+日+时+分+秒+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 5

        # 总数目总金额
        total_count = 0
        total_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()

        try:
            # 向df_order_info表中添加一条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             address=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # 用户的订单中有几个商品 就向df_order_goods表中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):
                    # 获取商品的信息
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        # 出现异常进行回滚rollback
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    # 从redis中获取用户所需购买的商品数量
                    count = int(conn.hget(cart_key, sku_id))

                    # 判断商品的库存
                    if count > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # 更新商品的库存和销量
                    origin_stock = sku.stock
                    new_stock = origin_stock - count
                    new_sales = sku.sales + count
                    # sku.stock = new_stock
                    # sku.sales = new_sales
                    # sku.save()

                    # 返回受影响的行数
                    # update df_goods_sku set stock=new_stock,sale=new_sales
                    # where id=sku_id and stock=origin_stock
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                        sales=new_sales)
                    if res == 0:
                        if i == 2:
                            # 尝试第三次
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
                        # 返回去接着循环
                        continue

                    # 向df_order_goods表中添加一次记录
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)

                    # 累加计算订单商品的总数量和总价格
                    amount = sku.price * count
                    total_count += count
                    total_price += amount
                    # 成功的话跳出循环
                    break
                # 更新订单信息表中的总数量和总价格
                order.total_count = total_count
                order.total_price = total_price
                order.save()

        except Exception as e:
            # 出现异常进行回滚rollback
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # 清除用户购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})


"""悲观锁
class OrderCommitView(View):
    @transaction.atomic
    def post(self, request):
        # 校验用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHOD.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址是否存在
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 创建订单核心业务

        # 组织参数
        # 订单id 年+月+日+时+分+秒+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 8

        # 总数目总金额
        total_count = 0
        total_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()

        try:
            # 向df_order_info表中添加一条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # 用户的订单中有几个商品 就向df_order_goods表中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品的信息
                try:
                    # 加锁select * from df_goods_sku where id=sku_id for update;
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                # 从redis中获取用户所需购买的商品数量
                count = int(conn.hget(cart_key, sku_id))

                # 判断商品的库存
                if count > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                # 向df_order_goods表中加入记录
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)

                # 更新商品的库存和销量
                sku.stock -= count
                sku.sales += count
                sku.save()

                # 累加计算订单商品的总数量和总价格
                amount = sku.price * count
                total_count += count
                total_price += amount

                # 更新订单信息表中的总数量和总价格
                order.total_count = total_count
                order.total_price = total_price
                order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # 清除用户购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})
"""


class OrderPayView(LoginRequiredMixin, View):
    """订单支付"""

    def post(self, request):
        # 校验用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=1, order_status=1)
        except OrderInfo.DoseNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理：使用python sdk调用支付宝的支付接口
        # 初始化
        app_private_key_string = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAsFko74d1M54lfulnSYmZ3dFM7QJVQC7lTArrRTuppag+HCkxldKtkhYUnq0JjnbRN0n7f7mCSb5yK6FdILqTowu4/ZZw/XWxF0Kt70ox5K+nmNM2peO6czpI1mFR7QTSoAkii9mmWLNYyaPCY5ly31/VKSO9qyn1XsZ4zKT8qus0ENgXQRx527egmP2pFqehWJMvDYI7hXZMZah9TgjccF/3imQCAGcMMoHAk77A0hHzQrfbX0/1gR33/blz3Utyyqqbt1t5ZR/d6Mj+iZUAbUa5PbZk+NBq5qIOQ6ZG6OOq/LgjoZEU9qATKdCoFqEODlqJlhO3SlN+ea64tU1TUwIDAQABAoIBAAGZ3aBHF45PakG7tr9ZK3dzFgK02bdKdbR6CObJAuJJI783tIaKsh64apmCMqsDcyTQXCMtuPwYaYrx3RmV+A8r5RMQUZhLgD8Y0OFyR/+uhJQDnuRkq+Wt6slfetHvEEZ5rsGcSUFW54B1JyemVf+nLBVCiM9MAzlIDgK1oMGgeyFkZLT90ehqeJf13pxFITmAW7F+1u9/unFxvsPILhQ3aLN3lw0n53Y2COBT6C7EUE4HuvZ1GYHIIpK2mcxZSDSH8bceFsnXSAxVb9MwAOW5SbEXDg7KiVqIyci9Z+b85bYAXMrGusNdDRQqoh48HAb8DL/G7xCdvW7yZnfv9+kCgYEA+QXBK+/lpxp0KQ/AcibY9mpxtSrRppq6sX4cEaKVzxQSHM3KLQtr8wH6Utpffp/vBR9mggWYUl9BYkvHvN82tzUm9cOcaWXiPllfZiy34UnPWynspu90DEUGTIlvbh8YZtMpGfOlqEh2AJWYfNygL7LDB8LcfIFDRVBVZeDPh8cCgYEAtUoceEY7K0kPZwA4PHhPGanmcqJaWIk10lUuiSFcvSnBMo+6vPjfS+jkwXejBM9lKIEY/TIbeJadL1w/zPUC2qSCQGLV6AODXzAeO5cFh2B7fcDbv9Lksn/821C4gbU6ZqBG2CQDt4ERW6DSE56Vn4AhTWimTXrXaJ+9ZMFfUBUCgYBZG3kLGtXHnMyyIMPRVRtP2bkEheTtQ/LILoMmwFHw/pKYof7VbX/cPfnwCdof+mTSJXFN12ixGQrRfKJlcE4o8qkVSkC+6kkx3FMpwZiu0fWT/oWDGq4g8dYWLxujgRb/PFI5yhieBgfLn7wn+d6MEuB893pkRvDmbZ+RTAeW4wKBgDrCjLvHN8Jt6doezht7e1f8I7+gM9xijNlh1rWH5MFDWWWEBKjfmbDHCe5TUrlqZ4VbYrgel5zcZJJHOj66Y3RuwfEQl/iduuUNeZ8i8h3Q/fXintdsCch5h4Gmhkc0cHt3E79W3QWLhg7G75CAZErQgvrOIqkWWd+FdyPDMZuJAoGABC8AGPErOo5+FjpWQR8TitxQ2X/SZHKI00Q1Bm5Flqr1yCcoJmOXH1RXRQymlps8Fkz4jZoEl+o6R2iJSzk2pwncalWtwQxvDVmiK0YRzWl+CWaGZC1eyZoK0YzG5J2KN3OM3f+6wRpZtl1oXJXI4NK5OUrbpp61ePYsiROkGZc=
 -----END RSA PRIVATE KEY-----
        """

        alipay_public_key_string = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsqovQPv/1rPEf178Brxf9Zti9l6WZz6xzUGXAjiPKZle2nOS8NsACT/VqMj7KrHJcZKVJoDrrJdoDLJHC6Vt+TMYcpnrKZIBfnwfTDwzoYxj/fpxHexz1oXV2rwkbdbJtBT5YazN6eRnrQnk8/08l+iX26y4byu+OsAzN3q6LgTRo4BMu9klYBxRU+7M/cNOT3dCD9cfASc2ZHJ0Q/GtBiGQs/uAQDci7JXAWYByfUbEjpmMsYOPK4eUBjyvCD5hAEWkogIFwLXaXT1rxfwt6h3rC+chWBDKUyTGnuwkWpGyfSS/pDC21qrjfdBUSKu/ntHaLKAkE6N/HHhQVzW79wIDAQAB
-----END PUBLIC KEY-----"""

        alipay = AliPay(
            appid="2016102100732390",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )

        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject="天天图书%s" % order_id,
            return_url=None,
            notify_url=None  # 可选 不填则使用默认notify url
        )

        # 返回应答
        pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class OrderCheckView(LoginRequiredMixin, View):
    """order/pay 查看订单支付的结果"""

    def post(self, request):
        # 校验用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=1, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理 调用支付宝的支付接口
        # 初始化
        app_private_key_string = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAsFko74d1M54lfulnSYmZ3dFM7QJVQC7lTArrRTuppag+HCkxldKtkhYUnq0JjnbRN0n7f7mCSb5yK6FdILqTowu4/ZZw/XWxF0Kt70ox5K+nmNM2peO6czpI1mFR7QTSoAkii9mmWLNYyaPCY5ly31/VKSO9qyn1XsZ4zKT8qus0ENgXQRx527egmP2pFqehWJMvDYI7hXZMZah9TgjccF/3imQCAGcMMoHAk77A0hHzQrfbX0/1gR33/blz3Utyyqqbt1t5ZR/d6Mj+iZUAbUa5PbZk+NBq5qIOQ6ZG6OOq/LgjoZEU9qATKdCoFqEODlqJlhO3SlN+ea64tU1TUwIDAQABAoIBAAGZ3aBHF45PakG7tr9ZK3dzFgK02bdKdbR6CObJAuJJI783tIaKsh64apmCMqsDcyTQXCMtuPwYaYrx3RmV+A8r5RMQUZhLgD8Y0OFyR/+uhJQDnuRkq+Wt6slfetHvEEZ5rsGcSUFW54B1JyemVf+nLBVCiM9MAzlIDgK1oMGgeyFkZLT90ehqeJf13pxFITmAW7F+1u9/unFxvsPILhQ3aLN3lw0n53Y2COBT6C7EUE4HuvZ1GYHIIpK2mcxZSDSH8bceFsnXSAxVb9MwAOW5SbEXDg7KiVqIyci9Z+b85bYAXMrGusNdDRQqoh48HAb8DL/G7xCdvW7yZnfv9+kCgYEA+QXBK+/lpxp0KQ/AcibY9mpxtSrRppq6sX4cEaKVzxQSHM3KLQtr8wH6Utpffp/vBR9mggWYUl9BYkvHvN82tzUm9cOcaWXiPllfZiy34UnPWynspu90DEUGTIlvbh8YZtMpGfOlqEh2AJWYfNygL7LDB8LcfIFDRVBVZeDPh8cCgYEAtUoceEY7K0kPZwA4PHhPGanmcqJaWIk10lUuiSFcvSnBMo+6vPjfS+jkwXejBM9lKIEY/TIbeJadL1w/zPUC2qSCQGLV6AODXzAeO5cFh2B7fcDbv9Lksn/821C4gbU6ZqBG2CQDt4ERW6DSE56Vn4AhTWimTXrXaJ+9ZMFfUBUCgYBZG3kLGtXHnMyyIMPRVRtP2bkEheTtQ/LILoMmwFHw/pKYof7VbX/cPfnwCdof+mTSJXFN12ixGQrRfKJlcE4o8qkVSkC+6kkx3FMpwZiu0fWT/oWDGq4g8dYWLxujgRb/PFI5yhieBgfLn7wn+d6MEuB893pkRvDmbZ+RTAeW4wKBgDrCjLvHN8Jt6doezht7e1f8I7+gM9xijNlh1rWH5MFDWWWEBKjfmbDHCe5TUrlqZ4VbYrgel5zcZJJHOj66Y3RuwfEQl/iduuUNeZ8i8h3Q/fXintdsCch5h4Gmhkc0cHt3E79W3QWLhg7G75CAZErQgvrOIqkWWd+FdyPDMZuJAoGABC8AGPErOo5+FjpWQR8TitxQ2X/SZHKI00Q1Bm5Flqr1yCcoJmOXH1RXRQymlps8Fkz4jZoEl+o6R2iJSzk2pwncalWtwQxvDVmiK0YRzWl+CWaGZC1eyZoK0YzG5J2KN3OM3f+6wRpZtl1oXJXI4NK5OUrbpp61ePYsiROkGZc=
-----END RSA PRIVATE KEY-----"""

        alipay_public_key_string = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsqovQPv/1rPEf178Brxf9Zti9l6WZz6xzUGXAjiPKZle2nOS8NsACT/VqMj7KrHJcZKVJoDrrJdoDLJHC6Vt+TMYcpnrKZIBfnwfTDwzoYxj/fpxHexz1oXV2rwkbdbJtBT5YazN6eRnrQnk8/08l+iX26y4byu+OsAzN3q6LgTRo4BMu9klYBxRU+7M/cNOT3dCD9cfASc2ZHJ0Q/GtBiGQs/uAQDci7JXAWYByfUbEjpmMsYOPK4eUBjyvCD5hAEWkogIFwLXaXT1rxfwt6h3rC+chWBDKUyTGnuwkWpGyfSS/pDC21qrjfdBUSKu/ntHaLKAkE6N/HHhQVzW79wIDAQAB
-----END PUBLIC KEY-----"""

        alipay = AliPay(
            appid="2016102100732390",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )

        cnt = 0
        while True:
            # 调用支付宝的交易查询接口
            response = alipay.api_alipay_trade_query(order_id)
            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4  # 待评价状态
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                if cnt == 3:
                    print(response)
                    return JsonResponse({'res': 5, 'errmsg': '查询超时'})
                cnt += 1
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class CommentView(LoginRequiredMixin, View):
    """订单评论"""
    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order'))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count * order_sku.price
            order_sku.amount = amount
            order_sku.image = GoodsImage.objects.filter(sku=order_sku.sku, is_delete=False)[0]
        # 动态给order_sku增加属性order_skus,保存商品订单信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, 'order_comment.html', {'order': order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order'))

        # 获取评论条数
        total_count = request.POST.get('total_count')
        total_count = int(total_count)

        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get('sku_%d' % i)
            # 获取商品评论
            content = request.POST.get('content_%d' % i)
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse('user:order', kwargs={'page': 1}))

# qoqamp8198@sandbox.com
# 111111
