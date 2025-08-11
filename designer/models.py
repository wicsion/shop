from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomProductSize(models.Model):
    SIZE_CHOICES = [
        ('XXS', 'XXS (40-42)'),
        ('XS', 'XS (44-46)'),
        ('S', 'S (48)'),
        ('M', 'M (50)'),
        ('L', 'L (52)'),
        ('XL', 'XL (54)'),
        ('XXL', 'XXL (56-58)'),
        ('3XL', '3XL (60-62)'),
        ('4XL', '4XL (64-66)'),
        ('5XL', '5XL (68-70)'),
        ('6XL', '6XL (72-74)'),
        ('7XL', '7XL (76-78)'),
    ]

    name = models.CharField(max_length=50, choices=SIZE_CHOICES, unique=True)
    description = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.description})"


class CustomProductTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sizes = models.ManyToManyField(CustomProductSize, related_name='templates')

    def get_available_sizes(self):
        return self.sizes.filter(active=True).order_by('order')

    def __str__(self):
        return self.name


# models.py - update CustomProductImage model
class CustomProductImage(models.Model):
    template = models.ForeignKey(CustomProductTemplate, on_delete=models.CASCADE, related_name='images')
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='custom_products/')
    is_front = models.BooleanField(default=False)
    is_back = models.BooleanField(default=False)
    is_silhouette = models.BooleanField(default=False, verbose_name="Use as silhouette")  # New field
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class CustomDesignArea(models.Model):
    template = models.ForeignKey(CustomProductTemplate, on_delete=models.CASCADE, related_name='design_areas')
    name = models.CharField(max_length=100)
    x_position = models.IntegerField()
    y_position = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    max_text_length = models.IntegerField(default=50)
    allow_images = models.BooleanField(default=True)
    allow_text = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class UserCustomDesign(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_session = models.CharField(max_length=40)
    template = models.ForeignKey(CustomProductTemplate, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    product = models.ForeignKey('main.XMLProduct', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('user_session', 'product')


    def __str__(self):
        return f"Custom Design for {self.template.name}"


class CustomDesignElement(models.Model):
    SIDE_CHOICES = [
        ('front', 'Лицевая сторона'),
        ('back', 'Тыльная сторона'),
    ]

    design = models.ForeignKey(UserCustomDesign, on_delete=models.CASCADE, related_name='elements')
    area = models.ForeignKey(CustomDesignArea, on_delete=models.CASCADE)
    text_content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='design_elements/', null=True, blank=True)
    color = models.CharField(max_length=7, default='#000000')  # HEX color
    font_size = models.IntegerField(default=14)
    rotation = models.IntegerField(default=0)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES, default='front')  # Новое поле
    created_at = models.DateTimeField(auto_now_add=True)

    def has_image(self):
        """Проверяет, есть ли у элемента изображение"""
        try:
            return bool(self.image) and bool(self.image.url)
        except ValueError:
            # Обработка случая, когда image есть, но файл не прикреплен
            return False

    def get_image_url(self):
        """Безопасно возвращает URL изображения или None"""
        try:
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
        except ValueError:
            pass
        return None

    def __str__(self):
        return f"Element for {self.design.template.name}"


class CustomProductColor(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7)
    preview_image = models.ImageField(upload_to='product_colors/', blank=True, null=True)
    active = models.BooleanField(default=True)
    is_pattern = models.BooleanField(default=False)
    pattern_image = models.ImageField(upload_to='color_patterns/', blank=True, null=True)
    gradient_css = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def display_value(self):
        if self.gradient_css:
            return self.gradient_css
        elif self.pattern_image:
            return f"url('{self.pattern_image.url}')"
        return self.hex_code

class CustomProductOrder(models.Model):
    design = models.ForeignKey(UserCustomDesign, on_delete=models.CASCADE)
    selected_color = models.ForeignKey(CustomProductColor, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    size = models.CharField(max_length=10, blank=True, null=True)
    in_cart = models.BooleanField(default=True)
    original_product = models.ForeignKey(
        'main.XMLProduct',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Оригинальный товар'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order for {self.design.template.name}"

    def get_preview_image(self):
        if self.design.template.images.filter(is_front=True).exists():
            return self.design.template.images.filter(is_front=True).first().image.url
        return None

# models.py
class ProductSilhouette(models.Model):
    template = models.OneToOneField(CustomProductTemplate, on_delete=models.CASCADE, related_name='silhouette')
    front_mask_image = models.ImageField(upload_to='product_silhouettes/', verbose_name="Маска для передней стороны")
    back_mask_image = models.ImageField(upload_to='product_silhouettes/', blank=True, null=True, verbose_name="Маска для тыловой стороны")
    colored_areas = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Silhouette for {self.template.name}"


class ProductMask(models.Model):
    template = models.ForeignKey(CustomProductTemplate, on_delete=models.CASCADE, related_name='masks')
    name = models.CharField(max_length=100)
    mask_image = models.ImageField(upload_to='product_masks/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mask for {self.template.name}"