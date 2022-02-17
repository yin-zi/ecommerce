from django.contrib import admin
from .models import User, Address, UserFavorite


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1


class UserAdmin(admin.ModelAdmin):
    inlines = [AddressInline]
    search_fields = ['username', 'nickname']


admin.site.register(User, UserAdmin)
# admin.site.register(Address)
admin.site.register(UserFavorite)
