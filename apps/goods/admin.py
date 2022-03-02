from django.contrib import admin
from django.core.cache import cache
from .models import GoodsType, GoodsSPU, GoodsSKU, GoodsImage, \
    IndexGoodsBanner, IndexPromotionBanner


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """新增或更新表中的数据时使用"""
        super().save_model(request, obj, form, change)

        # 发出任务 让celery worker重新生成首页静态页面
        from .tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清空缓存
        cache.delete('index_page_cache')

    def delete_model(self, request, obj):
        """删除表中的数据时调用"""
        super().delete_model(request, obj)

        # 发出任务 让celery worker重新生成首页静态页面
        from tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清空缓存
        cache.delete('index_page_cache')


class GoodsImageInline(admin.TabularInline):
    model = GoodsImage
    extra = 1


class GoodsSKUInline(admin.TabularInline):
    model = GoodsSKU
    extra = 1


class GoodsSPUAdmin(admin.ModelAdmin):
    inlines = [GoodsSKUInline]


admin.site.register(GoodsType)
admin.site.register(GoodsSPU, GoodsSPUAdmin)
# admin.site.register(GoodsSKU)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner)
admin.site.register(IndexPromotionBanner)
