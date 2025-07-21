from django.contrib import admin
from .models import (
    CustomProductTemplate, CustomProductImage,
    CustomDesignArea, UserCustomDesign,
    CustomDesignElement, CustomProductColor,
    CustomProductOrder, CustomProductSize
)

class CustomProductImageInline(admin.TabularInline):
    model = CustomProductImage
    extra = 1
    fields = ('name', 'image', 'is_front', 'is_back', 'order')
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
    list_display = ('name', 'base_price', 'active', 'created_at')
    list_editable = ('base_price', 'active')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [CustomProductImageInline, CustomDesignAreaInline]
    filter_horizontal = ('sizes',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'base_price', 'active', 'sizes')
        }),
    )

@admin.register(CustomProductColor)
class CustomProductColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code', 'active', 'preview_color')
    list_editable = ('active',)
    list_filter = ('active',)
    search_fields = ('name', 'hex_code')

    def preview_color(self, obj):
        return f'<div style="width: 20px; height: 20px; background-color: {obj.hex_code};"></div>'
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
    list_display = ('id', 'design', 'selected_color', 'quantity', 'price', 'created_at')
    list_filter = ('created_at', 'selected_color', 'design__template')
    search_fields = ('design__id',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'