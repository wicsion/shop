# views.py
from django.views.generic import CreateView, UpdateView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Company, Document, Order, AuditLog, CustomUser
from .forms import CompanyRegistrationForm, DocumentUploadForm, OrderCreateForm
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta


class CompanyRegisterView(CreateView):
    model = Company
    form_class = CompanyRegistrationForm
    template_name = 'registration/company_register.html'
    success_url = reverse_lazy('accounts:verify_email_sent')

    @transaction.atomic
    def form_valid(self, form):
        print("Начало обработки формы регистрации компании")

        try:
            # Сохраняем компанию с временным токеном подтверждения
            company = form.save(commit=False)
            company.organization_type = form.data.get('organization_type', 'ООО')
            company.company_status = form.data.get('company_status', 'Действующее')
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
            company.verification_token = token
            company.verification_token_created_at = timezone.now()  # Время создания токена
            company.is_verified = False

            print(f"Данные формы: {form.data}")
            print(f"Organization type: {form.data.get('organization_type')}")
            print(f"Company status: {form.data.get('company_status')}")
            print(f"Сохранение компании: {company.legal_name}")
            company.save()

            # Создаем администратора компании
            admin_user = CustomUser.objects.create(
                email=form.cleaned_data['email'],
                password=make_password(form.cleaned_data['password']),
                company=company,
                role=form.cleaned_data['role'],
                is_active=False,
                phone='',
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                middle_name=form.cleaned_data.get('middle_name', '')  # Сохраняем отчество
            )
            print(f"Создан пользователь: {admin_user.email}")

            # Отправляем email с подтверждением
            verification_url = self.request.build_absolute_uri(
                reverse('accounts:verify_company_email', kwargs={'token': token})
            )
            print(f"Ссылка подтверждения: {verification_url}")

            subject = 'Подтверждение регистрации компании'
            message = (
                f'Для завершения регистрации вашей компании "{company.legal_name}" перейдите по ссылке:\n\n'
                f'{verification_url}\n\n'
                f'Ваши данные для входа:\n'
                f'Email: {admin_user.email}\n'
                f'Пароль: {form.cleaned_data["password"]}\n\n'
                'Ссылка действительна в течение 5 минут.\n\n'
                'После входа вам будет предложено сменить пароль.'
            )

            print(f"Отправка email на {admin_user.email}")
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [admin_user.email],
                fail_silently=False,
            )

            # Сохраняем ID компании в сессии
            self.request.session['new_company_id'] = company.id
            print(f"Сохранено в сессии: new_company_id={company.id}")

            print(f"Перенаправление на: {self.success_url}")
            return redirect(self.success_url)

        except Exception as e:
            print(f"Ошибка при обработке формы: {str(e)}")
            messages.error(self.request, f'Ошибка при регистрации: {str(e)}')
            return self.form_invalid(form)


def verify_company_email(request, token):
    try:
        company = Company.objects.get(verification_token=token)

        # Проверяем, не истекло ли время действия токена (5 минут)
        token_age = timezone.now() - company.verification_token_created_at
        if token_age > timedelta(minutes=5):
            messages.error(request, '❌ Срок действия ссылки истёк. Пожалуйста, запросите новую.')
            return redirect('accounts:invalid_token')

        # Подтверждаем компанию и активируем пользователя
        company.is_verified = True
        company.verification_token = None
        company.verification_token_created_at = None
        company.save()

        admin_user = CustomUser.objects.get(email=company.email)
        admin_user.is_active = True
        admin_user.save()

        # Авторизуем пользователя
        login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')

        return redirect('accounts:company_dashboard')

    except (Company.DoesNotExist, CustomUser.DoesNotExist):
        messages.error(request, '❌ Недействительная ссылка подтверждения')
        return redirect('accounts:invalid_token')

    except Exception as e:
        messages.error(request, f'❌ Ошибка: {str(e)}')
        return redirect('accounts:invalid_token')


