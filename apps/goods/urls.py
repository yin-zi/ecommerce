from django.urls import path
from . import views


app_name = 'goods'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),  # 首页
    path('goods/<str:spu_id>/<str:sku_id>', views.DetailView.as_view(), name='detail'),  # 详情页
    path('list/<str:type_id>/<int:page>', views.ListView.as_view(), name='list'),  # 列表页
    path('search', views.GoodsSearchView.as_view(), name='search'),  # 全文检索框架
]
