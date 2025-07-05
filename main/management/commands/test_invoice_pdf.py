from django.core.management.base import BaseCommand
from django.conf import settings  # Add this import
from main.models import Order
from main.signals import generate_invoice_pdf
import os


class Command(BaseCommand):
    help = 'Test PDF invoice generation'

    def handle(self, *args, **options):
        try:
            # Get the most recent order with 'in_progress' status
            order = Order.objects.filter(status='in_progress').last()

            if not order:
                self.stdout.write(self.style.WARNING('No order with "in_progress" status found'))
                return

            self.stdout.write(f"Testing invoice generation for order #{order.id}")

            # Generate PDF
            pdf_content = generate_invoice_pdf(order)

            if pdf_content:
                # Save to file
                output_path = os.path.join(settings.BASE_DIR, f'test_invoice_{order.id}.pdf')
                with open(output_path, 'wb') as f:
                    f.write(pdf_content)

                self.stdout.write(
                    self.style.SUCCESS(f'Success! PDF saved to: {output_path}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to generate PDF (check logs for details)')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )