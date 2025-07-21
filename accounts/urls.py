from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views


from . import views  # Добавьте этот импорт
from .forms import EmailAuthenticationForm
from .views import add_delivery_address, delete_delivery_address, SupportTicketCreateView
from .views import download_document
app_name = 'accounts'

urlpatterns = [
    path('register/', views.CompanyRegisterView.as_view(), name='company_register'),

    # Авторизация
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=EmailAuthenticationForm),  # Добавляем кастомную форму
         name='login'
         ),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='registration/logged_out.html',
        next_page='/'),  # Перенаправление на главную после выхода
         name='logout'),

    # Личный кабинет
    path('dashboard/', views.CompanyDashboardView.as_view(), name='company_dashboard'),
    path('add_delivery_address/', add_delivery_address, name='add_delivery_address'),
    path('delete_delivery_address/<int:address_id>/', delete_delivery_address, name='delete_delivery_address'),
path('add-user/', views.AddUserToCompanyView.as_view(), name='add_user_to_company'),


    # Документы
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),

    # Заказы
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),

    # Профиль компании
    path('profile/', views.CompanyProfileUpdateView.as_view(), name='company_profile'),

    # Подтверждение email
    path('verify-email-sent/', views.EmailVerificationSentView.as_view(), name='verify_email_sent'),
    path('verify-email/<str:token>/', views.verify_company_email, name='verify_company_email'),
    path('invalid-token/', views.InvalidTokenView.as_view(), name='invalid_token'),
    path('resend-verification/<int:company_id>/', views.resend_verification, name='resend_verification'),
    path('check-verification/<int:company_id>/', views.check_verification_status, name='check_verification_status'),
    path('dashboard/financial/', views.FinancialDashboardView.as_view(), name='financial_dashboard'),
    path('dashboard/orders/', views.OrdersDashboardView.as_view(), name='orders_dashboard'),
    path('dashboard/documents/', views.DocumentsDashboardView.as_view(), name='documents_dashboard'),
    path('dashboard/activity/', views.ActivityDashboardView.as_view(), name='activity_dashboard'),
    path('dashboard/stats/', views.StatsDashboardView.as_view(), name='stats_dashboard'),
    path('team/', views.TeamDashboardView.as_view(), name='team_dashboard'),
path('support/', views.SupportTicketCreateView.as_view(), name='support_ticket'),
path('password-reset/',
     auth_views.PasswordResetView.as_view(
         template_name='registration/password_reset.html',
         email_template_name='registration/password_reset_email.html',
         subject_template_name='registration/password_reset_subject.txt',
         success_url=reverse_lazy('accounts:password_reset_done')
     ),
     name='password_reset'),
path('password-reset/done/',
     auth_views.PasswordResetDoneView.as_view(
         template_name='registration/password_reset_done.html'
     ),
     name='password_reset_done'),
path('password-reset/confirm/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(
         template_name='registration/password_reset_confirm.html',
         success_url=reverse_lazy('accounts:password_reset_complete')
     ),
     name='password_reset_confirm'),
path('password-reset/complete/',
     auth_views.PasswordResetCompleteView.as_view(
         template_name='registration/password_reset_complete.html'
     ),
     name='password_reset_complete'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<str:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('documents/<int:pk>/download/', download_document, name='download_document'),








]