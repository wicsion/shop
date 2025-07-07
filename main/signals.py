import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import pdfkit
from .models import Order, Invoice
import os
from django.db import transaction
from datetime import datetime, timedelta

logger = logging.getLogger('signals')


def setup_logging():
    """Настройка расширенного логирования"""
    logger.setLevel(logging.DEBUG)

    # Очистка старых обработчиков
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Файловый обработчик
    file_handler = logging.FileHandler('signals.log')
    file_handler.setLevel(logging.DEBUG)

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
        'File "%(pathname)s", line %(lineno)d\n'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


setup_logging()


def process_invoice_for_order(order):
    """Основная функция обработки счета для заказа"""
    try:
        logger.info(f"Starting invoice processing for order #{order.id}")

        # Проверяем, не был ли уже отправлен счет
        if hasattr(order, 'invoice') and order.invoice.sent:
            logger.warning(f"Invoice for order #{order.id} was already sent, skipping")
            return False

        with transaction.atomic():
            logger.debug("Starting transaction for invoice processing")

            # 1. Генерируем PDF счета
            pdf_content = generate_invoice_pdf(order)
            if not pdf_content:
                raise ValueError("Failed to generate PDF invoice")

            # 2. Создаем или обновляем запись Invoice
            invoice, created = Invoice.objects.get_or_create(
                order=order,
                defaults={
                    'invoice_number': f"INV-{order.id}-{datetime.now().strftime('%Y%m%d')}",
                    'due_date': datetime.now() + timedelta(days=7),
                    'amount': order.total_price,
                    'sent': False,
                    'paid': False
                }
            )

            # 3. Подготавливаем и отправляем email
            send_invoice_email(order, invoice, pdf_content)

            return True

    except Exception as e:
        logger.error(f"Error processing invoice for order #{order.id}: {str(e)}", exc_info=True)
        raise


def generate_invoice_pdf(order):
    """Генерация PDF счета"""
    try:
        logger.debug(f"Generating PDF for order #{order.id}")

        # Конфигурация wkhtmltopdf
        config = pdfkit.configuration(
            wkhtmltopdf=find_wkhtmltopdf()
        )

        # Настройки PDF
        options = {
            'encoding': 'UTF-8',
            'quiet': '',
            'margin-top': '15mm',
            'margin-right': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '15mm',
            'footer-center': '[page]/[topage]',
            'footer-font-size': '8'
        }

        # Рендеринг HTML
        context = {
            'order': order,
            'items': order.items.all(),
            'date': datetime.now().strftime('%d.%m.%Y'),
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%d.%m.%Y'),
            'company': order.company if hasattr(order, 'company') else None,
            'site_name': getattr(settings, 'SITE_NAME', 'Интернет-магазин')
        }

        html = render_to_string('main/invoice_pdf.html', context)
        return pdfkit.from_string(html, False, configuration=config, options=options)

    except Exception as e:
        logger.error(f"PDF generation failed for order #{order.id}: {str(e)}", exc_info=True)
        return None


def send_invoice_email(order, invoice, pdf_content):
    """Отправка счета по email"""
    try:
        logger.info(f"Preparing to send invoice email for order #{order.id}")

        if not order.email:
            raise ValueError("No email address specified for order")

        # Подготовка контекста для шаблонов
        context = {
            'order': order,
            'invoice': invoice,
            'site_name': getattr(settings, 'SITE_NAME', 'Интернет-магазин')
        }

        # Подготовка письма (используем EmailMultiAlternatives вместо EmailMessage)
        email = EmailMultiAlternatives(
            subject=f"Счет на оплату заказа #{order.id}",
            body=render_to_string('main/emails/invoice_email.txt', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )

        email.attach(
            f"Счет_{order.id}.pdf",
            pdf_content,
            "application/pdf"
        )

        # Отправка письма
        email.send(fail_silently=False)
        logger.info(f"Invoice email sent successfully for order #{order.id}")

        # Обновление статуса счета
        invoice.sent = True
        invoice.sent_at = datetime.now()
        invoice.save()

    except Exception as e:
        logger.error(f"Failed to send invoice email for order #{order.id}: {str(e)}", exc_info=True)
        raise


def find_wkhtmltopdf():
    """Поиск исполняемого файла wkhtmltopdf"""
    possible_paths = [
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
        os.getenv('WKHTMLTOPDF_PATH', ''),
        '/usr/local/bin/wkhtmltopdf',
        '/usr/bin/wkhtmltopdf'
    ]

    for path in possible_paths:
        if path and os.path.exists(path):
            logger.debug(f"Found wkhtmltopdf at: {path}")
            return path

    error_msg = "wkhtmltopdf not found in any of: " + ", ".join(filter(None, possible_paths))
    logger.error(error_msg)
    raise Exception(error_msg)


@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, created, **kwargs):
    """Обработчик изменения статуса заказа"""
    try:
        logger.debug(f"Order #{instance.id} save signal received. Created: {created}, Status: {instance.status}")

        # Пропускаем новые заказы
        if created:
            logger.debug(f"Skipping newly created order #{instance.id}")
            return

        # Получаем предыдущий статус из базы данных
        try:
            old_order = Order.objects.get(pk=instance.pk)
            old_status = old_order.status
        except Order.DoesNotExist:
            logger.error(f"Order #{instance.id} not found in database")
            return

        logger.info(f"Order #{instance.id} status change: {old_status} -> {instance.status}")

        # Обрабатываем переход в статус 'in_progress'
        if instance.status == 'in_progress' and old_status != 'in_progress':
            logger.info(f"Status changed to 'in_progress' for order #{instance.id}")
            process_invoice_for_order(instance)

    except Exception as e:
        logger.error(f"Error in order status change handler: {str(e)}", exc_info=True)
        raise