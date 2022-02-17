from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


class GoodsType(BaseModel):
    """商品类型模型类"""
    goods_type = models.CharField(max_length=20, verbose_name='商品类型')
    logo = models.CharField(max_length=20, blank=True, verbose_name='logo标识')
    image = models.ImageField(upload_to='goods_type_images', blank=True, verbose_name='商品类型图片路径')

    class Meta:
        db_table = 'ec_goods_type'
        verbose_name = '商品类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.goods_type)


class GoodsSPU(BaseModel):
    XIAJIA = 0
    SHANGJIA = 1

    """商品SPU模型类"""
    GOODS_STATUS_CHOICES = (
        (XIAJIA, '下架'),
        (SHANGJIA, '上架'),
    )

    type = models.ForeignKey('goods.GoodsType', verbose_name='商品种类', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='商品SPU')
    desc = models.JSONField(blank=True, verbose_name='商品介绍')
    detail = HTMLField(blank=True, verbose_name='商品详情')
    status = models.SmallIntegerField(default=SHANGJIA, choices=GOODS_STATUS_CHOICES, verbose_name='商品状态')

    class Meta:
        db_table = 'ec_goods_spu'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.name)


class GoodsSKU(BaseModel):
    """商品SKU模型类"""
    spu = models.ForeignKey('goods.GoodsSPU', verbose_name='商品SPU', on_delete=models.CASCADE)
    # name = models.CharField(max_length=100, verbose_name='商品SKU')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品单价')
    stock = models.IntegerField(default=1, verbose_name='商品库存')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    unite = models.CharField(max_length=20, verbose_name='商品单位')
    category = models.CharField(max_length=50, verbose_name="商品系列规格型号")

    class Meta:
        db_table = 'ec_goods_sku'
        verbose_name = '商品SKU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.spu) + str(self.category)


class GoodsImage(BaseModel):
    """商品图片模型类"""
    sku = models.ForeignKey('goods.GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='goods_images', verbose_name='商品图片路径')

    class Meta:
        db_table = 'ec_goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.sku)


class IndexGoodsBanner(BaseModel):
    """首页轮播商品展示模型类"""
    sku = models.ForeignKey('goods.GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='banner_images', verbose_name='首页焦点图图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'ec_index_banner'
        verbose_name = '首页焦点图轮播商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.sku)


# class IndexTypeGoodsBanner(BaseModel):
#     """首页分类商品展示模型类"""
#     DISPLAY_TYPE_CHOICES = (
#         (0, '标题'),
#         (1, '图片'),
#     )

#     type = models.ForeignKey('goods.GoodsType', verbose_name='商品类型', on_delete=models.CASCADE)
#     sku = models.ForeignKey('goods.GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
#     display_type = models.SmallIntegerField(default=1, choices=DISPLAY_TYPE_CHOICES, verbose_name='展示类型')
#     index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

#     class Meta:
#         db_table = 'ec_index_goods_type_show'
#         verbose_name = '主页分类展示商品'
#         verbose_name_plural = verbose_name

#     def __str__(self):
#         return str(self.type) + '-' + str(self.sku)


class IndexPromotionBanner(BaseModel):
    """首页促销活动模型类"""
    name = models.CharField(max_length=100, verbose_name='活动名称')
    url = models.CharField(max_length=255, verbose_name='活动链接')
    image = models.ImageField(upload_to='banner_images', verbose_name='活动图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'ec_index_promotion'
        verbose_name = '主页促销活动'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.name)
