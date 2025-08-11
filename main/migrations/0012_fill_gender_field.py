# 0012_fill_gender_field.py
from django.db import migrations


def normalize_gender_value(gender):
    """Унифицированная функция нормализации значения пола"""
    if not gender:
        return None

    gender = str(gender).lower().strip()
    gender_mapping = {
        'мужские': 'male',
        'male': 'male',
        'м': 'male',
        'муж': 'male',
        'для мужчин': 'male',
        'men': 'male',
        'man': 'male',
        'женские': 'female',
        'female': 'female',
        'ж': 'female',
        'жен': 'female',
        'для женщин': 'female',
        'women': 'female',
        'woman': 'female',
        'унисекс': 'unisex',
        'unisex': 'unisex',
        'уни': 'unisex',
        'для всех': 'unisex'
    }

    # Проверяем полное совпадение
    if gender in gender_mapping:
        return gender_mapping[gender]

    # Проверяем частичное совпадение
    for key, value in gender_mapping.items():
        if key in gender:
            return value

    return None


def get_gender_from_xml_data(xml_data):
    """Получаем пол из XML данных"""
    if not xml_data:
        return None

    # 1. Проверяем XML атрибуты
    if 'attributes' in xml_data and xml_data['attributes'].get('gender'):
        normalized = normalize_gender_value(xml_data['attributes']['gender'])
        if normalized:
            return normalized

    # 2. Проверяем XML фильтры (type_id=23)
    if 'filters' in xml_data:
        for f in xml_data['filters']:
            if str(f.get('type_id')) == '23' and f.get('filter_name'):
                normalized = normalize_gender_value(f['filter_name'])
                if normalized:
                    return normalized

    # 3. Проверяем название и описание
    name = (xml_data.get('name') or '').lower()
    description = (xml_data.get('description') or '').lower()

    if any(word in name or word in description
           for word in ['мужск', 'male', 'man', 'для муж']):
        return 'male'
    elif any(word in name or word in description
             for word in ['женск', 'female', 'woman', 'для жен']):
        return 'female'
    elif any(word in name or word in description
             for word in ['унисекс', 'unisex', 'для всех']):
        return 'unisex'

    return None


def fill_gender_field(apps, schema_editor):
    XMLProduct = apps.get_model('main', 'XMLProduct')

    # Обновляем только товары с пустым полем
    products = XMLProduct.objects.filter(gender__isnull=True) | \
               XMLProduct.objects.filter(gender='')

    batch_size = 1000
    total_updated = 0

    while True:
        batch = list(products[:batch_size])
        if not batch:
            break

        updated_count = 0

        for product in batch:
            # Получаем пол из XML данных
            gender = get_gender_from_xml_data(product.xml_data)

            if gender:
                product.gender = gender
                product.save(update_fields=['gender'])
                updated_count += 1

        total_updated += updated_count
        print(f"Обновлено {updated_count} товаров в этой партии")

        # Если в партии не было обновлений, выходим
        if updated_count == 0:
            break

    print(f"Всего обновлено товаров: {total_updated}")


def reverse_fill_gender_field(apps, schema_editor):
    """Откат миграции - очищаем поле gender"""
    XMLProduct = apps.get_model('main', 'XMLProduct')
    XMLProduct.objects.update(gender=None)


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0011_add_gender_methods'),
    ]

    operations = [
        migrations.RunPython(
            fill_gender_field,
            reverse_code=reverse_fill_gender_field
        ),
    ]