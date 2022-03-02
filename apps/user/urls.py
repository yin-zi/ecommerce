from django.urls import path
from . import views


app_name = 'user'
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),  # 注册
    path('active/<str:token>', views.ActiveView.as_view(), name='active'),  # 用户激活
    path('login/', views.LoginView.as_view(), name='login'),  # 登录
    path('logout/', views.LogoutView.as_view(), name='logout'),  # 退出登录
    path('profile/', views.ProfileView.as_view(), name='profile'),  # 用户中心-信息页
    path('order/<int:page>', views.UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    path('address/', views.AddressView.as_view(), name='address'),  # 用户中心-地址页
    path('favorite/', views.FavoriteView.as_view(), name='favorite'),  # 用户收藏
    path('<username:username>/count/', views.UsernameView.as_view(), name='count'),  # 用户名数量
]
