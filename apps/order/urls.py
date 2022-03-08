from django.urls import path
from . import views

app_name = 'order'
urlpatterns = [
    path('place', views.OrderPlaceView.as_view(), name='place'),  # 提交订单页面
    path('buy', views.BuyPlaceView.as_view(), name='buy'),  # 立即购买按钮
    path('commit', views.OrderCommitView.as_view(), name='commit'),  # 订单创建
    path('pay', views.OrderPayView.as_view(), name='pay'),  # 订单支付
    path('check', views.OrderCheckView.as_view(), name='check'),  # 查询交易结果
    path('comment/<str:order_id>', views.CommentView.as_view(), name='comment'),  # 订单评论
]
