from django.contrib.sites import requests
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, F
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
from .models import Category, Cart, CartItem, Order, Brand, Slider, Partner, OrderItem, XMLProduct
from .forms import AddToCartForm, OrderForm, SearchForm
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
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
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

        # Фильтрация по параметрам
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        status = self.request.GET.get('status')
        brands = [b for b in self.request.GET.get('brands', '').split(',') if b] if self.request.GET.get(
            'brands') else []
        materials = [m for m in self.request.GET.get('materials', '').split(',') if m] if self.request.GET.get(
            'materials') else []
        sizes = [s for s in self.request.GET.get('sizes', '').split(',') if s] if self.request.GET.get('sizes') else []
        is_featured = self.request.GET.get('is_featured') == 'true'
        is_bestseller = self.request.GET.get('is_bestseller') == 'true'
        has_discount = self.request.GET.get('has_discount') == 'true'
        in_stock = self.request.GET.get('in_stock') == 'true'
        on_order = self.request.GET.get('on_order') == 'true'

        if min_price:
            products = products.filter(price__gte=float(min_price))
        if max_price:
            products = products.filter(price__lte=float(max_price))
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

        # Получаем уникальные бренды
        brands = products.exclude(brand='').values_list(
            'brand', flat=True
        ).distinct().order_by('brand')

        # Получаем уникальные материалы
        materials = products.exclude(material='').values_list(
            'material', flat=True
        ).distinct().order_by('material')

        # Получаем уникальные размеры
        size_set = set()
        for product in products:
            if product.sizes_available:
                # Разделяем строку с размерами и добавляем в множество
                for size in product.sizes_available.split(','):
                    size = size.strip()
                    if size:
                        size_set.add(size)

        # Сортируем размеры по стандартному порядку
        standard_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', '4XL', '5XL']
        sizes = sorted(size_set, key=lambda x: (
            standard_sizes.index(x) if x in standard_sizes else len(standard_sizes),
            x
        ))

        # Пагинация
        per_page = int(self.request.GET.get('per_page', 12))
        paginator = Paginator(products, per_page)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'subcategories': category.children.all().order_by('order'),
            'products': page_obj,
            'brands': brands,
            'materials': materials,
            'sizes': sizes,
            'status_choices': [
                ('new', 'Новинки'),
                ('limited', 'Ограниченный тираж'),
                ('regular', 'Обычные товары')
            ],
            'selected_status': status,
            'selected_brands': self.request.GET.get('brands', '').split(','),
            'selected_materials': self.request.GET.get('materials', '').split(','),
            'selected_sizes': self.request.GET.get('sizes', '').split(','),
            'current_per_page': per_page,
            'selected_sort': sort_by,
            'search_form': SearchForm()
        })
        return context




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
    product = get_object_or_404(XMLProduct, product_id=product_id)
    cart = get_cart(request)

    if request.method == 'POST':
        form = AddToCartForm(request.POST, product=product)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            selected_size = form.cleaned_data.get('selected_size')

            # Создаем или обновляем элемент корзины
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                xml_product=product,
                size=selected_size,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Товар добавлен в корзину',
                    'cart_total': cart.total_quantity
                })

            messages.success(request, 'Товар добавлен в корзину')
            return redirect('main:cart_view')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
            messages.error(request, 'Ошибка при добавлении в корзину')
            return redirect(product.get_absolute_url())





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

    # Prepare cart items with product data
    cart_items = []
    for item in cart.items.all():
        if item.xml_product:
            cart_items.append({
                'item': item,
                'product': item.xml_product,
                'image': item.xml_product.main_image,
                'total_price': item.quantity * item.xml_product.price,
                'size': item.size  # Добавляем размер в контекст
            })

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'order_form': order_form,
        'search_form': SearchForm(),
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
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # Явно устанавливаем статус "new" при создании заказа
            order.status = Order.STATUS_NEW

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
            # Если форма невалидна, показываем ошибки
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        # Для GET-запроса предзаполняем форму, если пользователь авторизован
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': request.user.phone,
            }
            form = OrderForm(initial=initial)
        else:
            form = OrderForm()

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
        # Поиск по категориям
        categories = Category.objects.filter(
            Q(slug__iexact=query) |
            Q(name__iexact=query) |
            Q(name__icontains=query_raw) |
            Q(name__icontains=query_raw.capitalize())
        ).distinct()

        if categories.exists():
            return redirect('main:category_detail', slug=categories.first().slug)

        # Ищем товары, если категорий нет
        results = XMLProduct.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(code__icontains=query),
            in_stock=True
        ).distinct()

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
        # Поиск по категориям
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

        # Поиск по товарам
        products = XMLProduct.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(code__icontains=query),
            in_stock=True
        )[:5]

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
        product = self.object

        # 1. Получаем полную информацию о размерах из модели
        size_info = product.get_size_info()

        # 2. Формируем удобную структуру sizes_info для шаблона
        sizes_info = []

        # Для товаров с вариантами размеров
        if product.variants.exists():
            for variant in product.variants.all().order_by('size'):
                sizes_info.append({
                    'size': variant.size,
                    'normalized_size': size_info.get('normalized_sizes', [variant.size])[0],
                    'quantity': variant.quantity,
                    'price': variant.price if variant.price is not None else product.price,
                    'old_price': variant.old_price if variant.old_price is not None else product.old_price,
                    'in_stock': variant.quantity > 0,
                    'is_variant': True
                })

        # Для товаров без вариантов, но с таблицей размеров
        elif size_info.get('available_sizes'):
            for i, size in enumerate(size_info['available_sizes']):
                normalized_size = size_info['normalized_sizes'][i] if i < len(
                    size_info.get('normalized_sizes', [])) else size
                sizes_info.append({
                    'size': size,
                    'normalized_size': normalized_size,
                    'quantity': product.quantity,
                    'price': product.price,
                    'old_price': product.old_price,
                    'in_stock': product.quantity > 0,
                    'is_variant': False
                })

        # 3. Подготовка данных для отображения
        has_multiple_prices = any(s['price'] != product.price for s in sizes_info)
        has_size_table = size_info.get('size_table') is not None

        # 4. Добавляем данные в контекст
        context.update({
            'sizes_info': sizes_info,
            'size_data': {
                'available_sizes': [s['size'] for s in sizes_info],
                'normalized_sizes': [s['normalized_size'] for s in sizes_info],
                'size_table': size_info.get('size_table'),
                'gender': size_info.get('gender'),
                'has_size_table': has_size_table,
                'has_multiple_prices': has_multiple_prices,
                'all_sizes_out_of_stock': all(s['quantity'] <= 0 for s in sizes_info) if sizes_info else False
            },
            'printing_data': product.get_printing_info(),
            'product_has_variants': product.variants.exists(),
            'main_product_data': {
                'price': product.price,
                'old_price': product.old_price,
                'quantity': product.quantity,
                'in_stock': product.in_stock
            }
        })

        # 5. Отладочная информация (можно убрать в production)
        if settings.DEBUG:
            context['debug_size_info'] = {
                'source': 'variants' if product.variants.exists() else
                'size_table' if has_size_table else
                'sizes_available' if product.sizes_available else
                'size_field',
                'raw_data': size_info
            }

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


def test_email(request, order_id):
    order = Order.objects.get(id=order_id)
    order.status = Order.STATUS_IN_PROGRESS
    order.save()
    return HttpResponse("Order status changed, check if email was sent")