from django.test import TestCase
from main.models import XMLProduct, ProductVariant


class SizeNormalizationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем тестовые данные
        cls.product = XMLProduct.objects.create(
            name="Test Product",
            sizes_available="женские XS, S, мужские L"
        )
        cls.variant = ProductVariant.objects.create(
            product=cls.product,
            size="3XL",
            quantity=10
        )

    def test_product_size_normalization(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.sizes_available, "XS, S, L")

    def test_variant_size_normalization(self):
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.size, "XXXL")

    def test_all_products_have_clean_sizes(self):
        bad_products = XMLProduct.objects.exclude(
            sizes_available__regex=r'^([X]?[SML]|X{1,3}L|3XL|4XL|5XL)(,\s*([X]?[SML]|X{1,3}L|3XL|4XL|5XL))*$'
        )
        self.assertEqual(bad_products.count(), 0)