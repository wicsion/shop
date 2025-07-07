from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, XMLProduct,
    Cart, CartItem, Order, OrderItem,
    Slider, Partner, ProductReview, Wishlist
)
from django.db.models import Q
from django.urls import path
from django.views.decorators.http import require_GET

import logging

logger = logging.getLogger(__name__)


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
        'name', 'category', 'brand', 'price', 'old_price',
        'in_stock', 'quantity', 'is_featured', 'is_new', 'is_bestseller'
    ]
    list_filter = [
        'category', 'brand', 'is_featured', 'is_new',
        'is_bestseller', 'in_stock'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ['name']}
    readonly_fields = ['created_at', 'updated_at']
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


class CategoryFilter(admin.SimpleListFilter):
    title = 'Категория'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return [
            (cat.id, cat.name)
            for cat in Category.objects.all().order_by('name')
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(categories__id=self.value())
        return queryset


@admin.register(XMLProduct)
class XMLProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'price', 'old_price', 'display_categories',
        'in_stock', 'status', 'is_featured', 'is_bestseller', 'display_discount'
    ]
    list_filter = [
        CategoryFilter,
        'status', 'is_featured', 'is_bestseller', 'in_stock',
        'categories', 'brand_link',
        'made_in_russia', 'is_eco', 'for_kids', 'is_profitable',
        'gender', 'requires_marking', 'individual_packaging',
        'replaceable_refill', 'application_type', 'mechanism_type',
        'cover_type', 'format_size', 'page_count', 'marking_type',
        'packaging_type', 'umbrella_type', 'has_lining'
    ]
    search_fields = [
        'name', 'product_id', 'code', 'barcode', 'material',
        'collection', 'stock_marking', 'xml_id'
    ]
    filter_horizontal = ['categories']
    readonly_fields = [
        'created_at', 'updated_at', 'main_image_preview',
        'attachments_preview', 'discount_percent_display'
    ]
    fieldsets = (
        (None, {
            'fields': ('product_id', 'code', 'name', 'categories', 'brand_link')
        }),
        (_('Описание'), {
            'fields': ('description', 'material', 'collection')
        }),
        (_('Цены и наличие'), {
            'fields': (
                'price', 'old_price', 'discount_percent_display',
                'in_stock', 'quantity', 'sizes_available'
            )
        }),
        (_('Изображения'), {
            'fields': ('main_image_preview', 'attachments_preview')
        }),
        (_('Основные характеристики'), {
            'fields': (
                'status', 'weight', 'volume', 'barcode', 'dimensions',
                'gender', 'made_in_russia', 'is_eco', 'for_kids', 'is_profitable',
                'video_link', 'stock_marking'
            )
        }),
        (_('Технические параметры'), {
            'fields': (
                'application_type', 'mechanism_type', 'ball_diameter',
                'refill_type', 'replaceable_refill', 'format_size',
                'cover_type', 'block_color', 'edge_type', 'page_count',
                'calendar_grid', 'ribbon_color', 'box_size', 'density',
                'expiration_date', 'pantone_color', 'cover_material', 'block_number',
                'dating', 'fit', 'cut', 'lining', 'has_lining', 'umbrella_type',
                'marking_type', 'packaging_type', 'requires_marking', 'individual_packaging'
            ),
            'classes': ('collapse',)
        }),
        (_('Флаги'), {
            'fields': ('is_featured', 'is_bestseller', 'was_imported')
        }),
        (_('Дополнительно'), {
            'fields': ('xml_data', 'alt_ids', 'special_filters'),
            'classes': ('collapse',)
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['assign_to_category', 'mark_as_featured', 'mark_as_bestseller']

    def display_discount(self, obj):
        if obj.has_discount:
            return f"{obj.discount_percent}%"
        return "-"

    display_discount.short_description = _('Скидка')

    def discount_percent_display(self, obj):
        return self.display_discount(obj)

    discount_percent_display.short_description = _('Скидка')

    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="200" />', obj.main_image)
        return '-'

    main_image_preview.short_description = _('Основное изображение')

    def attachments_preview(self, obj):
        images_html = []
        additional_images = []

        if obj.main_image:
            images_html.append(
                format_html(
                    '<div style="float: left; margin-right: 10px; margin-bottom: 10px;">'
                    '<img src="{}" width="100" /><br>'
                    '<small>Основное изображение</small>'
                    '</div>',
                    obj.main_image
                )
            )

        for i, url in enumerate(obj.additional_images, 1):
            additional_images.append(url)
            images_html.append(
                format_html(
                    '<div style="float: left; margin-right: 10px; margin-bottom: 10px;">'
                    '<img src="{}" width="100" /><br>'
                    '<small>Доп. изображение {}</small>'
                    '</div>',
                    url, i
                )
            )

        if obj.xml_data and 'attributes' in obj.xml_data and 'attachments' in obj.xml_data['attributes']:
            for attachment in obj.xml_data['attributes']['attachments']:
                if attachment.get('image'):
                    images_html.append(
                        format_html(
                            '<div style="float: left; margin-right: 10px; margin-bottom: 10px;">'
                            '<img src="{}" width="100" /><br>'
                            '<small>{} (тип: {})</small>'
                            '</div>',
                            attachment['image'],
                            attachment.get('name', 'Без названия'),
                            attachment.get('type', 'image')
                        )
                    )
                elif attachment.get('file'):
                    images_html.append(
                        format_html(
                            '<div style="float: left; margin-right: 10px; margin-bottom: 10px;">'
                            '<a href="{}" target="_blank">Файл: {}</a><br>'
                            '<small>Тип: {}</small>'
                            '</div>',
                            attachment['file'],
                            attachment.get('name', 'Без названия'),
                            attachment.get('type', 'file')
                        )
                    )

        if images_html:
            return format_html(''.join(images_html))
        return '-'

    attachments_preview.short_description = _('Все изображения и файлы')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('category_search/',
                 self.admin_site.admin_view(self.category_search_view),
                 name='xmlproduct_category_search'),
        ]
        return custom_urls + urls

    def category_search_view(self, request):
        q = request.GET.get('q', '').strip().lower()
        if not q or len(q) < 2:
            return JsonResponse({'results': []})

        try:
            categories = Category.objects.filter(
                Q(name__icontains=q) |
                Q(slug__icontains=q.replace(' ', '-'))
            ).distinct().order_by('name')[:20]

            results = [{
                'id': cat.id,
                'text': cat.name,
                'slug': cat.slug
            } for cat in categories]

            logger.debug(f"Found {len(results)} categories for query: '{q}'")
            return JsonResponse({'results': results})

        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    def display_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])

    display_categories.short_description = 'Категории'

    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            f"Помечено как рекомендуемые: {updated} товаров",
            messages.SUCCESS
        )

    mark_as_featured.short_description = _('Пометить как рекомендуемые')

    def mark_as_bestseller(self, request, queryset):
        updated = queryset.update(is_bestseller=True)
        self.message_user(
            request,
            f"Помечено как хиты продаж: {updated} товаров",
            messages.SUCCESS
        )

    mark_as_bestseller.short_description = _('Пометить как хиты продаж')

    def assign_to_category(self, request, queryset):
        if request.method == 'POST' and 'apply' in request.POST:
            try:
                category_ids = request.POST.getlist('categories', [])
                if not category_ids:
                    self.message_user(request, "Ошибка: не выбрано ни одной категории", messages.ERROR)
                    return HttpResponseRedirect(request.get_full_path())

                valid_ids = []
                for cat_id in category_ids:
                    try:
                        valid_ids.append(int(cat_id))
                    except (ValueError, TypeError):
                        continue

                categories = Category.objects.filter(id__in=valid_ids)
                if not categories.exists():
                    self.message_user(request, "Ошибка: выбранные категории не найдены", messages.ERROR)
                    return HttpResponseRedirect(request.get_full_path())

                updated_count = 0
                for product in queryset:
                    current_categories = set(product.categories.all())
                    new_categories = set(categories)
                    if current_categories != new_categories:
                        product.categories.clear()
                        product.categories.add(*categories)
                        updated_count += 1

                if updated_count > 0:
                    self.message_user(
                        request,
                        f"Категории успешно обновлены для {updated_count} товаров",
                        messages.SUCCESS
                    )
                else:
                    self.message_user(
                        request,
                        "Категории не были изменены (уже соответствуют выбранным)",
                        messages.WARNING
                    )

                return HttpResponseRedirect(request.get_full_path())

            except Exception as e:
                logger.error(f"Ошибка при обновлении категорий: {str(e)}", exc_info=True)
                self.message_user(request, f"Ошибка: {str(e)}", messages.ERROR)
                return HttpResponseRedirect(request.get_full_path())

        return render(
            request,
            'admin/main/assign_to_category.html',
            context={
                'products': queryset,
                'opts': self.model._meta,
                'action_name': 'assign_to_category'
            }
        )


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
    readonly_fields = ('total_price',)

    def total_price(self, obj):
        if obj.price is not None and obj.quantity is not None:
            return obj.price * obj.quantity
        return 0

    total_price.short_description = 'Общая стоимость'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('id', 'status', 'created_at', 'total_price', 'email', 'invoice_status_display')  # Заменили invoice_status на invoice_status_display
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'email']
    list_editable = ['status']
    actions = [
        'mark_as_new',
        'mark_as_in_progress',
        'mark_as_completed',
        'mark_as_delivered',
        'mark_as_cancelled',
    ]
    readonly_fields = ['created_at', 'updated_at', 'invoice_status_display']

    def invoice_status_display(self, obj):
        if hasattr(obj, 'invoice'):
            return "Отправлен" if obj.invoice.sent else "Не отправлен"
        return "Не создан"

    invoice_status_display.short_description = 'Статус счета'

    def save_model(self, request, obj, form, change):
        # Получаем старый статус из базы данных
        old_status = None
        if change and obj.pk:
            old_order = Order.objects.get(pk=obj.pk)
            old_status = old_order.status

        # Сохраняем заказ
        super().save_model(request, obj, form, change)

        # Проверяем изменение статуса на 'in_progress'
        if change and obj.status == 'in_progress' and old_status != 'in_progress':
            logger.info(f"Admin: Status changed to in_progress for order #{obj.id}")
            try:
                # Импортируем здесь, чтобы избежать циклического импорта
                from main.signals import process_invoice_for_order
                process_invoice_for_order(obj)
            except Exception as e:
                logger.error(f"Failed to process invoice from admin: {str(e)}", exc_info=True)
                self.message_user(request, f"Ошибка обработки счета: {str(e)}", level=messages.ERROR)

    def mark_as_in_progress(self, request, queryset):
        # Получаем заказы, у которых статус не 'in_progress'
        to_update = queryset.exclude(status=Order.STATUS_IN_PROGRESS)
        updated = to_update.update(status=Order.STATUS_IN_PROGRESS)

        if updated > 0:
            self.message_user(request, f"Обновлено {updated} заказов: статус 'Ожидает оплаты'", messages.SUCCESS)

            # Обрабатываем счета для обновленных заказов
            from main.signals import process_invoice_for_order
            for order in to_update.filter(status=Order.STATUS_IN_PROGRESS):
                try:
                    process_invoice_for_order(order)
                except Exception as e:
                    logger.error(f"Failed to process invoice for order #{order.id}: {str(e)}")
                    self.message_user(request,
                                      f"Ошибка обработки счета для заказа #{order.id}: {str(e)}",
                                      level=messages.ERROR)
        else:
            self.message_user(request, "Нет заказов для обновления статуса", messages.WARNING)

    mark_as_in_progress.short_description = "Установить статус 'Ожидает оплаты'"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_COMPLETED)
        self.message_user(request, f"Обновлено {updated} заказов: статус 'Доставляется'", messages.SUCCESS)

    mark_as_completed.short_description = "Установить статус 'Доставляется'"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_DELIVERED)
        self.message_user(request, f"Обновлено {updated} заказов: статус 'Доставлен'", messages.SUCCESS)

    mark_as_delivered.short_description = "Установить статус 'Доставлен'"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_CANCELLED)
        self.message_user(request, f"Обновлено {updated} заказов: статус 'Отменен'", messages.SUCCESS)

    mark_as_cancelled.short_description = "Установить статус 'Отменен'"

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