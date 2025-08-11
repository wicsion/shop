from django.db import migrations


def add_methods(apps, schema_editor):
    pass  # Методы уже добавлены в модель


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0010_cartitem_selected_sizes'),  # Замените на последнюю миграцию
    ]

    operations = [
        migrations.RunPython(add_methods),
    ]