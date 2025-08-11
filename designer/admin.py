from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from .models import (
    CustomProductTemplate, CustomProductImage,
    CustomDesignArea, UserCustomDesign,
    CustomDesignElement, CustomProductColor,
    CustomProductOrder, CustomProductSize,
    ProductSilhouette
)
from .views import SilhouetteEditView
from .forms import SilhouetteEditForm

class ProductSilhouetteInline(admin.TabularInline):
    model = ProductSilhouette
    extra = 1
    fields = ('front_mask_image', 'back_mask_image')
    max_num = 1

class CustomProductImageInline(admin.TabularInline):
    model = CustomProductImage
    extra = 1
    fields = ('name', 'image', 'is_front', 'is_back', 'is_silhouette', 'order')
    ordering = ('order',)

class CustomDesignAreaInline(admin.TabularInline):
    model = CustomDesignArea
    extra = 1
    fields = ('name', 'x_position', 'y_position', 'width', 'height',
              'max_text_length', 'allow_images', 'allow_text')

class CustomProductSizeInline(admin.TabularInline):
    model = CustomProductSize
    extra = 1
    fields = ('name', 'description', 'active', 'order')
    ordering = ('order',)

@admin.register(CustomProductTemplate)
class CustomProductTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'active', 'created_at', 'has_silhouette')
    list_editable = ('base_price', 'active')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [CustomProductImageInline, CustomDesignAreaInline, ProductSilhouetteInline]
    filter_horizontal = ('sizes',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'base_price', 'active', 'sizes')
        }),
    )

    def has_silhouette(self, obj):
        return hasattr(obj, 'silhouette') and obj.silhouette is not None
    has_silhouette.boolean = True
    has_silhouette.short_description = 'Has Silhouette'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/add-silhouette/',
                 self.admin_site.admin_view(self.add_silhouette_view),
                 name='designer_customproducttemplate_add_silhouette'),
        ]
        return custom_urls + urls

    def add_silhouette_view(self, request, object_id):
        return redirect(reverse('admin:designer_productsilhouette_add') + f'?template_id={object_id}')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['has_add_silhouette'] = True
        return super().change_view(request, object_id, form_url, extra_context)

@admin.register(ProductSilhouette)
class ProductSilhouetteAdmin(admin.ModelAdmin):
    list_display = ('template', 'preview_front_mask', 'preview_back_mask', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('template__name',)
    readonly_fields = ('preview_front_mask', 'preview_back_mask')
    form = SilhouetteEditForm
    change_form_template = 'admin/silhouette_editor.html'

    def preview_front_mask(self, obj):
        if obj.front_mask_image:
            return mark_safe(f'<img src="{obj.front_mask_image.url}" style="max-height: 50px;" />')
        return '-'
    preview_front_mask.short_description = 'Front Mask Preview'

    def preview_back_mask(self, obj):
        if obj.back_mask_image:
            return mark_safe(f'<img src="{obj.back_mask_image.url}" style="max-height: 50px;" />')
        return '-'
    preview_back_mask.short_description = 'Back Mask Preview'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/edit-mask/',
                 self.admin_site.admin_view(SilhouetteEditView.as_view()),
                 name='designer_productsilhouette_edit_mask'),
        ]
        return custom_urls + urls

    def add_view(self, request, form_url='', extra_context=None):
        template_id = request.GET.get('template_id')
        if template_id:
            extra_context = extra_context or {}
            extra_context['template_id'] = template_id

        extra_context = extra_context or {}
        extra_context['object'] = None
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['object'] = self.get_object(request, object_id)
        extra_context['has_edit_mask'] = True
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

@admin.register(CustomProductColor)
class CustomProductColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code', 'active', 'preview_color')
    list_editable = ('active',)
    list_filter = ('active',)
    search_fields = ('name', 'hex_code')

    def preview_color(self, obj):
        return mark_safe(f'<div style="width: 20px; height: 20px; background-color: {obj.hex_code};"></div>')
    preview_color.short_description = 'Preview'
    preview_color.allow_tags = True

@admin.register(CustomProductSize)
class CustomProductSizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active',)
    search_fields = ('name', 'description')
    ordering = ('order',)

@admin.register(UserCustomDesign)
class UserCustomDesignAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'user', 'created_at')
    list_filter = ('template', 'created_at')
    search_fields = ('user__username', 'template__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

@admin.register(CustomDesignElement)
class CustomDesignElementAdmin(admin.ModelAdmin):
    list_display = ('id', 'design', 'area', 'element_type')
    list_filter = ('design__template', 'area')
    search_fields = ('design__id', 'text_content')

    def element_type(self, obj):
        if obj.image:
            return 'Image'
        return 'Text'
    element_type.short_description = 'Type'

@admin.register(CustomProductOrder)
class CustomProductOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'design', 'selected_color', 'quantity', 'price', 'created_at', 'preview_link')
    list_filter = ('created_at', 'selected_color', 'design__template')
    search_fields = ('design__id',)
    readonly_fields = ('created_at', 'preview_link')
    date_hierarchy = 'created_at'

    def preview_link(self, obj):
        return mark_safe(f'<a href="{reverse("designer:custom_designer_edit", args=[obj.design.id])}" target="_blank">Просмотреть дизайн</a>')
    preview_link.short_description = 'Ссылка на дизайн'



