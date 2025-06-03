from django.db import models
from django.urls import reverse


class WelcomePack(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to='welcome_packs/', verbose_name="Изображение")

    def get_absolute_url(self):
        return reverse('welcome-pack-detail', args=[str(self.id)])


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(verbose_name="Описание", blank=True)  # Добавьте это поле
    image = models.ImageField(upload_to='categories/', verbose_name="Изображение")

    def get_absolute_url(self):
        return reverse('category-detail', args=[str(self.id)])

class PortfolioProject(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название проекта")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to='portfolio/', verbose_name="Изображение")


class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    excerpt = models.TextField(verbose_name="Краткое описание")
    content = models.TextField(verbose_name="Содержание")
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    def get_absolute_url(self):
        return reverse('news-detail', args=[str(self.id)])


class ContactRequest(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True)

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name="Категория")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to='products/', verbose_name="Изображение")
    description = models.TextField(verbose_name="Описание")