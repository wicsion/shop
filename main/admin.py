from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Category, Product, ProductImage, ProductAttribute, ProductAttributeValue,
    Brand, Cart, CartItem, Order, OrderItem, Slider, Partner
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_main', 'order']
    ordering = ['order']


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ['attribute', 'value']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_featured', 'order']
    list_filter = ['is_featured', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}
    ordering = ['order', 'name']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo_preview']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

    def logo_preview(self, obj):
        if obj.logo:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="50" />', obj.logo.url)
        return '-'

    logo_preview.short_description = _('Логотип')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'brand', 'price', 'old_price', 'in_stock',
        'quantity', 'is_featured', 'is_new', 'is_bestseller'
    ]
    list_filter = [
        'category', 'brand', 'is_featured', 'is_new', 'is_bestseller', 'in_stock'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ['name']}
    inlines = [ProductImageInline, ProductAttributeValueInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'brand', 'sku')
        }),
        (_('Описание'), {
            'fields': ('short_description', 'description')
        }),
        (_('Цены и наличие'), {
            'fields': ('price', 'old_price', 'in_stock', 'quantity')
        }),
        (_('Флаги'), {
            'fields': ('is_featured', 'is_new', 'is_bestseller')
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['product', 'quantity', 'total_price']
    readonly_fields = ['total_price']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'total_price', 'total_quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_key']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']

    def total_price(self, obj):
        return obj.total_price

    total_price.short_description = _('Общая сумма')

    def total_quantity(self, obj):
        return obj.total_quantity

    total_quantity.short_description = _('Общее количество')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'price', 'total_price']
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'status', 'total_price', 'first_name', 'last_name',
        'email', 'phone', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'first_name', 'last_name', 'email', 'phone']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key', 'status')
        }),
        (_('Контактная информация'), {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        (_('Доставка'), {
            'fields': ('address', 'comment')
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_price(self, obj):
        return obj.total_price

    total_price.short_description = _('Общая сумма')


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'image_preview']
    list_filter = ['is_active']
    search_fields = ['title', 'subtitle']
    ordering = ['order']

    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return '-'

    image_preview.short_description = _('Изображение')


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'logo_preview']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['order']

    def logo_preview(self, obj):
        if obj.logo:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="50" />', obj.logo.url)
        return '-'

    logo_preview.short_description = _('Логотип')