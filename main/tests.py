from django.test import TestCase
from main.models import Category, XMLProduct  # Убедитесь, что XMLProduct импортирован


class CategoryModelTest(TestCase):
    def test_create_category(self):
        category = Category.objects.create(
            xml_id="58",
            name="Тестовая категория",
            slug="test-category"
        )
        self.assertEqual(category.xml_id, "58")
        self.assertEqual(str(category), "Тестовая категория")


class XMLProductModelTest(TestCase):
    def test_product_with_categories(self):
        category1 = Category.objects.create(xml_id="58", name="Категория 58", slug="cat-58")
        category2 = Category.objects.create(xml_id="46252", name="Категория 46252", slug="cat-46252")

        product = XMLProduct.objects.create(
            product_id="123",
            name="Тестовый товар",
            code="TEST123",
            price=100.00,  # Обязательное поле (Decimal)
            quantity=1,  # Обязательное поле (PositiveInteger)
            description="Тестовое описание",
            brand="Тестовый бренд",  # CharField (не обязательное, но лучше заполнить)
            status="regular",  # Обязательное (выбор из 'new', 'regular', 'limited')
            in_stock=True,  # BooleanField (default=True, можно не указывать)

            # Дополнительные поля с тестовыми значениями:
            group_id="TEST_GROUP",
            old_price=150.00,
            small_image="http://example.com/small.jpg",
            big_image="http://example.com/big.jpg",
            super_big_image="http://example.com/super_big.jpg",
            material="Тестовый материал",
            weight=0.5,
            volume=1.0,
            barcode="123456789012",
            is_featured=False,
            is_bestseller=False,
            size_type="Универсальный",
            composition="100% тест",
            density="150 г/м²",
            min_order_quantity=1,
            packaging="Коробка",
            delivery_time="1-2 дня",
            production_time="3 дня",
            print_areas={},
            care_instructions="Стирать вручную",
            product_size="M",
            xml_data={},  # JSONField (можно пустой dict)

            # Для ImageField можно не указывать значения в тестах
            # small_image_local=None,
            # big_image_local=None,
            # super_big_image_local=None,

            # attachments - JSONField (можно пустой list)
            attachments=[],
        )
        product.categories.add(category1, category2)

        self.assertEqual(product.categories.count(), 2)
        self.assertTrue(product.categories.filter(xml_id="58").exists())