from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import *

def index(request):
    context = {
        'welcome_packs': WelcomePack.objects.all()[:3],
        'categories': ProductCategory.objects.all()[:8],
        'portfolio': PortfolioProject.objects.all()[:6],
        'news': News.objects.all()[:3]
    }
    return render(request, 'main/index.html', context)

def category_detail(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    return render(request, 'main/category_detail.html', {'category': category})

def news_detail(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    return render(request, 'main/news_detail.html', {'news_item': news_item})

def welcome_pack_detail(request, pk):
    pack = get_object_or_404(WelcomePack, pk=pk)
    return render(request, 'main/welcome_pack_detail.html', {'pack': pack})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        ContactRequest.objects.create(name=name, email=email, message=message)
        return render(request, 'main/contact_success.html')
    return redirect('index')

def personal_cabinet(request):
    return render(request, 'main/personal_cabinet.html')


def search_view(request):
    query = request.GET.get('q', '')
    # Добавьте логику поиска, например:
    # results = Product.objects.filter(name__icontains=query)
    context = {
        'query': query,
        'results': []  # Замените на реальные результаты
    }
    return render(request, 'main/search.html', context)


def search_autocomplete(request):
    term = request.GET.get('term')
    products = Product.objects.filter(name__icontains=term).values_list('name', flat=True)
    return JsonResponse(list(products), safe=False)

