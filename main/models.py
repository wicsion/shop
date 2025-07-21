from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
import os
import logging
from django.core.cache import cache
import re
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
import uuid
from django.conf import settings
from model_utils import FieldTracker

logger = logging.getLogger(__name__)
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


class ProductVariant(models.Model):
    product = models.ForeignKey(
        'XMLProduct',
        on_delete=models.CASCADE,
        related_name='product_variants',
        verbose_name='Товар',
        null=True,  # Разрешаем NULL
        blank=True  # Разрешаем пустое значение в формах
    )
    size = models.CharField('Размер', max_length=50)
    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    old_price = models.DecimalField(
        'Старая цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    barcode = models.CharField(
        'Штрих-код размера',
        max_length=50,
        blank=True,
        help_text="Штрих-код, общий для этого размера во всех товарах"
    )
    quantity = models.PositiveIntegerField('Количество', default=0)
    sku = models.CharField(
        'Артикул размера',
        max_length=100,
        blank=True,
        help_text="Автоматически генерируется как 'SIZE-{размер}'"
    )


    # При создании связи:
    # Обновить количество для всех вариантов товара

    class Meta:
        verbose_name = 'Вариант товара'
        verbose_name_plural = 'Варианты товаров'
        unique_together = ('product', 'size')
        ordering = ['size']

    def __str__(self):
        return f"{self.size} - {self.product.name}"

    @staticmethod
    def normalize_size(size):
        """Нормализует размер в стандартный формат"""
        if not size:
            return size

        size = str(size).strip().upper()
        size_map = {
            'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'XL',
            'XXL': 'XXL', 'XXXL': 'XXXL', '3XL': 'XXXL', '4XL': '4XL', '5XL': '5XL'
        }
        return size_map.get(size, size)

    def save(self, *args, **kwargs):

        self.size = self.normalize_size(self.size)
        super().save(*args, **kwargs)





