from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
import pdfkit

from .models import Order
import logging
import os

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def send_invoice_on_status_change(sender, instance, created, **kwargs):
    """
    Отправляет счет на оплату при изменении статуса заказа на 'ожидает оплаты'
    """
    logger.info(f"Проверка заказа #{instance.id}. Статус: {instance.status}")

    # Проверяем что статус изменился на 'in_progress'
    if instance.status == 'in_progress':
        # Проверяем что это новый заказ или статус изменился
        status_changed = created
        if hasattr(instance, 'tracker'):
            status_changed = instance.tracker.has_changed('status')

        if status_changed:
            logger.info(f"Статус заказа #{instance.id} изменился на 'ожидает оплаты'")

            try:
                # 1. Генерация PDF
                pdf_content = generate_invoice_pdf(instance)
                if not pdf_content:
                    raise ValueError("Не удалось сгенерировать PDF")

                # 2. Подготовка письма
                subject = f"Счет на оплату заказа #{instance.id}"

                # Используем шаблон для текста письма
                message = render_to_string('main/emails/invoice_email.txt', {
                    'order': instance,
                    'site_name': settings.SITE_NAME,
                })

                email = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.email],
                    reply_to=[settings.DEFAULT_FROM_EMAIL],
                )

                # Прикрепляем PDF
                email.attach(
                    f"Счет_{instance.id}.pdf",
                    pdf_content,
                    "application/pdf"
                )

                # Отправка с обработкой ошибок
                try:
                    email.send(fail_silently=False)
                    logger.info(f"Счет для заказа #{instance.id} отправлен на {instance.email}")
                except Exception as send_error:
                    logger.error(f"Ошибка отправки письма: {str(send_error)}")
                    # Можно добавить повторную попытку или уведомление админу

            except Exception as e:
                logger.error(f"Ошибка при формировании счета: {str(e)}", exc_info=True)
                # Логируем полную информацию об ошибке


def generate_invoice_pdf(order):  # Принимает `order`, а не `instance`
    try:
        # Проверка путей к wkhtmltopdf (оставляем как было)
        possible_paths = [
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
            os.getenv('WKHTMLTOPDF_PATH', ''),
            '/usr/local/bin/wkhtmltopdf',
            '/usr/bin/wkhtmltopdf'
        ]

        wkhtmltopdf_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                wkhtmltopdf_path = path
                break

        if not wkhtmltopdf_path:
            raise Exception("wkhtmltopdf not found. Tried paths: " + ", ".join(filter(None, possible_paths)))

        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

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
        company = order.company or order.user.company
        # Контекст для шаблона (исправлено: `order` вместо `instance`)
        context = {
            'order': order,
            'site_name': getattr(settings, 'SITE_NAME', 'Интернет-магазин'),
            'payer_details': {
                'name': company.legal_name,
                'inn': getattr(company, 'inn', ''),
                'legal_address': getattr(company, 'legal_address', ''),
                'bank_account': getattr(company, 'bank_account', ''),
                'bank_bik': getattr(company, 'bank_bik', ''),



            },
            'items': order.items.all(),
        }

        html = render_to_string('main/invoice_pdf.html', context)
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        return pdf

    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
        return None
