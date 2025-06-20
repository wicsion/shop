from django.http import JsonResponse, Http404
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.shortcuts import get_object_or_404, redirect , render
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from .models import Product, Category, Cart, CartItem, Order, Wishlist,Brand,  Slider, Partner, OrderItem
from .forms import AddToCartForm, OrderForm, ProductReviewForm, SearchForm
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
        context['sliders'] = Slider.objects.filter(is_active=True).order_by('order')
        context['featured_categories'] = Category.objects.filter(
            is_featured=True, parent__isnull=True
        ).order_by('order')[:12]
        context['featured_products'] = Product.objects.filter(
            is_featured=True, in_stock=True
        ).order_by('-created_at')[:8]
        context['new_products'] = Product.objects.filter(
            is_new=True, in_stock=True
        ).order_by('-created_at')[:8]
        context['bestsellers'] = Product.objects.filter(
            is_bestseller=True, in_stock=True
        ).order_by('-created_at')[:8]
        context['partners'] = Partner.objects.filter(is_active=True).order_by('order')
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
        print("All category slugs:", list(Category.objects.values_list('slug', flat=True)))
        category = self.object

        # Получаем товары с учетом фильтров
        products = Product.objects.filter(
            category=category,
            in_stock=True
        ).select_related('brand', 'category').prefetch_related('images')

        # Фильтрация по брендам
        brands = Brand.objects.filter(products__category=category).distinct()
        context['brands'] = brands

        # Фильтрация по подкатегориям
        subcategories = category.children.all()
        context['subcategories'] = subcategories

        # Применение фильтров из GET-параметров
        brand_slugs = self.request.GET.get('brands', '').split(',')
        if brand_slugs and brand_slugs[0]:
            products = products.filter(brand__slug__in=brand_slugs)

        min_price = self.request.GET.get('min_price')
        if min_price:
            try:
                products = products.filter(price__gte=float(min_price))
            except ValueError:
                pass

        max_price = self.request.GET.get('max_price')
        if max_price:
            try:
                products = products.filter(price__lte=float(max_price))
            except ValueError:
                pass

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

        # Пагинация
        per_page = int(self.request.GET.get('per_page', 12))
        paginator = Paginator(products, per_page)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context['products'] = page_obj
        context['selected_brands'] = brand_slugs
        context['selected_sort'] = sort_by
        context['search_form'] = SearchForm()

        # Минимальная и максимальная цена для подсказок
        price_range = products.aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = price_range['min_price']
        context['max_price'] = price_range['max_price']

        return context


class BrandListView(ListView):
    model = Brand
    template_name = 'main/brand_list.html'
    context_object_name = 'brands'

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
        products = Product.objects.filter(brand=brand, in_stock=True)

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


class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id).order_by('?')[:4]
        context['add_to_cart_form'] = AddToCartForm()
        context['search_form'] = SearchForm()
        return context


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            messages.success(request, _('Товар добавлен в корзину'))

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'cart_total': cart.total_quantity,
                    'message': str(_('Товар добавлен в корзину'))
                })

            return redirect('main:cart_view')

    return redirect('main:product_detail', slug=product.slug)


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
                    'item_total': cart_item.total_price,
                    'cart_subtotal': cart.total_price,
                    'message': str(_('Количество товара обновлено'))
                })

    return redirect('main:cart_view')


def cart_view(request):
    cart = get_cart(request)
    order_form = OrderForm()

    context = {
        'cart': cart,
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
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
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
        # Пробуем найти категорию по slug или названию без учета регистра
        categories = Category.objects.filter(
            Q(slug__iexact=query) |
            Q(name__iexact=query) |
            Q(name__icontains=query_raw) |
            Q(name__icontains=query_raw.capitalize())
        ).distinct()

        if categories.exists():
            return redirect('main:category_detail', slug=categories.first().slug)

        # Ищем товары, если категорий нет
        results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(sku__icontains=query),
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



class CheckoutView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'main/checkout.html'
    success_url = reverse_lazy('main:order_success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart.objects.get_or_create_for_request(self.request)
        context['cart'] = cart
        return context

    def form_valid(self, form):
        cart = Cart.objects.get_or_create_for_request(self.request)
        order = form.save(commit=False)
        order.user = self.request.user if self.request.user.is_authenticated else None
        order.save()

        for item in cart.items.all():
            order.items.create(
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        cart.items.all().delete()
        messages.success(self.request, 'Ваш заказ успешно оформлен!')
        return super().form_valid(form)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get_or_create_for_request(request)

    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            messages.success(request, 'Товар добавлен в корзину')
            return redirect('main:cart')

    return redirect('main:product_detail', slug=product.slug)


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, 'Товар удален из корзины')
    return redirect('main:cart')


def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Для добавления в избранное необходимо авторизоваться')
        return redirect('accounts:login')

    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.add(product)
    messages.success(request, 'Товар добавлен в избранное')
    return redirect('main:product_detail', slug=product.slug)


class ProductListView(ListView):
    model = Product
    template_name = 'main/product_list.html'
    paginate_by = 12
    context_object_name = 'products'

    def get_queryset(self):
        queryset = super().get_queryset().filter(in_stock=True)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent__isnull=True)
        return context



class CartView(DetailView):
    model = Cart
    template_name = 'main/cart.html'

    def get_object(self, queryset=None):
        cart, created = Cart.objects.get_or_create_for_request(self.request)
        return cart


class WishlistView(DetailView):
    model = Wishlist
    template_name = 'main/wishlist.html'

    def get_object(self, queryset=None):
        if not self.request.user.is_authenticated:
            raise Http404("Wishlist is available only for authenticated users")
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist


def search_suggestions(request):
    query = request.GET.get('q', '').strip().lower()
    results = {
        'categories': [],
        'products': []
    }

    if len(query) >= 2:
        # Поиск по категориям (и точные, и частичные совпадения)
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
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(sku__icontains=query),
            in_stock=True
        ).select_related('category')[:5]

        results['products'] = [
            {
                'name': prod.name,
                'url': reverse('main:product_detail', kwargs={'slug': prod.slug}),
                'price': str(prod.price),
                'image': prod.images.filter(is_main=True).first().image.url if prod.images.filter(
                    is_main=True).exists() else '',
                'category': prod.category.name,
                'type': 'product'
            }
            for prod in products
        ]

    return JsonResponse(results)