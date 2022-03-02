from django.db import models
from db.base_model import BaseModel


class OrderInfo(BaseModel):
    """订单模型类"""
    PAY_METHOD = {
        1: '支付宝',
        2: '微信支付',
        3: '银联支付',
        4: '货到付款',
    }

    PAY_METHOD_CHOICES = (
        (1, '支付宝'),
        (2, '微信支付'),
        (3, '银联支付'),
        (4, '货到付款'),
    )

    ORDER_STATUS = {
        1: '待支付',
        2: '待发货',
        3: '待收货',
        4: '待评价',
        5: '已完成',
    }

    ORDER_STATUS_CHOICES = (
        (1, '待支付'),
        (2, '待发货'),
        (3, '待收货'),
        (4, '待评价'),
        (5, '已完成'),
    )

    EXPRESS = {
        1: "京东快递",
        2: "顺丰快递",
        3: "申通快递",
        4: "圆通快递",
        5: "中通快递",
        6: "韵达快递",
        7: "天天快递",
        8: "百世快递",
        9: "EMS",
        10: "其它",
    }

    EXPRESS_CHOICES = {
        (1, "京东快递"),
        (2, "顺丰快递"),
        (3, "申通快递"),
        (4, "圆通快递"),
        (5, "中通快递"),
        (6, "韵达快递"),
        (7, "天天快递"),
        (8, "百世快递"),
        (9, "EMS"),
        (10, "其它"),
    }

    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单id')
    trade_no = models.CharField(max_length=128, default='', verbose_name='支付编号')
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=1, verbose_name='支付方式')
    express = models.SmallIntegerField(choices=EXPRESS_CHOICES, default=10, verbose_name="配送方式")
    total_count = models.IntegerField(default=1, verbose_name='商品总数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
    transit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单运费')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name='订单状态')
    user = models.ForeignKey('user.User', verbose_name='用户', on_delete=models.CASCADE)
    address = models.ForeignKey('user.Address', verbose_name='地址', on_delete=models.CASCADE)

    class Meta:
        db_table = 'ec_order_info'
        verbose_name = '订单信息'
        verbose_name_plural = verbose_name


class OrderGoods(BaseModel):
    """订单商品模型类"""
    order = models.ForeignKey('order.OrderInfo', verbose_name='订单', on_delete=models.CASCADE)
    sku = models.ForeignKey('goods.GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
    count = models.IntegerField(default=1, verbose_name='商品数量')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品单价')
    comment = models.CharField(max_length=300, default='', verbose_name='商品评论')

    class Meta:
        db_table = 'ec_order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name
