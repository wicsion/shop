from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0012_fill_gender_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='XMLProduct',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('male', 'Мужские'), ('female', 'Женские'), ('unisex', 'Унисекс')],
                max_length=10,
                db_index=True
            ),
        ),
    ]