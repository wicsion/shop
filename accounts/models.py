# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.template.context_processors import static
from django.contrib.auth.models import BaseUserManager
from django.core.validators import MinValueValidator

import uuid





class Company(models.Model):
    ORGANIZATION_TYPES = (
        ('ООО', 'Общество с ограниченной ответственностью'),
        ('АО', 'Акционерное общество'),
        ('ИП', 'Индивидуальный предприниматель'),
    )
    STATUS_CHOICES = (
        ('Действующее', 'Действующее'),
        ('Ликвидировано', 'Ликвидировано'),

    )

    inn = models.CharField('ИНН', max_length=12, unique=True)
    legal_name = models.CharField('Юридическое название', max_length=255)
    email = models.EmailField('Email компании', unique=True)
    # Остальные поля сделаны необязательными
    kpp = models.CharField('КПП', max_length=9, blank=True, null=True)
    legal_address = models.TextField('Юридический адрес', blank=True, null=True)
    bank_account = models.CharField('Расчетный счет', max_length=20, blank=True, null=True)
    bank_bik = models.CharField('БИК', max_length=9, blank=True, null=True)
    ogrn_scan = models.FileField('Скан ОГРН', upload_to='company_docs/', blank=True, null=True)
    authorization_doc = models.FileField('Доверенность', upload_to='company_docs/', blank=True, null=True)
    contract_scan = models.FileField('Договор оферты', upload_to='company_docs/', blank=True, null=True)
    organization_type = models.CharField(
        'Тип организации',
        max_length=20,
        choices=ORGANIZATION_TYPES,
        default='ООО'
    )
    company_status = models.CharField(
        'Статус компании',
        max_length=20,
        choices=STATUS_CHOICES,
        default='Действующее'
    )

    verification_token = models.CharField(
        'Токен подтверждения',
        max_length=100,
        blank=True,
        null=True
    )
    verification_token_created_at = models.DateTimeField(
        'Время создания токена',
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(
        'Подтвержден',
        default=False
    )

    def __str__(self):
        return self.legal_name

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLES = (
        ('admin', 'Администратор'),
        ('accountant', 'Бухгалтер'),
        ('manager', 'Менеджер закупок'),
    )
    username = None
    email = models.EmailField('Email', unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    role = models.CharField('Роль', max_length=20, choices=ROLES)
    phone = models.CharField('Телефон', max_length=20)
    two_factor_auth = models.BooleanField('2FA', default=False)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    middle_name = models.CharField('Отчество', max_length=150, blank=True, null=True)
    objects = CustomUserManager()
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
        default='avatars/default.png'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []



    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        return static('avatars/default.png')


    def has_perm(self, perm, obj=None):
        return self.role == 'admin'

    def get_full_name(self):
        """
        Возвращает first_name, last_name и middle_name (если есть) с пробелом между ними.
        """
        full_name = f"{self.last_name} {self.first_name}"
        if self.middle_name:
            full_name += f" {self.middle_name}"
        return full_name.strip()


class AuditLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.TextField('Действие')
    timestamp = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    DOC_TYPES = (
        ('invoice', 'Счет-фактура'),
        ('act', 'Акт'),
        ('contract', 'Договор'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    doc_type = models.CharField('Тип', max_length=20, choices=DOC_TYPES)
    file = models.FileField('Файл', upload_to='documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    signed = models.BooleanField('Подписано', default=False)
    signature = models.TextField('ЭЦП', null=True, blank=True)

class SupportTicket(models.Model):
    TICKET_TYPES = (
        ('general', 'Общий вопрос'),
        ('legal', 'Юридический'),
        ('payment', 'Оплата'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    ticket_type = models.CharField('Тип обращения', max_length=20, choices=TICKET_TYPES)
    message = models.TextField('Сообщение')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField('Решено', default=False)

class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='accounts_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Корзина пользователя {self.user.email}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def items_count(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)  # ID из XML или другой системы
    product_name = models.CharField(max_length=255)
    product_image = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} ({self.quantity})"

    @property
    def total_price(self):
        return self.price * self.quantity

class Order(models.Model):
    ORDER_STATUSES = (
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    order_number = models.UUIDField('Номер заказа', default=uuid.uuid4, editable=False)
    status = models.CharField('Статус', max_length=20, choices=ORDER_STATUSES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Примечания', blank=True, null=True)

    def __str__(self):
        return f"Заказ #{self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    product_image = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} ({self.quantity})"

class Invoice(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    excel_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    sent = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Счет {self.invoice_number} для заказа #{self.order.order_number}"



class DeliveryAddress(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='delivery_addresses')
    address = models.TextField('Адрес доставки')
    is_default = models.BooleanField('Адрес по умолчанию', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Адрес доставки'
        verbose_name_plural = 'Адреса доставки'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.address} ({'по умолчанию' if self.is_default else ''})"