class XMLProduct(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новинка'),
        ('regular', 'Обычный'),
        ('limited', 'До исчерпания')
    ]
    quantity = models.PositiveIntegerField(
        _('Общее количество'),
        default=0,
        blank=True,
        null=True,
        help_text="Автоматически рассчитывается из вариантов"
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
    dimensions = models.CharField(_('Габариты'), max_length=255, blank=True)
    collection = models.CharField(_('Коллекция'), max_length=100, blank=True)
    fit = models.CharField(_('Посадка'), max_length=50, blank=True, null=True)  # Прямая, оверсайз и т.д.
    cut = models.CharField(_('Крой'), max_length=50, blank=True, null=True) # Крой
    lining = models.CharField(_('Изнанка'), max_length=50, blank=True, null=True)  # Например, начес
    has_lining = models.BooleanField(_('Есть подкладка'), default=False) # Наличие подкладки
    video_link = models.URLField(blank=True, null=True)  # Ссылка на видео
    stock_marking = models.CharField(max_length=100, blank=True, null=True)
    umbrella_type = models.CharField(_('Тип зонта'), max_length=100, blank=True, null=True)
    clothing_sizes = models.CharField(
        _('Размеры одежды'),
        max_length=255,
        blank=True,
        null=True
    )

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
    variants = models.ManyToManyField(
        ProductVariant,
        through='ProductVariantThrough',
        through_fields=('product', 'variant'),
        related_name='product_variants',  # Изменено с 'products' во избежание конфликта
        verbose_name='Варианты размеров'
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

    def get_materials_from_filters(self):
        """Получает материалы из фильтров товара"""
        materials = []
        if self.xml_data and 'filters' in self.xml_data:
            for f in self.xml_data['filters']:
                if str(f.get('type_id')) in ['5', '73']:  # Типы фильтров для материалов
                    materials.append(f.get('filter_name'))
        return list(set(materials))  # Убираем дубликаты

    def normalize_size(self, size):
        """Нормализует размер, удаляя ненужные термины"""
        if not size:
            return None

        size_str = str(size).strip().upper()

        # Удаляем нежелательные термины
        remove_terms = [
            'HAT', 'CAP', 'HEAD', 'CM', 'ONE SIZE', 'РАЗМЕР', 'ОБХВАТ',
            'ГОЛОВЫ', 'ОБУВИ', 'SHOE', 'SIZE', 'ДЛЯ'
        ]

        for term in remove_terms:
            size_str = size_str.replace(term, '').strip()

        # Удаляем двойные пробелы и лишние дефисы
        size_str = ' '.join(size_str.split())
        size_str = size_str.replace(' - ', '-').replace('- ', '-').replace(' -', '-')

        return size_str if size_str else None

    def get_size_info(self):
        """Получает информацию о размерах без излишней фильтрации"""
        size_info = {
            'available_sizes': [],
            'sizes_with_quantities': [],
            'is_available': False
        }

        # 1. Проверяем варианты размеров
        if self.variants.exists():
            for variant in self.variants.all():
                size_info['available_sizes'].append(variant.size)
                size_info['sizes_with_quantities'].append({
                    'size': variant.size,
                    'quantity': variant.quantity,
                    'in_stock': variant.quantity > 0
                })

        # 2. Проверяем поле sizes_available
        elif self.sizes_available:
            for size in self.sizes_available.split(','):
                size = size.strip()
                if size:
                    size_info['available_sizes'].append(size)
                    size_info['sizes_with_quantities'].append({
                        'size': size,
                        'quantity': self.quantity,
                        'in_stock': self.in_stock
                    })

        # 3. Проверяем таблицу размеров из XML
        if self.xml_data and 'attributes' in self.xml_data and 'size_table' in self.xml_data['attributes']:
            size_table = self.xml_data['attributes']['size_table']
            if 'headers' in size_table and len(size_table['headers']) > 1:
                for size in size_table['headers'][1:]:
                    if size and size not in size_info['available_sizes']:
                        size_info['available_sizes'].append(size)
                        size_info['sizes_with_quantities'].append({
                            'size': size,
                            'quantity': self.quantity,
                            'in_stock': self.in_stock
                        })

        size_info['is_available'] = any(size['in_stock'] for size in size_info['sizes_with_quantities'])

        # Сортируем размеры по стандартному порядку
        STANDARD_ORDER = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', '3XL', '4XL', '5XL']
        size_info['sizes_with_quantities'].sort(
            key=lambda x: (
                STANDARD_ORDER.index(x['size']) if x['size'] in STANDARD_ORDER else len(STANDARD_ORDER),
                x['size']
            )
        )
        size_info['available_sizes'] = [s['size'] for s in size_info['sizes_with_quantities']]

        return size_info


    def get_add_to_cart_form(self):
        from .forms import AddToCartForm
        return AddToCartForm(product=self)

    def update_quantity_from_variants(self):
        """Обновляет общее количество на основе вариантов размеров"""
        if self.variants.exists():
            self.quantity = sum(v.quantity for v in self.variants.all())
            self.in_stock = self.quantity > 0
            self.save(update_fields=['quantity', 'in_stock'])
            return True
        return False

    def get_absolute_url(self):
        return reverse('main:xml_product_detail', kwargs={'product_id': self.product_id})

    @property
    def has_variants(self):
        """Есть ли варианты у товара"""
        return self.variants.exists()

    def get_available_sizes(self):
        """Возвращает список доступных размеров"""
        if self.has_variants:
            return list(self.variants.values_list('size', flat=True))
        return [self.sizes_available] if self.sizes_available else []

    def get_variant_by_size(self, size):
        """Возвращает вариант по размеру"""
        try:
            return self.variants.get(size=size)
        except ProductVariant.DoesNotExist:
            return None

    def update_main_quantity(self):
        """Обновляет общее количество на основе вариантов"""
        if self.has_variants:
            self.quantity = sum(v.quantity for v in self.variants.all())
            self.save(update_fields=['quantity'])

    @property
    def main_image(self):
        cache_key = f"product_image_{self.product_id}"
        cached_url = cache.get(cache_key)
        if cached_url:
            return cached_url

        if self.xml_data and 'main_image_url' in self.xml_data:
            url = self.xml_data['main_image_url']
            if url.startswith('https://api2.gifts.ru/'):
                url = url.replace(
                    'https://api2.gifts.ru/',
                    'https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/'
                )
            cache.set(cache_key, url, 60 * 60 * 24)  # Кэшируем на 24 часа
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

    @property
    def available_sizes(self):
        """Возвращает список всех доступных размеров, исключая пол и другие не-размеры"""
        sizes = set()
        # Расширенный список исключаемых терминов
        excluded_terms = [
            'мужские', 'женские', 'унисекс', 'male', 'female', 'unisex',
            'для мужчин', 'для женщин', 'для детей', 'детские',
            'муж', 'жен', 'м', 'ж', 'man', 'woman', 'men', 'women'
        ]

        # Добавляем размеры из вариантов
        if self.variants.exists():
            for variant in self.variants.all():
                size = variant.size.strip()
                # Проверяем, что размер не содержит исключенных терминов
                if size and not any(term.lower() in size.lower() for term in excluded_terms):
                    sizes.add(size)
        else:
            # Добавляем основной размер, если нет вариантов
            if self.sizes_available:
                for size in self.sizes_available.split(','):
                    size = size.strip()
                    if size and not any(term.lower() in size.lower() for term in excluded_terms):
                        sizes.add(size)

        # Добавляем размеры из фильтров (если нужно)
        if self.xml_data and 'filters' in self.xml_data:
            for f in self.xml_data['filters']:
                if f.get('type_id') == '1' and f.get('filter_name'):
                    filter_name = f['filter_name'].strip()
                    if filter_name and not any(term.lower() in filter_name.lower() for term in excluded_terms):
                        sizes.add(filter_name)

        # Сортируем размеры
        standard_order = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
        return sorted(sizes, key=lambda x: (
            standard_order.index(x) if x in standard_order else len(standard_order),
            x
        ))

    def get_printing_info(self):
        printing_info = {
            'methods': set(),
            'marking': None
        }

        # Словарь соответствия кодов методов нанесения их названиям
        PRINTING_METHODS = {
            'D2': 'Шелкография с трансфером (5 цветов)',
            'I': 'Вышивка (10 цветов)',
            'F1': 'Флекс (1 цвет)',
            'F2': 'Флекс (1 цвет)',
            'DTF2': 'Полноцвет с трансфером',
            'B2': 'Шелкография на текстиль (6 цветов)'
        }

        # 1. Обрабатываем методы нанесения из поля prints
        if self.xml_data and 'attributes' in self.xml_data and 'prints' in self.xml_data['attributes']:
            for print_data in self.xml_data['attributes']['prints']:
                if 'description' in print_data:
                    printing_info['methods'].add(print_data['description'])
                elif 'code' in print_data and print_data['code'] in PRINTING_METHODS:
                    printing_info['methods'].add(PRINTING_METHODS[print_data['code']])

        # 2. Также проверяем фильтры, где могут быть указаны методы нанесения
        if self.xml_data and 'filters' in self.xml_data:
            for f in self.xml_data['filters']:
                if str(f.get('type_id')) == '28':  # Вид нанесения
                    printing_info['methods'].add(f.get('filter_name'))

        # 3. Проверяем поле модели application_type
        if self.application_type:
            printing_info['methods'].add(self.get_application_type_display())

        # 4. Проверяем requires_marking
        if self.requires_marking:
            printing_info['marking'] = self.get_marking_type_display() if self.marking_type else 'Да'

        # Преобразуем в отсортированный список по длине строки (от самой длинной к самой короткой)
        if printing_info['methods']:
            printing_info['methods'] = sorted(printing_info['methods'], key=lambda x: len(x), reverse=True)
        else:
            printing_info['methods'] = None

        return printing_info



    def _get_filter_value(self, filter_type, filter_id):
        """Преобразует type_id и filter_id в читаемое название"""
        filter_mapping = {
            '5': {'22': 'Кнопка', '51': 'Молния'},
            '8': {  # Виды нанесения
                '229': 'Шелкография',
                '232': 'Термопечать',
                '233': 'Вышивка',
                '234': 'УФ-печать',
                '235': 'Лазерная гравировка',
                '236': 'Сублимация'
            },
            '21': {'14': 'Чёрный'},  # Цвета
            '73': {'2': 'Хлопок'}  # Материалы
        }
        return filter_mapping.get(filter_type, {}).get(filter_id, None)

    def get_max_available_quantity(self, size=None):
        """Возвращает максимальное доступное количество для размера"""
        if size and self.variants.exists():
            variant = self.variants.filter(size=size).first()
            return variant.quantity if variant else 0
        return self.quantity

    def get_variant_quantity(self, size=None):
        """Возвращает количество для конкретного размера"""
        if size and self.variants.exists():
            variant = self.variants.filter(size=size).first()
            return variant.quantity if variant else 0
        return self.quantity

    def update_quantity(self):
        """Обновляет общее количество на основе вариантов"""
        total = self.productvariantthrough_set.aggregate(
            total_quantity=models.Sum('quantity')
        )['total_quantity'] or 0
        self.quantity = total
        self.save(update_fields=['quantity'])

    def get_sizes_with_quantities(self):
        """Возвращает список размеров с их количеством"""
        sizes = []
        excluded_terms = [
            'мужские', 'женские', 'унисекс', 'male', 'female', 'unisex',
            'для мужчин', 'для женщин', 'для детей', 'детские',
            'муж', 'жен', 'м', 'ж', 'man', 'woman', 'men', 'women'
        ]

        # Если есть варианты, берем из них
        if self.variants.exists():
            for variant in self.variants.all():
                size = variant.size.strip()
                if size and not any(term.lower() in size.lower() for term in excluded_terms):
                    # Получаем связь через промежуточную модель
                    through = ProductVariantThrough.objects.filter(
                        product=self,
                        variant=variant
                    ).first()

                    if through:
                        sizes.append({
                            'size': variant.size,
                            'quantity': through.quantity
                        })
        # Иначе берем из sizes_available с общим количеством
        elif self.sizes_available:
            for size in self.sizes_available.split(','):
                size = size.strip()
                if size and not any(term.lower() in size.lower() for term in excluded_terms):
                    sizes.append({
                        'size': size,
                        'quantity': self.quantity
                    })

        return sizes

    def clean_sizes(self):
        """Минимальная очистка размеров (только базовое форматирование)"""
        if not self.sizes_available:
            return None
        return ', '.join([s.strip() for s in self.sizes_available.split(',') if s.strip()])

    def save(self, *args, **kwargs):
        # Очищаем и нормализуем размеры перед сохранением
        self.sizes_available = self.clean_sizes()

        # Обновляем общее количество на основе вариантов
        if self.variants.exists():
            self.quantity = sum(v.quantity for v in self.variants.all())
            self.in_stock = self.quantity > 0
        super().save(*args, **kwargs)




# models.py - добавить новые модели


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
class ProductVariantThrough(models.Model):
    """
    Промежуточная модель для связи товара с вариантами
    """
    product = models.ForeignKey(
        XMLProduct,
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        verbose_name='Размер'
    )
    quantity = models.PositiveIntegerField(
        'Количество для товара',
        default=0
    )
    price = models.DecimalField(
        'Цена для этого товара',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    old_price = models.DecimalField(
        'Старая цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )


    # Дублируем артикул и штрих-код (если могут быть уникальными для товара)
    item_sku = models.CharField(
        'Артикул позиции',
        max_length=100,
        blank=True,
        help_text="Артикул для конкретной связки товар-размер"
    )

    item_barcode = models.CharField(
        'Штрих-код позиции',
        max_length=50,
        blank=True,
        help_text="Уникальный штрих-код для связки товар-размер"
    )

    class Meta:
        verbose_name = 'Связь товара с размером'
        verbose_name_plural = 'Связи товаров с размерами'
        unique_together = [('product', 'variant')]  # Одна связь на пару товар-размер

    def __str__(self):
        return f"{self.product.name} - {self.variant.size}"

    def get_price(self):
        """Возвращает цену варианта (индивидуальную или из продукта)"""
        return self.price or self.product.price

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

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def merge_with_session_cart(self, session_cart):
        """Объединяет текущую корзину с корзиной из сессии"""
        logger = logging.getLogger('cart')
        logger.debug(f"Starting cart merge: user_cart={self.id}, session_cart={session_cart.id}")

        for session_item in session_cart.items.all():
            # Ищем такой же товар в корзине пользователя
            existing_item = self.items.filter(
                xml_product=session_item.xml_product,
                size=session_item.size
            ).first()

            if existing_item:
                # Если товар уже есть - увеличиваем количество
                existing_item.quantity += session_item.quantity
                existing_item.save()
                logger.debug(f"Merged item: {session_item.xml_product.name}, new qty: {existing_item.quantity}")
            else:
                # Если нет - создаем новый элемент
                session_item.cart = self
                session_item.pk = None
                session_item.save()
                logger.debug(f"Added new item: {session_item.xml_product.name}")

        # Удаляем корзину сессии
        session_cart.delete()
        logger.debug("Session cart deleted after merge")

        return self


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Корзина')
    )
    product = models.ForeignKey(
        'Product',
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
    size = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    selected_sizes = models.JSONField(
        _('Выбранные размеры'),
        default=dict,
        blank=True,
        help_text="Словарь с размерами и их количеством в формате {'size': quantity}"
    )

    class Meta:
        verbose_name = _('Элемент корзины')
        verbose_name_plural = _('Элементы корзины')

    @property
    def total_price(self):
        product = self.product or self.xml_product
        return product.price * self.quantity



class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, _('Создан')),
        (STATUS_IN_PROGRESS, _('Ожидает оплаты')),
        (STATUS_COMPLETED, _('Доставляется')),
        (STATUS_DELIVERED, _('Доставлен')),
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
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Компания')
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
    order_number = models.UUIDField(
        _('Номер заказа'),
        default=uuid.uuid4,
        editable=False
    )
    tracker = FieldTracker(fields=['status'])



    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']

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
        'Product',
        on_delete=models.PROTECT,
        verbose_name=_('Товар'),
        null=True,
        blank=True
    )
    xml_product = models.ForeignKey(
        XMLProduct,
        on_delete=models.PROTECT,
        verbose_name=_('XML Товар'),
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(_('Количество'), default=1)
    price = models.DecimalField(_('Цена'), max_digits=10, decimal_places=2)
    size = models.CharField(_('Размер'), max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _('Элемент заказа')
        verbose_name_plural = _('Элементы заказа')

    @property
    def total_price(self):
        return self.price * self.quantity

class Invoice(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    excel_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    sent = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    document = models.ForeignKey(
        'accounts.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )

    class Meta:
        verbose_name = _('Счет')
        verbose_name_plural = _('Счета')

    def save(self, *args, **kwargs):
        # Автоматическое создание документа при создании счета
        if not self.pk and not self.document and self.pdf_file:
            doc = Document.objects.create(
                company=self.order.company,
                doc_type='invoice',
                file=self.pdf_file,
                signed=False,
                invoice=self  # Связываем документ со счетом
            )
            self.document = doc
        super().save(*args, **kwargs)


class DeliveryAddress(models.Model):
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='delivery_addresses'
    )
    address = models.TextField(_('Адрес доставки'))
    is_default = models.BooleanField(_('Адрес по умолчанию'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Адрес доставки')
        verbose_name_plural = _('Адреса доставки')
        ordering = ['-is_default', '-created_at']

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




