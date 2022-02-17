from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator
from .models import GoodsType, GoodsSKU, GoodsSPU, GoodsImage, IndexGoodsBanner, IndexPromotionBanner
from order.models import OrderGoods


class IndexView(View):
    """首页视图 http://127.0.0.1:8000"""
    def get(self, request):
        # 从缓存中获取首页
        context = cache.get('index_page_cache')
        if context is None:
            # 获取商品类型/分类信息
            goods_types = GoodsType.objects.filter(is_delete=False)
            # 获取首页轮播商品(焦点图)信息
            index_goods_banners = IndexGoodsBanner.objects.filter(is_delete=False).order_by('index')
            # 获取首页促销活动(广告)信息
            promotion_banners = IndexPromotionBanner.objects.filter(is_delete=False).order_by('index')
            # 获取首页每个商品分类下要展示的商品
            for goods_type in goods_types:
                goods_type.spu = GoodsSPU.objects.filter(type=goods_type, is_delete=False, status=GoodsSPU.SHANGJIA)[:4]
                for spu in goods_type.spu:
                    spu.sku = GoodsSKU.objects.filter(spu=spu, is_delete=False)[0]
                    spu.sku.image = GoodsImage.objects.filter(sku=spu.sku, is_delete=False)[0]
            # 组织模板上下文,更新context
            context = {
                'goods_types': goods_types,
                'index_goods_banners': index_goods_banners,
                'promotion_banners': promotion_banners,
            }
        # 获取用户购物车中的商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:  # 判断用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        
        context.update(cart_count=cart_count)
        # 设置缓存 key value
        cache.set('index_page_cache', context, 30)
        return render(request, 'index.html', context)


class DetailView(View):
    """详情页 /goods/spu_id/sku_id"""
    def get(self, request, spu_id, sku_id):
        goods_types = GoodsType.objects.filter(is_delete=False)
        # 检验商品spu_id sku_id是否合法
        try:
            spu = GoodsSPU.objects.get(id=spu_id, is_delete=False, status=GoodsSPU.SHANGJIA)
            sku = GoodsSKU.objects.get(id=sku_id, spu=spu, is_delete=False)
        except GoodsSPU.DoesNotExist:  # 商品不存在或已删除或已下架
            return redirect(reverse('goods:index'))
        except GoodsSKU.DoseNotExist:  # 该商品spu不存在sku
            return redirect(reverse('goods:index'))
        sku.images = GoodsImage.objects.filter(sku=sku, is_delete=False)
        # 查询该sku的全部规格商品
        skus = GoodsSKU.objects.filter(spu=spu, is_delete=False)
        # 查询sku对应的图片和评论 并将其动态添加到skus中
        for s in skus:
            s.comments = OrderGoods.objects.filter(sku=s, is_delete=False).exclude(comment='')
        # 获取两个推荐sku信息
        new_skus = GoodsSKU.objects.exclude(spu=spu).filter(is_delete=False)[:2]
        for n_s in new_skus:
            n_s.images = GoodsImage.objects.filter(sku=n_s, is_delete=False)
        # 获取用户购物车中的商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:  # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史浏览记录
            # history_key = 'history_%d' % user.id
            # conn.lrem(history_key, 0, goods_id)  # 移除列表中的goods_id
            # conn.lpush(history_key, goods_id)  # 插入goods_id到列表的左侧
            # conn.ltrim(history_key, 0, 4)  # 对列表进行裁剪 只保存5条浏览记录

        context = {
            'goods_types': goods_types,
            'spu': spu,
            'sku': sku,
            'skus': skus,
            'cart_count': cart_count,
            'new_skus': new_skus,
        }

        return render(request, 'detail.html', context)


class ListView(View):
    """list/种类id/页码?sort=排序方式"""
    def get(self, request, type_id, page=1):
        goods_types = GoodsType.objects.filter(is_delete=False)
        # 获取商品种类信息
        try:
            goods_type = GoodsType.objects.get(id=type_id, is_delete=False)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))
        # 获取该分类下商品spu信息
        spus = GoodsSPU.objects.filter(type=goods_type, is_delete=False, status=GoodsSPU.SHANGJIA)

        sort_m = request.GET.get('sort', 'default')
        if sort_m == 'price':  # 按照商品价格排序
            skus = GoodsSKU.objects.filter(spu__in=spus, is_delete=False).order_by('price')
        elif sort_m == 'hot':  # 按照商品销量排序
            skus = GoodsSKU.objects.filter(spu__in=spus, is_delete=False).order_by('-sales')
        else:  # 按照默认id排序
            skus = GoodsSKU.objects.filter(spu__in=spus, is_delete=False).order_by('-id')
        for sku in skus:
            sku.images = GoodsImage.objects.filter(sku=sku, is_delete=False)
        # 对数据进行分页
        paginator = Paginator(skus, 20)
        # 获取第page页的内容,总页数paginator.num_pages
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实列对象
        skus_page = paginator.page(page)
        # 进行页码控制 页面上最多显示5个页码
        # 总页数小于5页，显示页面上所有代码
        # 如果当前页是前3页，显示1-5页
        # 如果当前页是后3页，显示后5页
        # 其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 获取新品的信息
        new_skus = GoodsSKU.objects.filter(spu__type=goods_type, is_delete=False).order_by('-create_time')[:2]
        print(new_skus)
        for n_s in new_skus:
            n_s.images = GoodsImage.objects.filter(sku=n_s, is_delete=False)
        # 获取用户购物车中的商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:  # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        context = {
            'goods_types': goods_types,
            'goods_type': goods_type,
            'sort': sort_m,
            'pages': pages,
            'skus_page': skus_page,
            'new_skus': new_skus,
            'cart_count': cart_count,
        }
        return render(request, 'list.html', context)
