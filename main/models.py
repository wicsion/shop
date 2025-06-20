
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from gifts_project import settings
from mptt.models import MPTTModel, TreeForeignKey



User = get_user_model()

class Category(MPTTModel):
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                            related_name='children', verbose_name=_('Родительская категория'))
    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL-адрес'), max_length=255, unique=True)


    image = models.URLField(_('Изображение'), blank=True, null=True)

    description = models.TextField(_('Описание'), blank=True)
    is_featured = models.BooleanField(_('Популярная категория'), default=False)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    xml_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    ICON_CHOICES = [
        ('fas fa-tshirt', 'Одежда'),
        ('fas fa-mug-hot', 'Посуда'),
        ('fas fa-pen', 'Ручки'),
        ('fas fa-mobile-alt', 'Электроника'),
        ('fas fa-shopping-bag', 'Сумки'),
        ('fas fa-book', 'Книги/Блокноты'),
        ('fas fa-box-open', 'Упаковка'),
        ('fas fa-gift', 'Подарки'),
        ('fas fa-building', 'Корпоративные'),
        ('fas fa-umbrella', 'Зонты'),
        ('fas fa-running', 'Спорт'),
        ('fas fa-suitcase', 'Путешествия'),
        ('fas fa-utensils', 'Пикник'),
        ('fas fa-hiking', 'Походы'),
        ('fas fa-umbrella-beach', 'Пляж'),
    ]
    icon = models.CharField(_('Иконка'), max_length=50, choices=ICON_CHOICES, blank=True)


    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:category_detail', kwargs={'slug': self.slug})