class CompanyDashboardView(LoginRequiredMixin, ListView):
    template_name = 'accounts/company_dashboard.html'

    def get_queryset(self):
        return {
            'documents': Document.objects.filter(company=self.request.user.company),
            'orders': Order.objects.filter(company=self.request.user.company),
            'audit_logs': AuditLog.objects.filter(company=self.request.user.company)
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        user = self.request.user

        admin_user = CustomUser.objects.filter(company=company, role='admin').first()
        manager_user = CustomUser.objects.filter(company=company, role='manager').first()

        context.update({
            'company': company,
            'admin_user': admin_user,
            'manager_user': manager_user,
            'user': user,
        })
        return context

class InvalidTokenView(TemplateView):
    template_name = 'accounts/emails/invalid_token.html'


class DocumentUploadView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = 'accounts/upload_document.html'

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'dashboard/create_order.html'

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)


class CompanyProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Company
    fields = ['legal_address', 'bank_account', 'bank_bik']
    template_name = 'accounts/company_dashboard.html'

    def get_object(self):
        return self.request.user.company


def resend_verification(request, company_id):
    try:
        company = get_object_or_404(Company, id=company_id)

        # Генерируем новый токен и обновляем время
        new_token = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        company.verification_token = new_token
        company.verification_token_created_at = timezone.now()
        company.save()

        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_company_email', kwargs={'token': new_token})
        )

        subject = 'Повторное подтверждение регистрации компании'
        message = (
            f'Для завершения регистрации вашей компании "{company.legal_name}" перейдите по ссылке:\n\n'
            f'{verification_url}\n\n'
            f'Ссылка действительна в течение 5 минут.\n\n'
            f'Если вы не запрашивали повторную отправку, проигнорируйте это письмо.'
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [company.email],
            fail_silently=False,
        )

        messages.success(request, '✅ Письмо с подтверждением отправлено повторно')
        return redirect('accounts:verify_email_sent')

    except Exception as e:
        messages.error(request, f'❌ Ошибка: {str(e)}')
        return redirect('accounts:invalid_token')


def check_verification_status(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    return JsonResponse({
        'is_verified': company.is_verified,
        'company_name': company.legal_name
    })


class EmailVerificationSentView(TemplateView):
    template_name = 'registration/verify_email_sent.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.request.session.get('new_company_id')
        if company_id:
            company = get_object_or_404(Company, id=company_id)
            context['company'] = company
            context['expiration_minutes'] = 5  # Время действия ссылки

            if company.verification_token:
                context['verification_link'] = self.request.build_absolute_uri(
                    reverse('accounts:verify_company_email', kwargs={'token': company.verification_token})
                )
        return context


class FinancialDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/financial_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company

        context.update({
            'company': company,
            'total_orders_amount': 1245000,
            'average_order_amount': 24900,
            'unpaid_invoices': 245000,
        })
        return context


class OrdersDashboardView(LoginRequiredMixin, ListView):
    template_name = 'accounts/orders_dashboard.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(company=self.request.user.company).order_by('-created_at')[:10]


class DocumentsDashboardView(LoginRequiredMixin, ListView):
    template_name = 'accounts/documents_dashboard.html'
    context_object_name = 'documents'

    def get_queryset(self):
        return Document.objects.filter(company=self.request.user.company).order_by('-created_at')[:10]


class ActivityDashboardView(LoginRequiredMixin, ListView):
    template_name = 'accounts/activity_dashboard.html'
    context_object_name = 'audit_logs'

    def get_queryset(self):
        return AuditLog.objects.filter(company=self.request.user.company).order_by('-timestamp')[:10]


class StatsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/stats_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company

        context.update({
            'company': company,
            'orders_count': Order.objects.filter(company=company).count(),
            'documents_count': Document.objects.filter(company=company).count(),
            'completed_orders': Order.objects.filter(
                company=company,
                status='completed'
            ).count(),
            'new_messages': 3,
        })
        return context


class TeamDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/team_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.request.user.company
        return context