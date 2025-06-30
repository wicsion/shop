from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, XMLProduct,
    Cart, CartItem, Order, OrderItem,
    Slider, Partner, ProductReview, Wishlist
)



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_featured', 'order']
    list_filter = ['is_featured', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}
    ordering = ['order', 'name']
    fields = ['name', 'slug', 'parent', 'icon', 'description', 'is_featured', 'order']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo_preview']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}
    fields = ['name', 'slug', 'logo', 'description', 'additional_info']

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" />', obj.logo.url)
        return '-'
    logo_preview.short_description = _('Логотип')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'brand', 'price', 'old_price', 'discount_percent',
        'in_stock', 'quantity', 'is_featured', 'is_new', 'is_bestseller', 'sku'
    ]
    list_filter = [
        'category', 'brand', 'is_featured', 'is_new',
        'is_bestseller', 'in_stock'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ['name']}
    readonly_fields = ['created_at', 'updated_at', 'discount_percent', 'main_image_preview']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'brand', 'sku', 'main_image_preview')
        }),
        (_('Описание'), {
            'fields': ('short_description', 'description')
        }),
        (_('Цены и наличие'), {
            'fields': ('price', 'old_price', 'discount_percent', 'in_stock', 'quantity')
        }),
        (_('Флаги'), {
            'fields': ('is_featured', 'is_new', 'is_bestseller')
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def discount_percent(self, obj):
        if obj.has_discount:
            return f"{obj.discount_percent}%"
        return "0%"
    discount_percent.short_description = _('Скидка')

    def main_image_preview(self, obj):
        # Здесь можно добавить превью главного изображения, если оно есть в модели
        return "-"
    main_image_preview.short_description = _('Главное изображение')


@admin.register(XMLProduct)
class XMLProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'price', 'old_price', 'discount_percent',
        'in_stock', 'quantity', 'status', 'is_featured', 'is_bestseller', 'code'
    ]
    list_filter = [
        'status', 'is_featured', 'is_bestseller', 'in_stock',
        'categories', 'brand'
    ]
    search_fields = ['name', 'product_id', 'code', 'description']
    filter_horizontal = ['categories']
    readonly_fields = [
        'created_at', 'updated_at', 'main_image_preview',
        'small_image_preview', 'big_image_preview',
        'super_big_image_preview', 'discount_percent',
        'attachments_preview'
    ]
    fieldsets = (
        (None, {
            'fields': ('product_id', 'group_id', 'code', 'name', 'categories')
        }),
        (_('Описание'), {
            'fields': ('description', 'material')
        }),
        (_('Цены и наличие'), {
            'fields': ('price', 'old_price', 'discount_percent', 'in_stock', 'quantity', 'min_order_quantity')
        }),
        (_('Изображения'), {
            'fields': (
                'small_image', 'small_image_preview',
                'big_image', 'big_image_preview',
                'super_big_image', 'super_big_image_preview',
                'main_image_preview'
            )
        }),
        (_('Дополнительные фото'), {
            'fields': ('attachments_preview',),
            'classes': ('collapse',)
        }),
        (_('Характеристики'), {
            'fields': ('brand', 'status', 'weight', 'volume', 'barcode', 'size_type', 'composition')
        }),
        (_('Флаги'), {
            'fields': ('is_featured', 'is_bestseller')
        }),
        (_('Дополнительно'), {
            'fields': ('xml_data', 'attachments'),
            'classes': ('collapse',)
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def discount_percent(self, obj):
        if obj.has_discount:
            return f"{obj.discount_percent}%"
        return "0%"

    discount_percent.short_description = _('Скидка')

    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="200" />', obj.main_image)
        return '-'

    main_image_preview.short_description = _('Основное изображение')

    def small_image_preview(self, obj):
        if obj.small_image:
            return format_html('<img src="{}" width="100" />', obj.small_image)
        return '-'

    small_image_preview.short_description = _('Маленькое изображение')

    def big_image_preview(self, obj):
        if obj.big_image:
            return format_html('<img src="{}" width="150" />', obj.big_image)
        return '-'

    big_image_preview.short_description = _('Большое изображение')

    def super_big_image_preview(self, obj):
        if obj.super_big_image:
            return format_html('<img src="{}" width="200" />', obj.super_big_image)
        return '-'

    super_big_image_preview.short_description = _('Очень большое изображение')

    def attachments_preview(self, obj):
        if not obj.attachments:
            return '-'

        previews = []
        for attachment in obj.attachments:
            if attachment.get('type') == 'image' and attachment.get('image'):
                previews.append(
                    format_html(
                        '<div style="float: left; margin-right: 10px; margin-bottom: 10px;">'
                        '<img src="{}" width="150" /><br>'
                        '<small>{}</small>'
                        '</div>',
                        attachment['image'],
                        attachment.get('name', '')
                    )
                )

        if not previews:
            return '-'

        return format_html(''.join(previews))

    attachments_preview.short_description = _('Дополнительные фото')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['product', 'xml_product', 'quantity', 'total_price']
    readonly_fields = ['total_price']

    def total_price(self, obj):
        if obj.xml_product:
            return obj.xml_product.price * obj.quantity
        elif obj.product:
            return obj.product.price * obj.quantity
        return 0
    total_price.short_description = _('Общая сумма')


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
    fields = ['product', 'xml_product', 'quantity', 'price', 'total_price']
    readonly_fields = ['total_price']

    def total_price(self, obj):
        return obj.price * obj.quantity
    total_price.short_description = _('Общая сумма')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'status', 'total_price', 'first_name',
        'last_name', 'email', 'phone', 'created_at'
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
    fields = ['title', 'subtitle', 'image', 'link', 'button_text', 'is_active', 'order']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return '-'
    image_preview.short_description = _('Изображение')


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'logo_preview']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['order']
    fields = ['name', 'logo', 'link', 'is_active', 'order']

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" />', obj.logo.url)
        return '-'
    logo_preview.short_description = _('Логотип')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at', 'is_approved']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__username', 'text']
    readonly_fields = ['created_at']
    fields = ['product', 'user', 'rating', 'text', 'is_approved', 'created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'products_count', 'created_at']
    filter_horizontal = ['products']
    readonly_fields = ['created_at']

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = _('Количество товаров')


