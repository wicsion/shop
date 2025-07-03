from django.core.management.base import BaseCommand
from main.models import XMLProduct, ProductVariant, ProductVariantThrough
import requests
from xml.etree import ElementTree as ET
import logging
from tqdm import tqdm
from django.db import transaction
from colorama import init, Fore, Style
from datetime import datetime
import re
from typing import Dict, Optional, Union, Any

init(autoreset=True)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='import_stock.log'
)

# Расширенный список стандартных размеров с приоритетами
SIZE_PRIORITY = {
    'XXXL': 1, 'XXL': 2, 'XL': 3, 'L': 4, 'M': 5, 'S': 6, 'XS': 7,
    'S/M': 8, 'L/XL': 9, 'M/L': 10, 'XL/2XL': 11, 'XS/S': 12, 'XS-XXL': 13,
    '3XL': 14, '4XL': 15, '5XL': 16,
    'ONE SIZE': 17, 'ONESIZE': 18, 'UNISEX': 19,
    'OS': 20  # One Size сокращенно
}

# Словарь для отслеживания найденных размеров
found_sizes = {size: 0 for size in SIZE_PRIORITY}


class Command(BaseCommand):
    help = 'Import product quantities from stock.xml'

    def handle(self, *args, **options):
        start_time = datetime.now()
        self.stdout.write(Fore.YELLOW + f"=== НАЧАЛО ИМПОРТА {start_time} ===" + Style.RESET_ALL)
        logger.info(f"=== НАЧАЛО ИМПОРТА {start_time} ===")

        try:
            # 1. Загрузка данных
            stock_data = self.load_stock_data()

            if not stock_data:
                self.stdout.write(Fore.RED + "Ошибка: не загружено ни одного товара!" + Style.RESET_ALL)
                logger.error("Ошибка: не загружено ни одного товара!")
                return

            # 2. Обновление данных
            stats = self.update_product_quantities(stock_data)

            # Итоговая статистика
            end_time = datetime.now()
            duration = end_time - start_time

            self.stdout.write(Fore.GREEN + "\n=== ИТОГОВАЯ СТАТИСТИКА ===" + Style.RESET_ALL)
            logger.info("\n=== ИТОГОВАЯ СТАТИСТИКА ===")
            self.stdout.write(f"Время выполнения: {duration}")
            logger.info(f"Время выполнения: {duration}")
            self.stdout.write(f"Обновлено товаров: {stats['products']}")
            logger.info(f"Обновлено товаров: {stats['products']}")
            self.stdout.write(f"Обновлено вариантов: {stats['variants']}")
            logger.info(f"Обновлено вариантов: {stats['variants']}")
            self.stdout.write(f"Не найдено товаров: {stats['not_found']}")
            logger.info(f"Не найдено товаров: {stats['not_found']}")

            products_with_variants = sum(1 for data in stock_data.values() if data['variants'])
            self.stdout.write(f"Товаров с вариантами: {products_with_variants}")
            logger.info(f"Товаров с вариантами: {products_with_variants}")

            zero_qty_variants = sum(1 for data in stock_data.values()
                                    for qty in data['variants'].values() if qty == 0)
            self.stdout.write(Fore.YELLOW + f"Вариантов с нулевым количеством: {zero_qty_variants}" + Style.RESET_ALL)
            logger.warning(f"Вариантов с нулевым количеством: {zero_qty_variants}")

            # Выводим статистику по обработанным размерам
            self.stdout.write(Fore.CYAN + "\n=== СТАТИСТИКА ПО РАЗМЕРАМ ===" + Style.RESET_ALL)
            logger.info("\n=== СТАТИСТИКА ПО РАЗМЕРАМ ===")
            for size, count in sorted(found_sizes.items(), key=lambda x: SIZE_PRIORITY[x[0]]):
                status = "[FOUND]" if count > 0 else "[MISSING]"
                color = Fore.GREEN if count > 0 else Fore.RED
                self.stdout.write(f"{size:<8}: {color}{status}{Style.RESET_ALL} (найдено: {count})")
                logger.info(f"{size:<8}: {status} (найдено: {count})")

            unused_sizes = [size for size, count in found_sizes.items() if count == 0]
            if unused_sizes:
                self.stdout.write(
                    Fore.YELLOW + f"\nНеиспользованные размеры: {', '.join(unused_sizes)}" + Style.RESET_ALL)
                logger.warning(f"Неиспользованные размеры: {', '.join(unused_sizes)}")

        except Exception as e:
            self.stdout.write(Fore.RED + f"\nКРИТИЧЕСКАЯ ОШИБКА: {str(e)}" + Style.RESET_ALL)
            logger.exception("Ошибка в основном обработчике")

    def load_stock_data(self) -> Dict[str, Dict[str, Any]]:
        """Улучшенная загрузка данных с проверкой количества"""
        self.stdout.write(Fore.CYAN + "\n[1/2] Загрузка данных из stock.xml..." + Style.RESET_ALL)
        logger.info("[1/2] Загрузка данных из stock.xml...")

        try:
            response = requests.get(
                "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/stock.xml",
                timeout=60
            )
            response.raise_for_status()

            # Парсинг XML
            root = ET.fromstring(response.content)
            if root.tag != 'doct':
                raise ValueError(f"Неожиданный корневой элемент: {root.tag}")

            stocks = root.findall('.//stock')
            self.stdout.write(Fore.GREEN + f"Найдено записей: {len(stocks)}" + Style.RESET_ALL)
            logger.info(f"Найдено записей: {len(stocks)}")

            # Сбор и анализ данных
            product_map: Dict[str, Dict[str, Any]] = {}
            for stock in tqdm(stocks, desc="Анализ товаров"):
                try:
                    product_id = stock.find('product_id').text.strip() if stock.find('product_id') is not None else None
                    code = stock.find('code').text.strip() if stock.find('code') is not None else None
                    amount = int(stock.find('amount').text) if stock.find('amount') is not None else 0

                    if not product_id or not code:
                        continue

                    logger.debug(f"Обработка товара ID: {product_id}, Код: {code}, Количество: {amount}")

                    if product_id not in product_map:
                        product_map[product_id] = {
                            'main': None,
                            'variants': {},
                            'codes': set()
                        }

                    # Определяем тип записи (основной товар или вариант)
                    size = self.detect_size(code)
                    if size:
                        found_sizes[size] += 1
                        logger.debug(f"Найден размер: {size} для кода: {code}")
                        product_map[product_id]['variants'][size] = max(
                            product_map[product_id]['variants'].get(size, 0),
                            amount
                        )
                        logger.debug(f"Установлено количество {amount} для размера {size} товара {product_id}")
                    else:
                        current_main = product_map[product_id]['main']
                        if current_main is None or amount > current_main['amount']:
                            product_map[product_id]['main'] = {
                                'code': code,
                                'amount': amount
                            }
                            logger.debug(f"Установлено основное количество {amount} для товара {product_id}")

                    product_map[product_id]['codes'].add(code)

                except Exception as e:
                    logger.warning(f"Ошибка обработки записи: {e}")
                    continue

            # Формируем итоговые данные
            result: Dict[str, Dict[str, Any]] = {}
            for product_id, data in product_map.items():
                if not data['main'] and not data['variants']:
                    continue

                main_data = data['main'] if data['main'] is not None else {
                    'code': next(iter(data['codes'])),
                    'amount': 0
                }

                variants = {k: v for k, v in data['variants'].items() if v > 0}

                result[product_id] = {
                    'code': main_data['code'],
                    'quantity': main_data['amount'],
                    'variants': variants,
                    'all_codes': list(data['codes'])
                }

                logger.info(f"Товар {product_id}: основное количество={main_data['amount']}, варианты={variants}")

                if variants and main_data['amount'] == 0:
                    self.stdout.write(Fore.YELLOW +
                                      f"Товар {product_id} имеет варианты, но основное количество 0" + Style.RESET_ALL)
                    logger.warning(f"Товар {product_id} имеет варианты, но основное количество 0")

            return result

        except Exception as e:
            self.stdout.write(Fore.RED + f"Ошибка загрузки данных: {str(e)}" + Style.RESET_ALL)
            logger.error(f"Ошибка загрузки данных: {str(e)}")
            return {}

    def detect_size(self, code: str) -> Optional[str]:
        """Улучшенное определение размера с учетом всех вариантов написания"""
        if not code:
            return None

        # Нормализация кода
        original_code = code
        code = code.upper().replace(' ', '').replace('–', '-')
        logger.debug(f"Определение размера для кода: {original_code} -> нормализовано: {code}")

        # Порядок важен - сначала проверяем составные размеры
        composite_sizes = {
            'XS/S': ['XS/S', 'XSS', 'XS_S'],
            'XS-XXL': ['XS-XXL', 'XSXXL'],
            'XL/2XL': ['XL/2XL', 'XL2XL', 'XL_2XL'],
            'M/L': ['M/L', 'ML', 'M_L'],
            'L/XL': ['L/XL', 'LXL', 'L_XL'],
            'S/M': ['S/M', 'SM', 'S_M']
        }

        for size_name, variants in composite_sizes.items():
            if any(variant in code for variant in variants):
                logger.debug(f"Определен составной размер: {size_name} для кода: {original_code}")
                return size_name

        # Проверяем простые размеры
        simple_sizes = ['XXXL', 'XXL', 'XL', 'L', 'M', 'S', 'XS', 'ONE SIZE', 'OS', 'UNISEX']
        for size in simple_sizes:
            if size in code:
                logger.debug(f"Определен простой размер: {size} для кода: {original_code}")
                return size

        logger.debug(f"Размер не определен для кода: {original_code}")
        return None

    def update_product_quantities(self, stock_data: Dict[str, Any]) -> Dict[str, int]:
        """Обновление данных с проверкой логики"""
        stats = {'products': 0, 'variants': 0, 'not_found': 0, 'created': 0}

        with transaction.atomic():
            for product_id, data in tqdm(stock_data.items(), desc="Обновление БД"):
                try:
                    product = XMLProduct.objects.get(product_id=product_id)

                    # Обновляем основное количество товара
                    product.quantity = data['quantity']
                    product.in_stock = data['quantity'] > 0 or any(qty > 0 for qty in data['variants'].values())
                    product.save()
                    stats['products'] += 1

                    # Обновляем варианты размеров
                    for size, qty in data['variants'].items():
                        try:
                            # Получаем или создаем вариант размера
                            variant, created = ProductVariant.objects.get_or_create(
                                size=size,
                                defaults={
                                    'quantity': qty,
                                    'price': product.price,
                                    'old_price': product.old_price,
                                    'barcode': f"{product.code}-{size}",
                                    'sku': f"{product.code}-{size}"
                                }
                            )

                            if created:
                                stats['created'] += 1

                            # Создаем или обновляем связь через промежуточную модель
                            ProductVariantThrough.objects.update_or_create(
                                product=product,
                                variant=variant,
                                defaults={
                                    'quantity': qty,
                                    'price': product.price,
                                    'old_price': product.old_price,
                                    'item_sku': f"{product.code}-{size}",
                                    'item_barcode': f"{product.code}-{size}"
                                }
                            )
                            stats['variants'] += 1

                        except Exception as e:
                            logger.error(f"Ошибка варианта {product_id}/{size}: {e}")

                except XMLProduct.DoesNotExist:
                    stats['not_found'] += 1
                    logger.warning(f"Товар {product_id} не найден")
                except Exception as e:
                    logger.error(f"Ошибка обновления {product_id}: {e}")

        return stats