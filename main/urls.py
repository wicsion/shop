from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_view, name='search'),  # Добавлено
    path('category/<int:pk>/', views.category_detail, name='category-detail'),
    path('news/<int:pk>/', views.news_detail, name='news-detail'),
    path('welcome-pack/<int:pk>/', views.welcome_pack_detail, name='welcome-pack-detail'),
    path('contact/', views.contact, name='contact'),
    path('personal-cabinet/', views.personal_cabinet, name='personal_cabinet'),
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
]