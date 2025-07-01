from django.core.validators import MinValueValidator
from django.db import models
from django.core.files import File
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth import get_user_model
import os
from mptt.models import MPTTModel, TreeForeignKey

User = get_user_model()


class Category(MPTTModel):
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Родительская категория')
    )
    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL-адрес'), max_length=255, unique=True)
    image = models.ImageField(_('Изображение'), upload_to='categories/', blank=True, null=True)
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

    class MPTTMeta:
        order_insertion_by = ['name']

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
    is_active = models.BooleanField(default=True, verbose_name="Активный")

    class Meta:
        verbose_name = _('Бренд')
        verbose_name_plural = _('Бренды')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:brand_detail', kwargs={'slug': self.slug})


class XMLProduct(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новинка'),
        ('regular', 'Обычный'),
        ('limited', 'До исчерпания')
    ]
    quantity = models.PositiveIntegerField(
        _('Количество'),
        default=0,
        blank=True,
        null=True
    )
    sizes_available = models.CharField(
        _('Доступные размеры'),
        max_length=255,
        blank=True,
        null=True
    )

    # Основная информация
    product_id = models.CharField(_('ID товара'), max_length=50, unique=True)
    code = models.CharField(_('Артикул'), max_length=100)
    name = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    price = models.DecimalField(_('Цена'), max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        _('Старая цена'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    made_in_russia = models.BooleanField(_('Сделано в России'), default=False)
    is_eco = models.BooleanField(_('Эко-подарки'), default=False)
    for_kids = models.BooleanField(_('Для детей'), default=False)
    is_profitable = models.BooleanField(_('Выгодно'), default=False)

    # Поля для технических характеристик
    application_type = models.CharField(
        _('Вид нанесения'),
        max_length=100,
        blank=True,
        choices=[
            ('uv_print', 'УФ-печать'),
            ('laser_engraving', 'Лазерная гравировка'),
            ('embroidery', 'Вышивка'),
            ('silk_print', 'Шелкография'),
            ('tampo_print', 'Тамопечать'),
            ('thermal_print', 'Термопечать'),
        ]
    )
    mechanism_type = models.CharField(_('Механизм'), max_length=100, blank=True)
    ball_diameter = models.CharField(_('Диаметр шарика'), max_length=50, blank=True)
    refill_type = models.CharField(_('Тип стержня'), max_length=100, blank=True)
    replaceable_refill = models.BooleanField(_('Сменный стержень'), default=False)
    format_size = models.CharField(_('Формат'), max_length=20, blank=True)
    cover_type = models.CharField(_('Тип обложки'), max_length=100, blank=True)
    block_color = models.CharField(_('Цвет блока'), max_length=50, blank=True)
    edge_type = models.CharField(_('Обрез блока'), max_length=50, blank=True)
    page_count = models.PositiveIntegerField(_('Число страниц'), null=True, blank=True)
    calendar_grid = models.CharField(_('Календарная сетка'), max_length=100, blank=True)
    ribbon_color = models.CharField(_('Цвет ляссе'), max_length=50, blank=True)
    box_size = models.CharField(_('Размер коробки/полотна'), max_length=100, blank=True)
    density = models.CharField(_('Плотность (г/м²)'), max_length=50, blank=True)
    expiration_date = models.CharField(_('Срок годности'), max_length=100, blank=True)
    special_filters = models.JSONField(default=list, blank=True)  # Для хранения спецфильтров
    size = models.CharField(max_length=50, blank=True, null=True)  # Размер одежды
    dimensions = models.CharField(max_length=50, blank=True, null=True)  # Габариты
    collection = models.CharField(_('Коллекция'), max_length=100, blank=True)
    fit = models.CharField(_('Посадка'), max_length=50, blank=True, null=True)  # Прямая, оверсайз и т.д.
    cut = models.CharField(_('Крой'), max_length=50, blank=True, null=True) # Крой
    lining = models.CharField(_('Изнанка'), max_length=50, blank=True, null=True)  # Например, начес
    has_lining = models.BooleanField(_('Есть подкладка'), default=False) # Наличие подкладки
    video_link = models.URLField(blank=True, null=True)  # Ссылка на видео
    stock_marking = models.CharField(max_length=100, blank=True, null=True)
    umbrella_type = models.CharField(_('Тип зонта'), max_length=100, blank=True, null=True)

    MARKING_CHOICES = [
        ('textile', 'Текстиль'),
        ('other', 'Другое'),
    ]
    marking_type = models.CharField(_('Тип маркировки'), max_length=20, choices=MARKING_CHOICES, blank=True)
    PACKAGING_CHOICES = [
        ('bag', 'Пакет'),
        ('gift_box', 'Подарочная коробка'),
        ('none', 'Без упаковки'),
    ]
    packaging_type = models.CharField(_('Тип упаковки'), max_length=20, choices=PACKAGING_CHOICES, blank=True)
    # Дополнительные атрибуты
    pantone_color = models.CharField(_('Пантон (цвет)'), max_length=50, blank=True)
    GENDER_CHOICES = [
        ('male', 'Мужские'),
        ('female', 'Женские'),
        ('unisex', 'Унисекс'),
    ]
    gender = models.CharField(
        _('Пол'),
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )
    requires_marking = models.BooleanField(_('Подлежит маркировке'), default=False)
    individual_packaging = models.BooleanField(_('Индивидуальная упаковка'), default=False)
    cover_material = models.CharField(_('Материал обложки'), max_length=100, blank=True)
    block_number = models.CharField(_('Номер блока'), max_length=50, blank=True)

    dating = models.CharField(_('Датировка'), max_length=100, blank=True)


    additional_image_urls = models.JSONField(
        _('URL дополнительных изображений'),
        default=list,
        blank=True
    )

    # Характеристики
    material = models.CharField(_('Материал'), max_length=255, blank=True)

    weight = models.DecimalField(
        _('Вес'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    volume = models.DecimalField(
        _('Объем'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    barcode = models.CharField(_('Штрих-код'), max_length=50, blank=True)
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='regular'
    )

    # Связи
    brand = models.CharField(
        _('Бренд'),
        max_length=255,
        blank=True,
        null=True
    )
    brand_link = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Связанный бренд')
    )
    categories = models.ManyToManyField(
        Category,
        related_name='xml_products',
        verbose_name=_('Категории')
    )

    # Флаги
    in_stock = models.BooleanField(_('В наличии'), default=True)
    is_featured = models.BooleanField(_('Рекомендуемый'), default=False)
    is_bestseller = models.BooleanField(_('Хит продаж'), default=False)
    was_imported = models.BooleanField(
        _('Был импортирован'),
        default=True
    )

    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    xml_data = models.JSONField(_('Данные XML'), null=True, blank=True)
    alt_ids = models.JSONField(
        _('Альтернативные ID'),
        default=list,
        blank=True
    )

    class Meta:
        verbose_name = _('XML Товар')
        verbose_name_plural = _('XML Товары')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product_id']),
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['price']),
            models.Index(fields=['in_stock']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:xml_product_detail', kwargs={'product_id': self.product_id})

    @property
    def main_image(self):
        """Возвращает URL основного изображения с авторизацией"""
        if self.xml_data and 'main_image_url' in self.xml_data:
            url = self.xml_data['main_image_url']
            if url.startswith('https://api2.gifts.ru/'):
                return url.replace(
                    'https://api2.gifts.ru/',
                    'https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/'
                )
            return url
        return os.path.join(settings.STATIC_URL, 'images/no-image.jpg')

    @property
    def additional_images(self):
        """Возвращает список URL дополнительных изображений с авторизацией"""
        if self.xml_data and 'additional_image_urls' in self.xml_data:
            urls = []
            for url in self.xml_data['additional_image_urls']:
                if url.startswith('https://api2.gifts.ru/'):
                    urls.append(url.replace(
                        'https://api2.gifts.ru/',
                        'https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/'
                    ))
                else:
                    urls.append(url)
            return urls
        return []

    @property
    def has_discount(self):
        return self.old_price is not None and self.old_price > self.price

    @property
    def discount_percent(self):
        if not self.has_discount:
            return 0
        return int((1 - self.price / self.old_price) * 100)

    def get_gallery_images(self):
        """Все изображения для галереи (основное + вложения)"""
        gallery = [{
            'url': self.main_image_url,
            'name': self.name,
            'type': 'main',
            'alt': self.name
        }]

        gallery.extend([{
            'url': attachment.file.url,
            'name': attachment.name or self.name,
            'type': 'attachment',
            'alt': attachment.name or self.name
        } for attachment in self.attachments.filter(attachment_type='image').order_by('sort_order')])

        return gallery

# models.py - добавить новые модели
class ProductVariant(models.Model):
    product = models.ForeignKey(XMLProduct, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    barcode = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = _('Вариант товара')
        verbose_name_plural = _('Варианты товаров')

    def __str__(self):
        return f"{self.size} - {self.product.name}"

class ProductFilter(models.Model):
    filter_type = models.CharField(max_length=50)
    filter_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    products = models.ManyToManyField(XMLProduct, related_name='product_filters')

    class Meta:
        verbose_name = _('Фильтр товара')
        verbose_name_plural = _('Фильтры товаров')
        unique_together = ('filter_type', 'filter_id')

    def __str__(self):
        return f"{self.filter_type}: {self.filter_id}"

class ApplicationType(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    products = models.ManyToManyField(XMLProduct, related_name='application_types')

    class Meta:
        verbose_name = _('Тип нанесения')
        verbose_name_plural = _('Типы нанесения')

    def __str__(self):
        return self.name
class ProductAttachment(models.Model):
    ATTACHMENT_TYPES = [
        ('image', _('Изображение')),
        ('document', _('Документ')),
        ('video', _('Видео')),
        ('other', _('Другое'))
    ]

    product = models.ForeignKey(
        XMLProduct,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Товар')
    )
    file = models.FileField(
        _('Файл'),
        upload_to='attachments/',  # Просто папка, без даты
        max_length=255  # Увеличиваем максимальную длину
    )
    name = models.CharField(
        _('Название'),
        max_length=255,
        blank=True
    )
    attachment_type = models.CharField(
        _('Тип вложения'),
        max_length=20,
        choices=ATTACHMENT_TYPES,
        default='image'
    )
    sort_order = models.PositiveIntegerField(
        _('Порядок сортировки'),
        default=0
    )
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Вложение товара')
        verbose_name_plural = _('Вложения товаров')
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.product.name})"

    def save(self, *args, **kwargs):
        # Автоматическое определение типа по расширению файла
        if not self.attachment_type and self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                self.attachment_type = 'image'
            elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
                self.attachment_type = 'document'
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                self.attachment_type = 'video'
            else:
                self.attachment_type = 'other'
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(_('Название'), max_length=255)
    slug = models.SlugField(_('URL-адрес'), max_length=255, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('Категория')
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_brands',
        verbose_name=_('Бренд')
    )
    sku = models.CharField(_('Артикул'), max_length=50, unique=True)
    short_description = models.TextField(_('Краткое описание'), blank=True)
    description = models.TextField(_('Описание'), blank=True)
    price = models.DecimalField(_('Цена'), max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        _('Старая цена'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
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
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Пользователь')
    )
    session_key = models.CharField(
        _('Ключ сессии'),
        max_length=40,
        null=True,
        blank=True
    )
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
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Корзина')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name=_('Товар'),
        null=True,
        blank=True
    )
    xml_product = models.ForeignKey(
        XMLProduct,
        on_delete=models.CASCADE,
        verbose_name=_('XML Товар'),
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(
        _('Количество'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Элемент корзины')
        verbose_name_plural = _('Элементы корзины')
        unique_together = ('cart', 'product', 'xml_product')

    def __str__(self):
        product = self.product or self.xml_product
        return f"{self.quantity} x {product}"

    @property
    def total_price(self):
        product = self.product or self.xml_product
        return product.price * self.quantity


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

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Пользователь')
    )
    session_key = models.CharField(
        _('Ключ сессии'),
        max_length=40,
        null=True,
        blank=True
    )
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
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
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Заказ')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name=_('Товар')
    )
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


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Отзыв о товаре')
        verbose_name_plural = _('Отзывы о товарах')
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв {self.user} на {self.product}"


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    products = models.ManyToManyField(
        Product,
        related_name='wishlists'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Список желаний')
        verbose_name_plural = _('Списки желаний')
        ordering = ['-created_at']

    def __str__(self):
        return f"Список желаний {self.user}"


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