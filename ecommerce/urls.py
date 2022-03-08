"""ecommerce URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from django.urls import register_converter
# from utils.converters import UsernameConverter


# register_converter(UsernameConverter, 'username')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('', include('apps.goods.urls'), name='goods'),  # 商品模块
    path('cart/', include('apps.cart.urls'), name='cart'),  # 购物车模块
    path('order/', include('apps.order.urls'), name='order'),  # 订单模块
    path('user/', include('apps.user.urls'), name='user'),  # 用户模块
    path('captcha/', include('apps.captcha.urls'), name='captcha'),
]