class Brand(models.Model):
    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL-адрес'), max_length=255, unique=True)
    logo = models.ImageField(_('Логотип'), upload_to='brands/', blank=True)
    description = models.TextField(_('Описание'), blank=True)
    additional_info = models.TextField(blank=True)
    products = models.ManyToManyField('Product', related_name='brand_products')
    is_active = models.BooleanField(default=True, verbose_name="Активный")


    class Meta:
        verbose_name = _('Бренд')
        verbose_name_plural = _('Бренды')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:brand_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL-адрес'), max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                                 related_name='products', verbose_name=_('Категория'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='product_brands', verbose_name=_('Бренд'))
    sku = models.CharField(_('Артикул'), max_length=50, unique=True)
    short_description = models.TextField(_('Краткое описание'), blank=True)
    description = models.TextField(_('Описание'), blank=True)
    price = models.DecimalField(_('Цена'), max_digits=10, decimal_places=2)
    old_price = models.DecimalField(_('Старая цена'), max_digits=10, decimal_places=2,
                                    null=True, blank=True)
    is_featured = models.BooleanField(_('Рекомендуемый товар'), default=False)
    is_new = models.BooleanField(_('Новый товар'), default=False)
    is_bestseller = models.BooleanField(_('Хит продаж'), default=False)
    in_stock = models.BooleanField(_('В наличии'), default=True)
    quantity = models.PositiveIntegerField(_('Количество'), default=1)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:product_detail', kwargs={'slug': self.slug})

    @property
    def has_discount(self):
        return self.old_price is not None and self.old_price > self.price

    @property
    def discount_percent(self):
        if not self.has_discount:
            return 0
        return int((1 - self.price / self.old_price) * 100)


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             verbose_name=_('Пользователь'))
    session_key = models.CharField(_('Ключ сессии'), max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Корзина')
        verbose_name_plural = _('Корзины')

    def __str__(self):
        if self.user:
            return f"Корзина пользователя {self.user}"
        return f"Корзина (анонимная, ключ: {self.session_key})"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,
                             related_name='items', verbose_name=_('Корзина'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name=_('Товар'), null=True, blank=True)
    xml_product = models.ForeignKey('XMLProduct', on_delete=models.CASCADE,
                                    verbose_name=_('XML Товар'), null=True, blank=True)
    quantity = models.PositiveIntegerField(_('Количество'), default=1,
                                           validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Элемент корзины')
        verbose_name_plural = _('Элементы корзины')
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product}"

    @property
    def total_price(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, _('Новый')),
        (STATUS_IN_PROGRESS, _('В обработке')),
        (STATUS_COMPLETED, _('Завершен')),
        (STATUS_CANCELLED, _('Отменен')),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name=_('Пользователь'))
    session_key = models.CharField(_('Ключ сессии'), max_length=40, null=True, blank=True)
    status = models.CharField(_('Статус'), max_length=20, choices=STATUS_CHOICES,
                              default=STATUS_NEW)
    first_name = models.CharField(_('Имя'), max_length=100)
    last_name = models.CharField(_('Фамилия'), max_length=100)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Телефон'), max_length=20)
    address = models.TextField(_('Адрес'))
    comment = models.TextField(_('Комментарий'), blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name='items', verbose_name=_('Заказ'))
    product = models.ForeignKey(Product, on_delete=models.PROTECT,
                                verbose_name=_('Товар'))
    quantity = models.PositiveIntegerField(_('Количество'), default=1)
    price = models.DecimalField(_('Цена'), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _('Элемент заказа')
        verbose_name_plural = _('Элементы заказа')

    def __str__(self):
        return f"{self.quantity} x {self.product} (заказ #{self.order.id})"

    @property
    def total_price(self):
        return self.price * self.quantity


class Slider(models.Model):
    title = models.CharField(_('Заголовок'), max_length=255)
    subtitle = models.CharField(_('Подзаголовок'), max_length=255, blank=True)
    image = models.ImageField(_('Изображение'), upload_to='sliders/')
    link = models.CharField(_('Ссылка'), max_length=255, blank=True)
    button_text = models.CharField(_('Текст кнопки'), max_length=50, blank=True)
    is_active = models.BooleanField(_('Активный'), default=True)
    order = models.PositiveIntegerField(_('Порядок'), default=0)

    class Meta:
        verbose_name = _('Слайд')
        verbose_name_plural = _('Слайдер')
        ordering = ['order']

    def __str__(self):
        return self.title


class Partner(models.Model):
    name = models.CharField(_('Название'), max_length=255)
    logo = models.ImageField(_('Логотип'), upload_to='partners/')
    link = models.URLField(_('Ссылка'), blank=True)
    is_active = models.BooleanField(_('Активный'), default=True)
    order = models.PositiveIntegerField(_('Порядок'), default=0)

    class Meta:
        verbose_name = _('Партнер')
        verbose_name_plural = _('Партнеры')
        ordering = ['order']

    def __str__(self):
        return self.name




class ProductReview(models.Model):
    product = models.ForeignKey('Product', related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField('Product', related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)


class XMLProduct(models.Model):
    brand_model = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='xml_products')
    product_id = models.CharField(max_length=50, unique=True)
    group_id = models.CharField(max_length=50, blank=True, null=True)
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    small_image = models.URLField(blank=True)
    big_image = models.URLField(blank=True)
    super_big_image = models.URLField(blank=True)
    brand = models.CharField(max_length=255, blank=True)
    in_stock = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    xml_data = models.JSONField(null=True, blank=True)
    categories = models.ManyToManyField('Category', related_name='xml_products')
    status = models.CharField(max_length=20, choices=[
        ('new', 'Новинка'),
        ('regular', 'Обычный'),
        ('limited', 'До исчерпания')
    ], default='regular')
    material = models.CharField(max_length=255, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)


    class Meta:
        verbose_name = 'XML Товар'
        verbose_name_plural = 'XML Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:xml_product_detail', kwargs={'product_id': self.product_id})

    @property
    def main_image(self):
        return self.super_big_image or self.big_image or self.small_image

    @property
    def has_discount(self):
        return self.old_price is not None and self.old_price > self.price

    @property
    def discount_percent(self):
        if not self.has_discount:
            return 0
        return int((1 - self.price / self.old_price) * 100)
