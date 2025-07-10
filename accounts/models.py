
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


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
 # БИК


    inn = models.CharField('ИНН', max_length=12)
    legal_name = models.CharField('Юридическое название', max_length=255)
    email = models.EmailField('Email компании', unique=True)
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

    def get_activity(self):
        """Возвращает активность компании для отображения в ЛК"""
        from main.models import Order, Invoice
        from django.utils import timezone

        activity = []

        # Заказы компании
        orders = Order.objects.filter(company=self).order_by('-created_at')[:10]

        for order in orders:
            activity.append({
                'type': 'order_created',
                'object': order,
                'date': order.created_at,
                'message': f'Создан заказ #{order.id}',
                'status': order.get_status_display()
            })

            if hasattr(order, 'invoice'):
                invoice = order.invoice
                activity.append({
                    'type': 'invoice_issued',
                    'object': invoice,
                    'date': invoice.created_at,
                    'message': f'Выставлен счет #{invoice.invoice_number}',
                    'status': 'Оплачен' if invoice.paid else 'Ожидает оплаты'
                })

            if order.status == Order.STATUS_IN_PROGRESS:
                activity.append({
                    'type': 'order_pending',
                    'object': order,
                    'date': order.updated_at,
                    'message': f'Заказ #{order.id} ожидает оплаты',
                    'status': 'Ожидает оплаты'
                })

        return sorted(activity, key=lambda x: x['date'], reverse=True)[:15]

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
    invoice = models.OneToOneField(
        'main.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_link'
    )

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