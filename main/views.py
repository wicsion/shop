from django.contrib.sites import requests
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, F, Case, When, Value, IntegerField
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
from django.conf import settings
from django.views import View
from django.core.cache import cache
from django.utils.cache import patch_response_headers
import logging
import re
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import unquote, quote
from io import BytesIO
from PIL import Image
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from designer.models import CustomProductOrder
from .models import Category, Cart, CartItem, Order, Brand, Slider, Partner, OrderItem, XMLProduct
from .forms import AddToCartForm, OrderForm, SearchForm, SelectSizesForm
from .models import DeliveryAddress



logger = logging.getLogger(__name__)





class ResizeImageView(View):
    def get(self, request):
        image_url = unquote(request.GET.get('url', ''))
        width = int(request.GET.get('width', 400))
        height = int(request.GET.get('height', 400))
        format = request.GET.get('format', 'webp' if 'image/webp' in request.headers.get('Accept', '') else 'jpeg')

        cache_key = f"resized:{width}x{height}:{format}:{image_url}"
        cached = cache.get(cache_key)

        if cached:
            response = HttpResponse(cached, content_type=f'image/{format}')
            # Кэшировать в браузере на 7 дней
            patch_response_headers(response, cache_timeout=60*60*24*7)
            response['Cache-Control'] = 'public, max-age=604800'  # 7 дней
            return response

        try:
            clean_url = re.sub(r'https?://[^@]+@', 'https://', image_url)
            response = requests.get(
                clean_url,
                auth=HTTPBasicAuth('87358_xmlexport', 'MGzXXSgD'),
                stream=True,
                timeout=5  # Уменьшенный таймаут
            )
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))

            # Оптимизированное изменение размера
            img.thumbnail((width, height), Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format=format, quality=85, optimize=True)
            output.seek(0)

            # Кэшируем результат
            cache.set(cache_key, output.getvalue(), 60 * 60 * 24 * 7)  # 1 неделя

            response = HttpResponse(output.getvalue(), content_type=f'image/{format}')
            # Кэшировать в браузере на 7 дней
            patch_response_headers(response, cache_timeout=60*60*24*7)
            response['Cache-Control'] = 'public, max-age=604800'  # 7 дней
            return response

        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            # Возвращаем прозрачный 1x1 пиксель вместо редиректа
            transparent_pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x04\x00\x09\xfb\x03\xfd\x00\x00\x00\x00IEND\xaeB`\x82'
            response = HttpResponse(transparent_pixel, content_type='image/png')
            # Для ошибок кэшируем на 5 минут
            patch_response_headers(response, cache_timeout=300)
            response['Cache-Control'] = 'public, max-age=300'
            return response


def get_cart(request):
    logger = logging.getLogger('cart')

    if request.user.is_authenticated:
        # Для авторизованных пользователей
        cart, created = Cart.objects.get_or_create(user=request.user)
        logger.debug(f"Got user cart: {cart.id}, created: {created}")

        # Если есть корзина в сессии - объединяем
        if 'cart_session_key' in request.session:
            try:
                session_key = request.session['cart_session_key']
                session_cart = Cart.objects.get(session_key=session_key)
                logger.debug(f"Found session cart to merge: {session_cart.id}")

                # Переносим товары
                for item in session_cart.items.all():
                    existing_item = cart.items.filter(
                        xml_product=item.xml_product,
                        size=item.size
                    ).first()

                    if existing_item:
                        existing_item.quantity += item.quantity
                        existing_item.save()
                        logger.debug(f"Merged item {item.id}, new quantity: {existing_item.quantity}")
                    else:
                        item.cart = cart
                        item.pk = None
                        item.save()
                        logger.debug(f"Added new item {item.id} to user cart")

                # Удаляем сессионную корзину
                session_cart.delete()
                del request.session['cart_session_key']
                logger.debug("Session cart merged and removed")

            except Cart.DoesNotExist:
                logger.debug("No session cart found to merge")
                if 'cart_session_key' in request.session:
                    del request.session['cart_session_key']
    else:
        # Для анонимных пользователей
        if not request.session.session_key:
            request.session.create()
            logger.debug("Created new session for anonymous user")

        session_key = request.session.session_key
        request.session['cart_session_key'] = session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        logger.debug(f"Got session cart: {cart.id}, created: {created}")

    return cart



class HomeView(TemplateView):
    template_name = 'main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем слайдеры
        context['sliders'] = Slider.objects.filter(is_active=True).order_by('order')

        # Получаем основные категории (без родителя)
        main_categories = Category.objects.filter(parent__isnull=True).order_by('order')

        # Собираем данные для категорий как в шаблоне
        categories_data = []
        for category in main_categories:
            # Получаем первые 3 подкатегории
            subcategories = category.children.all().order_by('order')[:3]

            # Получаем товары для категории (первые 3)
            products = XMLProduct.objects.filter(
                categories=category,
                in_stock=True
            ).order_by('-created_at')[:3]

            categories_data.append({
                'category': category,
                'subcategories': subcategories,
                'products': products
            })

        context['categories_data'] = categories_data

        # Получаем бренды
        context['brands'] = Brand.objects.filter(is_active=True).order_by('name')

        # Получаем партнеров
        context['partners'] = Partner.objects.filter(is_active=True).order_by('order')

        # Форма поиска
        context['search_form'] = SearchForm()

        return context


class CategoryListView(ListView):
    model = Category
    template_name = 'main/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        return context


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'main/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object


        # Получаем все подкатегории (включая вложенные)
        subcategories = category.get_descendants(include_self=True)

        # Получаем товары для текущей категории и всех её подкатегорий
        products = XMLProduct.objects.filter(
            categories__in=subcategories
        ).distinct()

        # Фильтрация по цене
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        has_price_filter = False

        if min_price:
            try:
                min_price = float(min_price)
                products = products.filter(price__gte=min_price)
                has_price_filter = True
            except (ValueError, TypeError):
                pass

        if max_price:
            try:
                max_price = float(max_price)
                products = products.filter(price__lte=max_price)
                has_price_filter = True
            except (ValueError, TypeError):
                pass

        # Остальная фильтрация
        status = self.request.GET.get('status')
        brands = self.request.GET.get('brands', '').split(',') if self.request.GET.get('brands') else []
        materials = self.request.GET.get('materials', '').split(',') if self.request.GET.get('materials') else []
        sizes = self.request.GET.get('sizes', '').split(',') if self.request.GET.get('sizes') else []
        genders = self.request.GET.get('genders', '').split(',') if self.request.GET.get('genders') else []
        application_types = self.request.GET.get('application_types', '').split(',') if self.request.GET.get(
            'application_types') else []
        packaging_types = self.request.GET.get('packaging_types', '').split(',') if self.request.GET.get(
            'packaging_types') else []
        marking_types = self.request.GET.get('marking_types', '').split(',') if self.request.GET.get(
            'marking_types') else []
        mechanism_types = self.request.GET.get('mechanism_types', '').split(',') if self.request.GET.get(
            'mechanism_types') else []
        cover_types = self.request.GET.get('cover_types', '').split(',') if self.request.GET.get('cover_types') else []
        umbrella_types = self.request.GET.get('umbrella_types', '').split(',') if self.request.GET.get(
            'umbrella_types') else []

        is_featured = self.request.GET.get('is_featured') == 'true'
        is_bestseller = self.request.GET.get('is_bestseller') == 'true'
        has_discount = self.request.GET.get('has_discount') == 'true'
        in_stock = self.request.GET.get('in_stock') == 'true'
        on_order = self.request.GET.get('on_order') == 'true'
        made_in_russia = self.request.GET.get('made_in_russia') == 'true'
        is_eco = self.request.GET.get('is_eco') == 'true'
        requires_marking = self.request.GET.get('requires_marking') == 'true'
        individual_packaging = self.request.GET.get('individual_packaging') == 'true'

        # Применяем фильтры
        if status:
            products = products.filter(status=status)
        if brands:
            products = products.filter(brand__in=brands)
        if materials:
            material_query = Q()
            for material in materials:
                material_query |= Q(material__icontains=material)
            products = products.filter(material_query)
        if sizes:
            size_query = Q()
            for size in sizes:
                size_query |= Q(sizes_available__icontains=size)
            products = products.filter(size_query)

        genders = self.request.GET.get('genders', '').split(',') if self.request.GET.get('genders') else []

        if genders:
            gender_query = Q()
            for gender in genders:
                if gender == 'male':
                    gender_query |= Q(gender='male')
                elif gender == 'female':
                    gender_query |= Q(gender='female')
                elif gender == 'unisex':
                    # Только унисекс или без указания пола
                    gender_query |= (
                            Q(name__iregex=r'(унисекс|unisex|для всех|оверсайз)') |
                            (
                                    ~Q(name__iregex=r'(мужск|женск|men|women|man|woman|male|female|для муж|для жен)') &
                                    ~Q(name__iregex=r'(унисекс|unisex|для всех|оверсайз)')
                            )
                    )
            products = products.filter(gender_query).distinct()

        if application_types:
            all_products = list(products)
            filtered_products = [
                p for p in all_products
                if any(
                    app_type.lower() in (p.application_type or '').lower() or
                    any(app_type.lower() in (m or '').lower() for m in p.get_printing_info()['methods'] or [])
                    for app_type in application_types
                )
            ]
            products = products.filter(id__in=[p.id for p in filtered_products])

        if is_featured:
            products = products.filter(is_featured=True)
        if is_bestseller:
            products = products.filter(is_bestseller=True)
        if has_discount:
            products = products.filter(old_price__isnull=False, old_price__gt=F('price'))
        if in_stock:
            products = products.filter(in_stock=True, quantity__gt=0)
        if on_order:
            products = products.filter(in_stock=False)
        if made_in_russia:
            products = products.filter(made_in_russia=True)
        if is_eco:
            products = products.filter(is_eco=True)
        if requires_marking:
            products = products.filter(requires_marking=True)
        if individual_packaging:
            products = products.filter(individual_packaging=True)
        if mechanism_types:
            mech_query = Q()
            for mech_type in mechanism_types:
                mech_query |= Q(mechanism_type__icontains=mech_type)
            products = products.filter(mech_query)
        if cover_types:
            cover_query = Q()
            for cover_type in cover_types:
                cover_query |= Q(cover_type__icontains=cover_type)
            products = products.filter(cover_query)
        if umbrella_types:
            umbrella_query = Q()
            for umbrella_type in umbrella_types:
                umbrella_query |= Q(umbrella_type__icontains=umbrella_type)
            products = products.filter(umbrella_query)

        # Сортировка
        # Сортировка
        sort_by = self.request.GET.get('sort', 'default')

        if has_price_filter and sort_by == 'default':
            sort_by = 'price_asc'

        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'name_asc':
            products = products.order_by('name')
        elif sort_by == 'name_desc':
            products = products.order_by('-name')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        else:
            # Сортировка по умолчанию: сначала женские/мужские, потом унисекс
            products = products.annotate(
                gender_order=Case(
                    When(name__iregex=r'(женск|women|woman|female|для жен)', then=Value(1)),
                    When(name__iregex=r'(мужск|men|man|male|для муж)', then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).order_by('gender_order', '-created_at')

        # Получаем доступные типы нанесения
        available_application_types = self._get_available_application_types(products)

        # Получаем доступные полы из всех возможных источников
        available_genders = set()
        for product in products:
            name = (product.name or '').lower()
            if any(word in name for word in ['мужск', 'male', 'man', 'для муж']):
                available_genders.add('male')
            elif any(word in name for word in ['женск', 'female', 'woman', 'для жен']):
                available_genders.add('female')
            elif any(word in name for word in ['унисекс', 'unisex', 'для всех', 'оверсайз']):
                available_genders.add('unisex')

        # Если не найдено явных указаний, предлагаем все варианты
        if not available_genders:
            available_genders.update(['male', 'female', 'unisex'])

        context['available_genders'] = sorted(available_genders)

        # Пагинация
        per_page = int(self.request.GET.get('per_page', 12))
        paginator = Paginator(products, per_page)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Добавляем контекст
        context.update({
            'subcategories': category.children.all().order_by('order'),
            'products': page_obj,
            'brands': products.exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand'),
            'materials': products.exclude(material='').values_list('material', flat=True).distinct().order_by(
                'material'),
            'sizes': self._get_available_sizes(products),
            'available_genders': sorted(available_genders),
            'status_choices': [
                ('new', 'Новинки'),
                ('limited', 'Ограниченный тираж'),
                ('regular', 'Обычные товары')
            ],
            'selected_status': status,
            'selected_brands': brands,
            'selected_materials': materials,
            'selected_sizes': sizes,
            'selected_genders': genders,
            'selected_application_types': application_types,
            'selected_packaging_types': packaging_types,
            'selected_marking_types': marking_types,
            'selected_mechanism_types': mechanism_types,
            'selected_cover_types': cover_types,
            'selected_umbrella_types': umbrella_types,
            'current_per_page': per_page,
            'selected_sort': sort_by,
            'search_form': SearchForm(),
            'is_featured_checked': is_featured,
            'is_bestseller_checked': is_bestseller,
            'has_discount_checked': has_discount,
            'in_stock_checked': in_stock,
            'on_order_checked': on_order,
            'made_in_russia_checked': made_in_russia,
            'is_eco_checked': is_eco,
            'requires_marking_checked': requires_marking,
            'individual_packaging_checked': individual_packaging,
            'has_price_filter': has_price_filter,
            'available_application_types': available_application_types,
        })

        logger.debug(f"Available genders: {available_genders}")
        logger.debug(f"Selected genders: {genders}")

        logger.debug(f"Products after gender filter: {products.count()}")
        return context

    @staticmethod
    def get_normalized_gender(self):
        """Возвращает нормализованное значение пола из всех возможных источников"""
        # Проверяем основное поле gender
        if self.gender:
            normalized = self.normalize_gender_value(self.gender)
            if normalized:
                return normalized

        # Проверяем XML атрибуты
        if self.xml_data and 'attributes' in self.xml_data:
            xml_gender = self.xml_data['attributes'].get('gender')
            if xml_gender:
                normalized = self.normalize_gender_value(xml_gender)
                if normalized:
                    return normalized

        # Проверяем XML фильтры (type_id=23)
        if self.xml_data and 'filters' in self.xml_data:
            for f in self.xml_data['filters']:
                if str(f.get('type_id')) == '23' and f.get('filter_name'):
                    normalized = self.normalize_gender_value(f['filter_name'])
                    if normalized:
                        return normalized

        # Проверяем название товара и описание
        name = self.name.lower()
        description = (self.description or '').lower()

        if any(word in name or word in description
               for word in ['мужск', 'male', 'man', 'для муж']):
            return 'male'
        elif any(word in name or word in description
                 for word in ['женск', 'female', 'woman', 'для жен']):
            return 'female'
        elif any(word in name or word in description
                 for word in ['унисекс', 'unisex', 'для всех']):
            return 'unisex'

        return None


    def _get_available_sizes(self, products):
        size_set = set()
        STANDARD_SIZES = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', '3XL', '4XL', '5XL']

        # Определяем категории одежды
        CLOTHING_CATEGORIES = [
            'Одежда', 'Футболки', 'Кепки и бейсболки', 'Панамы', 'Футболки поло',
            'Футболки с длинным рукавом', 'Промо футболки', 'Ветровки', 'Толстовки',
            'Свитшоты', 'Худи', 'Куртки', 'Флисовые куртки и кофты', 'Шарфы',
            'Трикотажные шапки', 'Перчатки и варежки', 'Вязаные комплекты',
            'Джемперы', 'Жилеты', 'Офисные рубашки', 'Фартуки', 'Спортивная одежда',
            'Брюки и шорты', 'Детская одежда', 'Аксессуары',
            'Худи под нанесение логотипа', 'Футболки с логотипом',
            'Толстовки с логотипом', 'Свитшоты под нанесение логотипа',
            'Брюки и шорты с логотипом'
        ]

        # Проверяем, относится ли текущая категория к одежде
        is_clothing = self.object.name in CLOTHING_CATEGORIES or \
                      any(parent.name in CLOTHING_CATEGORIES for parent in self.object.get_ancestors())

        if not is_clothing:
            return []

        for product in products:
            # 1. Проверяем варианты размеров
            if product.variants.exists():
                for variant in product.variants.all():
                    size = str(variant.size).strip().upper()
                    if size in STANDARD_SIZES:
                        size_set.add(size)

            # 2. Проверяем поле sizes_available
            elif product.sizes_available:
                for size in product.sizes_available.split(','):
                    size = str(size).strip().upper()
                    if size in STANDARD_SIZES:
                        size_set.add(size)

            # 3. Проверяем таблицу размеров в XML
            if product.xml_data and 'attributes' in product.xml_data and 'size_table' in product.xml_data['attributes']:
                size_table = product.xml_data['attributes']['size_table']
                if 'headers' in size_table and len(size_table['headers']) > 1:
                    for size in size_table['headers'][1:]:
                        size = str(size).strip().upper()
                        if size in STANDARD_SIZES:
                            size_set.add(size)

            # 4. Проверяем фильтры из XML (type_id=1 - размеры одежды)
            if product.xml_data and 'filters' in product.xml_data:
                for f in product.xml_data['filters']:
                    if str(f.get('type_id')) == '1' and f.get('filter_name'):
                        size = str(f['filter_name']).strip().upper()
                        if size in STANDARD_SIZES:
                            size_set.add(size)

        return sorted(size_set, key=lambda x: (
            STANDARD_SIZES.index(x) if x in STANDARD_SIZES else len(STANDARD_SIZES),
            x
        ))

    def _get_available_application_types(self, products):
        """Возвращает уникальные типы нанесения для товаров категории"""
        application_types = set()

        for product in products:
            printing_info = product.get_printing_info()
            if printing_info['methods']:
                for method in printing_info['methods']:
                    # Нормализуем названия методов для группировки
                    method_lower = method.lower()
                    if 'шелкография' in method_lower:
                        application_types.add('Шелкография')
                    elif 'вышивка' in method_lower:
                        application_types.add('Вышивка')
                    elif 'флекс' in method_lower:
                        application_types.add('Флекс')
                    elif 'трансфер' in method_lower:
                        application_types.add('Трансфер')
                    elif 'лазер' in method_lower:
                        application_types.add('Лазерная гравировка')
                    elif 'наклейка' in method_lower:
                        application_types.add('Наклейка')
                    elif 'водными чернилами' in method_lower:
                        application_types.add('Полноцвет водными чернилами')
                    elif 'сублимация' in method_lower:
                        application_types.add('Сублимация')
                    elif 'тампопечать' in method_lower:
                        application_types.add('Тампопечать')
                    elif 'тиснение' in method_lower:
                        application_types.add('Тиснение')
                    elif 'уф-dtf' in method_lower:
                        application_types.add('УФ-DTF-печать')
                    elif 'уф-печать' in method_lower:
                        application_types.add('УФ-печать')
                    elif 'офсет' in method_lower:
                        application_types.add('Цифровой офсет')
                    else:
                        application_types.add(method)

        return sorted(application_types)

    def _get_available_genders(self, products):
        """Возвращает уникальные гендерные значения для товаров категории"""
        gender_set = set()

        for product in products:
            name = (product.name or '').lower()

            # Проверяем мужские (исключая женские и унисекс)
            if (any(word in name for word in ['мужск', 'male', 'man', 'для муж']) and
                    not any(word in name for word in ['женск', 'female', 'woman', 'для жен', 'унисекс', 'unisex'])):
                gender_set.add('male')
            # Проверяем женские (исключая мужские и унисекс)
            elif (any(word in name for word in ['женск', 'female', 'woman', 'для жен']) and
                  not any(word in name for word in ['мужск', 'male', 'man', 'для муж', 'унисекс', 'unisex'])):
                gender_set.add('female')
            # Все остальное - унисекс
            else:
                gender_set.add('unisex')

        return sorted(gender_set, key=lambda x: {'male': 0, 'female': 1, 'unisex': 2}[x])





class BrandListView(ListView):
    model = Brand
    template_name = 'main/brand_list.html'
    context_object_name = 'brands'

    def get_queryset(self):
        return Brand.objects.filter(is_active=True).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        return context


class BrandDetailView(DetailView):
    model = Brand
    template_name = 'main/brand_detail.html'
    context_object_name = 'brand'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.object
        products = XMLProduct.objects.filter(brand=brand.name, in_stock=True)

        # Сортировка
        sort_by = self.request.GET.get('sort', 'default')
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'name_asc':
            products = products.order_by('name')
        elif sort_by == 'name_desc':
            products = products.order_by('-name')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')

        context['products'] = products
        context['selected_sort'] = sort_by
        context['search_form'] = SearchForm()
        return context






def add_to_cart(request, product_id):
    logger.info(f"Add to cart request for product_id: {product_id}")

    try:
        product = get_object_or_404(XMLProduct, product_id=product_id)
        logger.info(f"Product found: {product.name} (ID: {product.product_id})")

        cart = get_cart(request)
        logger.info(f"Cart obtained: {cart.id} (User: {cart.user}, Session: {cart.session_key})")

        if request.method == 'POST':
            logger.debug("POST data: %s", request.POST)
            form = AddToCartForm(request.POST, product=product)

            if form.is_valid():
                logger.debug("Form is valid")
                quantity = form.cleaned_data['quantity']
                selected_size = form.cleaned_data.get('size') or form.cleaned_data.get('selected_size')
                logger.info(f"Adding to cart: {product.name}, Qty: {quantity}, Size: {selected_size}")

                # Create cart item
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    xml_product=product,
                    size=selected_size,
                    defaults={'quantity': quantity}
                )

                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()

                logger.info(f"Cart item {'created' if created else 'updated'}: {cart_item.id}")

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Товар добавлен в корзину',
                        'cart_total': cart.total_quantity
                    })

                messages.success(request, 'Товар добавлен в корзину')
                return redirect('main:cart_view')
            else:
                logger.error("Form errors: %s", form.errors.as_json())
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': form.errors.as_json()
                    }, status=400)

                messages.error(request, 'Ошибка при добавлении в корзину')
                return redirect(product.get_absolute_url())

    except Exception as e:
        logger.exception("Error in add_to_cart view")
        raise


def select_sizes(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    product = cart_item.xml_product

    if not product.has_variants:
        messages.error(request, 'Для этого товара не требуется выбор размеров')
        return redirect('main:cart_view')

    if request.method == 'POST':
        form = SelectSizesForm(request.POST, product=product, cart_item=cart_item)
        if form.is_valid():
            selected_sizes = {}
            for size in product.get_available_sizes():
                quantity = form.cleaned_data.get(f'size_{size}', 0)
                if quantity and quantity > 0:
                    selected_sizes[size] = quantity

            if selected_sizes:
                cart_item.selected_sizes = selected_sizes
                # Устанавливаем общее количество
                cart_item.quantity = sum(selected_sizes.values())
                cart_item.save()
                messages.success(request, 'Размеры успешно выбраны')
                return redirect('main:cart_view')
            else:
                messages.error(request, 'Выберите хотя бы один размер')
    else:
        form = SelectSizesForm(product=product, cart_item=cart_item)

    return render(request, 'main/select_sizes.html', {
        'form': form,
        'product': product,
        'cart_item': cart_item,
    })




def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = cart_item.cart

    # Проверка, что корзина принадлежит текущему пользователю или сессии
    if (request.user.is_authenticated and cart.user != request.user) or \
            (not request.user.is_authenticated and cart.session_key != request.session.session_key):
        messages.error(request, _('Ошибка доступа'))
        return redirect('main:cart_view')

    cart_item.delete()
    messages.success(request, _('Товар удален из корзины'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_quantity,
            'message': str(_('Товар удален из корзины'))
        })

    return redirect('main:cart_view')


def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = cart_item.cart

    # Проверка, что корзина принадлежит текущему пользователю или сессии
    if (request.user.is_authenticated and cart.user != request.user) or \
            (not request.user.is_authenticated and cart.session_key != request.session.session_key):
        messages.error(request, _('Ошибка доступа'))
        return redirect('main:cart_view')

    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, _('Количество товара обновлено'))

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'cart_total': cart.total_quantity,
                    'item_total': cart_item.quantity * cart_item.xml_product.price,
                    'cart_subtotal': cart.total_price,
                    'message': str(_('Количество товара обновлено'))
                })

    return redirect('main:cart_view')


def cart_view(request):
    cart = get_cart(request)
    order_form = OrderForm()

    # Обычные товары
    cart_items = []
    regular_total = 0
    has_missing_sizes = False

    for item in cart.items.all():
        if item.xml_product:
            total_price = item.quantity * item.xml_product.price
            regular_total += total_price
            cart_item_data = {
                'item': item,
                'product': item.xml_product,
                'image': item.xml_product.main_image,
                'total_price': total_price,
                'size': item.size,
                'selected_sizes': item.selected_sizes
            }
            cart_items.append(cart_item_data)

            if item.xml_product.has_variants:
                has_selected_sizes = bool(item.selected_sizes) and any(
                    qty > 0 for qty in item.selected_sizes.values()
                )
                if not item.size and not has_selected_sizes:
                    has_missing_sizes = True

    # Кастомные товары
    custom_items = []
    custom_total = 0
    cart_data = request.session.get('cart', {})

    for key, item_data in cart_data.items():
        if item_data.get('type') == 'custom':
            try:
                custom_order = CustomProductOrder.objects.get(id=item_data['id'], in_cart=True)

                # Добавляем информацию об оригинальном товаре, если он есть
                if custom_order.original_product:
                    custom_order.original_product_info = {
                        'name': custom_order.original_product.name,
                        'price': custom_order.original_product.price,
                        'image': custom_order.original_product.main_image,
                        'product_id': custom_order.original_product.product_id,
                        'url': custom_order.original_product.get_absolute_url()
                    }
                else:
                    # Если оригинального товара нет, создаем пустую информацию
                    custom_order.original_product_info = None

                custom_items.append(custom_order)
                custom_total += custom_order.price
            except CustomProductOrder.DoesNotExist:
                del cart_data[key]

    request.session['cart'] = cart_data
    request.session.modified = True

    total_price = regular_total + custom_total

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'custom_items': custom_items,
        'order_form': order_form,
        'has_missing_sizes': has_missing_sizes,
        'total_price': total_price,
    }
    return render(request, 'main/cart.html', context)

def send_order_confirmation_email(request, order):
    # Рендерим HTML содержимое письма из шаблона
    context = {
        'order': order,
        'request': request  # передаем request для корректной работы url-хелперов
    }
    html_content = render_to_string('main/order_email.html', context)

    # Текстовое содержимое (альтернатива для почтовых клиентов, не поддерживающих HTML)
    text_content = f"""
    Ваш заказ #{order.id} успешно создан!

    Статус заказа: {order.get_status_display()}
    Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}
    Сумма: {order.total_price} ₽

    Состав заказа:
    """

    for item in order.items.all():
        product_name = item.xml_product.name if item.xml_product else item.product.name
        text_content += f"\n- {product_name}: {item.quantity} × {item.price} ₽ = {item.total_price} ₽"

    text_content += f"\n\nИтого: {order.total_price} ₽"

    # Создаем email сообщение
    email = EmailMultiAlternatives(
        subject=f"Ваш заказ #{order.id} успешно создан",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    # Прикрепляем HTML версию
    email.attach_alternative(html_content, "text/html")

    # Отправляем письмо (в продакшене лучше использовать Celery)
    try:
        email.send()
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при отправке письма: {str(e)}")


def checkout(request):
    cart = get_cart(request)

    if cart.items.count() == 0:
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('main:cart_view')

    for item in cart.items.all():
        if item.xml_product and item.xml_product.has_variants:
            if not item.size and not item.selected_sizes:
                messages.error(request, f'Для товара "{item.xml_product.name}" необходимо выбрать размеры')
                return redirect('main:cart_view')

    # Подготовка cart_items
    cart_items = []
    for item in cart.items.all():
        if item.xml_product:
            cart_items.append({
                'item': item,
                'product': item.xml_product,
                'image': item.xml_product.main_image,
                'total_price': item.quantity * item.xml_product.price,
                'size': item.size
            })

    if request.method == 'POST':
        form = OrderForm(request.POST, user=request.user)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = Order.STATUS_NEW

            # Если выбран сохраненный адрес
            delivery_address_id = form.cleaned_data.get('delivery_address')
            if delivery_address_id and delivery_address_id != 'new':
                try:
                    address = DeliveryAddress.objects.get(id=delivery_address_id)
                    order.address = address.address
                except DeliveryAddress.DoesNotExist:
                    pass

            if request.user.is_authenticated:
                order.user = request.user
                if hasattr(request.user, 'company'):
                    order.company = request.user.company
            else:
                order.session_key = request.session.session_key

            order.save()

            # Создаем элементы заказа
            for cart_item in cart.items.all():
                if cart_item.xml_product:
                    OrderItem.objects.create(
                        order=order,
                        xml_product=cart_item.xml_product,
                        quantity=cart_item.quantity,
                        price=cart_item.xml_product.price,
                        size=cart_item.size
                    )

            # Очищаем корзину
            cart.items.all().delete()

            # Отправляем письмо с подтверждением
            send_order_confirmation_email(request, order)

            messages.success(request, f'Ваш заказ успешно оформлен! Номер заказа: #{order.id}')
            return redirect('main:order_detail', order_id=order.id)
    else:
        # Для GET-запроса предзаполняем форму, если пользователь авторизован
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': request.user.phone,
            }
            form = OrderForm(initial=initial, user=request.user)
        else:
            form = OrderForm(user=request.user)

    return render(request, 'main/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'form': form,
        'search_form': SearchForm(),
    })



def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Проверка, что заказ принадлежит текущему пользователю или сессии
    if (request.user.is_authenticated and order.user != request.user) or \
            (not request.user.is_authenticated and order.session_key != request.session.session_key):
        messages.error(request, _('Ошибка доступа'))
        return redirect('main:home')

    context = {
        'order': order,
        'search_form': SearchForm(),
    }
    return render(request, 'main/order_success.html', context)


def search(request):
    form = SearchForm(request.GET)
    query_raw = request.GET.get('q', '').strip()
    query = query_raw.lower()
    results = []

    if query:
        # Поиск по категориям (оставляем как есть)
        categories = Category.objects.filter(
            Q(slug__iexact=query) |
            Q(name__iexact=query) |
            Q(name__icontains=query_raw) |
            Q(name__icontains=query_raw.capitalize())
        ).distinct()

        if categories.exists():
            return redirect('main:category_detail', slug=categories.first().slug)

        # Разбиваем запрос на отдельные слова и создаем Q-объекты для каждого слова
        query_words = query.split()
        q_objects = Q()

        for word in query_words:
            # Ищем товары, где название или описание содержит хотя бы одно слово из запроса
            q_objects |= Q(name__icontains=word)
            q_objects |= Q(description__icontains=word)
            q_objects |= Q(code__icontains=word)

        # Добавляем поиск по полному названию (точное совпадение)
        q_objects |= Q(name__iexact=query_raw)

        # Ищем товары, используя созданные Q-объекты
        results = XMLProduct.objects.filter(q_objects, in_stock=True).distinct()

    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'query': query_raw,
        'page_obj': page_obj,
        'search_form': SearchForm(),
    }
    return render(request, 'main/search_results.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '').strip().lower()
    results = {
        'categories': [],
        'products': []
    }

    if len(query) >= 2:
        # Поиск по категориям (оставляем как есть)
        categories = Category.objects.filter(
            Q(name__iexact=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:5]

        results['categories'] = [
            {
                'name': cat.name,
                'url': reverse('main:category_detail', kwargs={'slug': cat.slug}),
                'type': 'category'
            }
            for cat in categories
        ]

        # Разбиваем запрос на отдельные слова и создаем Q-объекты для каждого слова
        query_words = query.split()
        q_objects = Q()

        for word in query_words:
            q_objects |= Q(name__icontains=word)
            q_objects |= Q(description__icontains=word)
            q_objects |= Q(code__icontains=word)

        # Добавляем поиск по полному названию (точное совпадение)
        q_objects |= Q(name__iexact=query)

        # Поиск по товарам с учетом всех условий
        products = XMLProduct.objects.filter(q_objects, in_stock=True)[:5]

        results['products'] = [
            {
                'name': prod.name,
                'url': reverse('main:xml_product_detail', kwargs={'product_id': prod.product_id}),
                'price': str(prod.price),
                'image': f"{reverse('main:resize_image')}?url={quote(prod.main_image)}&width=100&height=100",
                'type': 'product'
            }
            for prod in products
        ]

    return JsonResponse(results)


class XMLProductListView(ListView):
    model = XMLProduct
    template_name = 'main/xml_product_list.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        queryset = super().get_queryset().filter(in_stock=True)

        # Filter by brand
        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            brand = get_object_or_404(Brand, slug=brand_slug)
            queryset = queryset.filter(brand__iexact=brand.name)

        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(categories=category)

        # Filter by status
        status = self.request.GET.get('status')
        if status in ['new', 'regular', 'limited']:
            queryset = queryset.filter(status=status)

        # Sorting
        sort_by = self.request.GET.get('sort', 'default')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.filter(xmlproduct__isnull=False).distinct()
        context['categories'] = Category.objects.filter(parent__isnull=True)
        context['status_choices'] = [
            ('new', 'Новинки'),
            ('limited', 'Ограниченный тираж'),
        ]
        return context


class XMLProductDetailView(DetailView):
    model = XMLProduct
    template_name = 'main/xml_product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'product_id'
    slug_field = 'product_id'

    def get_filter_type_name(self, filter_type):

        type_names = {
            '1': 'Тип товара',
            '5': 'Тип крепления',
            '8': 'Метод нанесения',
            '13': 'Особенность',
            '21': 'Цвет',
            '23': 'Размер',
            '73': 'Материал',
            '93': 'Коллекция'
        }
        return type_names.get(filter_type, f"Фильтр {filter_type}")

    def get_filter_value_name(self, filter_type, filter_id):

        filter_mapping = {
            '5': {'22': 'Кнопка', '51': 'Молния'},
            '8': {'229': 'Шелкография', '232': 'Термопечать'},
            '21': {'14': 'Чёрный'},
            '30': {'48331': 'Лето 2023'}
        }
        return filter_mapping.get(filter_type, {}).get(filter_id, filter_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['designer_url'] = reverse('designer:custom_designer_start') + f'?product_id={self.object.product_id}'
        product = self.object

        # Получаем отфильтрованные размеры
        size_info = product.get_size_info()
        sizes_info = []

        # Формируем информацию о размерах для шаблона
        for size in size_info['available_sizes']:
            variant = product.variants.filter(size__iexact=size).first()
            sizes_info.append({
                'size': size,
                'quantity': variant.quantity if variant else product.quantity,
                'price': variant.price if variant else product.price,
                'old_price': variant.old_price if variant else product.old_price,
                'in_stock': (variant.quantity > 0) if variant else product.in_stock
            })

        # Получаем информацию о бренде
        brand = None
        if product.brand:
            try:
                brand = Brand.objects.filter(name__iexact=product.brand).first()
            except Brand.DoesNotExist:
                pass

        # Получаем похожие товары (из той же категории)
        related_products = XMLProduct.objects.filter(
            categories__in=product.categories.all(),
            in_stock=True
        ).exclude(product_id=product.product_id).distinct()[:4]

        # Получаем читаемые фильтры
        readable_filters = self._get_readable_filters(product)

        # Получаем информацию о нанесении
        printing_data = product.get_printing_info()

        context.update({
            'sizes_info': sizes_info,
            'size_data': size_info,
            'printing_data': printing_data,
            'brand': brand,
            'related_products': related_products,
            'readable_filters': readable_filters,
            'is_available': any(s['quantity'] > 0 for s in sizes_info) if sizes_info else product.in_stock
        })
        return context



    def _get_readable_filters(self, product):
        """Преобразует фильтры из XML в читаемый формат"""
        readable_filters = []
        if product.xml_data and 'filters' in product.xml_data:
            for f in product.xml_data['filters']:
                try:
                    filter_type = f.get('type_id', '') or f.get('type', '')
                    filter_id = f.get('filter_id', '') or f.get('id', '')

                    # Пропускаем фильтры типа 8 (они обрабатываются в printing_info)
                    if str(filter_type) == '8':
                        continue

                    type_name = f.get('type_name', self.get_filter_type_name(filter_type))
                    value_name = f.get('filter_name', self.get_filter_value_name(filter_type, filter_id))

                    if filter_type and filter_id:
                        readable_filters.append({
                            'type': type_name,
                            'value': value_name
                        })
                except (KeyError, AttributeError) as e:
                    logger.error(f"Error processing filter: {e}")
                    continue
        return readable_filters

    def _get_readable_prints(self, product):
        """Преобразует данные о принтах из XML в читаемый формат"""
        readable_prints = []
        if product.xml_data and 'prints' in product.xml_data:
            for p in product.xml_data['prints']:
                try:
                    if p.get('code') and p.get('description'):
                        readable_prints.append({
                            'code': p['code'],
                            'description': p['description']
                        })
                except (KeyError, AttributeError):
                    continue
        return readable_prints





    def clean_image_url(self, url):
        """Очистка URL от параметров размера"""
        return re.sub(r'_\d+x\d+', '', url)

@require_GET
def category_search(request):
    q = request.GET.get('q', '').strip()
    logger.debug(f"Search query: {q}")
    print(f"Request path: {request.path}")
    print(f"Request GET params: {request.GET}")

    if not q:
        return JsonResponse({'results': []})

    categories = Category.objects.filter(name__icontains=q)[:20]

    results = [{
        'id': cat.id,
        'text': cat.name
    } for cat in categories]

    return JsonResponse({'results': results})


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Проверка, что заказ принадлежит текущему пользователю или сессии
    if (request.user.is_authenticated and order.user != request.user) or \
            (not request.user.is_authenticated and order.session_key != request.session.session_key):
        messages.error(request, _('Ошибка доступа'))
        return redirect('main:home')

    context = {
        'order': order,
        'search_form': SearchForm(),
    }
    return render(request, 'main/order_confirmation.html', context)


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Проверка, что заказ принадлежит текущему пользователю или сессии
    if (request.user.is_authenticated and order.user != request.user) or \
            (not request.user.is_authenticated and order.session_key != request.session.session_key):
        messages.error(request, _('Ошибка доступа'))
        return redirect('main:home')

    context = {
        'order': order,
        'search_form': SearchForm(),
    }
    return render(request, 'main/order_detail.html', context)
def application_view(request):
    return render(request, 'main/application.html')

def test_email(request, order_id):
    order = Order.objects.get(id=order_id)
    order.status = Order.STATUS_IN_PROGRESS
    order.save()
    return HttpResponse("Order status changed, check if email was sent")


