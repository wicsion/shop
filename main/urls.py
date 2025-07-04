from django.urls import path

from .views import category_search
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import ResizeImageView

app_name = 'main'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/<slug:slug>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('xml-products/', views.XMLProductListView.as_view(), name='xml_product_list'),
    path('xml-products/<str:product_id>/', views.XMLProductDetailView.as_view(), name='xml_product_detail'),
    path('cart/', views.cart_view, name='cart_view'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('add-to-cart/<str:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('search/', views.search, name='search'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    path('category/search/', category_search, name='category_search'),
    path('resize-image/', ResizeImageView.as_view(), name='resize_image'),
    path('order/confirm/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)