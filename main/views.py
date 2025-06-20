from django.http import JsonResponse, Http404
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from .models import Category, Cart, CartItem, Order, Wishlist, Brand, Slider, Partner, OrderItem, XMLProduct
from .forms import AddToCartForm, OrderForm, SearchForm
from django.core.paginator import Paginator
from django.db.models import Min, Max


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
        print(f"Текущая категория: {category.name}, slug: {category.slug}")

        # Получаем все подкатегории (включая вложенные)
        subcategories = category.get_descendants(include_self=True)

        # Получаем товары для текущей категории и всех её подкатегорий
        products = XMLProduct.objects.filter(
            categories__in=subcategories,
            in_stock=True
        ).order_by('-created_at').distinct()
        print(f"Найдено товаров: {products.count()}")

        # Пагинация
        paginator = Paginator(products, 12)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'subcategories': category.children.all().order_by('order'),
            'products': page_obj,
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
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                xml_product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            messages.success(request, _('Товар добавлен в корзину'))

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': str(_('Товар добавлен в корзину')),
                    'cart_total': cart.total_quantity
                })

            return redirect('main:cart_view')

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
                'total_price': item.quantity * item.xml_product.price
            })

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'order_form': order_form,
        'search_form': SearchForm(),
    }
    return render(request, 'main/cart.html', context)


def checkout(request):
    cart = get_cart(request)

    if cart.items.count() == 0:
        messages.warning(request, _('Ваша корзина пуста'))
        return redirect('main:cart_view')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)

            if request.user.is_authenticated:
                order.user = request.user
            else:
                order.session_key = request.session.session_key

            order.save()

            # Переносим товары из корзины в заказ
            for cart_item in cart.items.all():
                if cart_item.xml_product:
                    OrderItem.objects.create(
                        order=order,
                        product=None,
                        xml_product=cart_item.xml_product,
                        quantity=cart_item.quantity,
                        price=cart_item.xml_product.price
                    )

            # Очищаем корзину
            cart.items.all().delete()

            messages.success(request, _('Ваш заказ успешно оформлен! Номер заказа: #{}').format(order.id))
            return redirect('main:order_success', order_id=order.id)
    else:
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
            form = OrderForm(initial=initial)
        else:
            form = OrderForm()

    context = {
        'cart': cart,
        'form': form,
        'search_form': SearchForm(),
    }
    return render(request, 'main/checkout.html', context)


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
                'image': prod.main_image,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Related products
        context['related_products'] = XMLProduct.objects.filter(
            brand=product.brand
        ).exclude(product_id=product.product_id).order_by('?')[:4]

        # Brand info if available
        if product.brand:
            try:
                context['brand'] = Brand.objects.get(name=product.brand)
            except Brand.DoesNotExist:
                pass

        return context