from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel
from datetime import date


class User(AbstractUser, BaseModel):
    """用户模型类
    继承django的AbstractUser 使用django自带的认证系统
    """
    G_SECRECY = 0
    MALE = 1
    FEMALE = 2
    GENDER_CHOICES = (
        (G_SECRECY, "保密"),
        (MALE, "男"),
        (FEMALE, "女"),
    )

    nickname = models.CharField(max_length=20, blank=True, default="nickname", verbose_name="昵称")
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, default=G_SECRECY, verbose_name="性别")
    birthday = models.DateField(default=date.today, blank=True, verbose_name="生日")

    class Meta:
        db_table = 'ec_user'
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name


class AddressManager(models.Manager):
    """地址模型管理类"""
    # 1.改变原有的查询结果:all()
    # 2.封装方法:用户操作模型类对应的数据表（增删改查）
    def get_default_address(self, user):
        """获取用户的默认收获地址"""
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:  # 不存在默认收货地址
            address = None
        return address


class Address(BaseModel):
    """地址模型类
    用户与地址是一对多的关系"""
    user = models.ForeignKey('user.User', verbose_name='所属用户', on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    address = models.CharField(max_length=255, verbose_name='收货地址')
    zip_code = models.CharField(max_length=6, blank=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    # 自定义一个模型管理类对象
    objects = AddressManager()

    class Meta:
        db_table = 'ec_address'
        verbose_name = '收货地址'
        verbose_name_plural = verbose_name


class UserFavorite(BaseModel):
    user = models.ForeignKey('user.User', verbose_name='用户', on_delete=models.CASCADE)
    sku = models.ForeignKey('goods.GoodsSKU', verbose_name='收藏商品SKU', on_delete=models.CASCADE)

    class Meta:
        db_table = 'ec_user_favorite'
        verbose_name = '用户收藏'
        verbose_name_plural = '用户收藏'
