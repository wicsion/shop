from django.core.management.base import BaseCommand
from main.models import Category
import requests
from xml.etree import ElementTree as ET
from django.utils.text import slugify
from urllib.parse import urljoin
from collections import defaultdict


class Command(BaseCommand):
    help = 'Import categories from Project 111 XML feed'

    CATEGORY_SLUG_MAPPING = {
        # Основные категории
        'Каталог': 'catalog',
        'Корпоративная одежда с логотипом': 'odezhda',
        'Дом': 'dom',
        'Отдых': 'otdyh',
        'Посуда': 'posuda',
        'Ручки с логотипом': 'ruchki',
        'Сумки': 'sumki',
        'Зонты с логотипом': 'zonty',
        'Электроника и гаджеты': 'elektronika',
        'Корпоративные подарки': 'korporativnye-podarki',
        'Ежедневники и блокноты': 'ezhednevniki-i-bloknoty',
        'Корпоративные подарки на Новый год': 'novogodnie-podarki',
        'Сувениры к праздникам': 'suveniry',
        'Упаковка': 'upakovka',
        'Подарочные наборы': 'podarochnye-nabory',
        'Коллекции с принтами': 'kollekcii',
        'Съедобные корпоративные подарки с логотипом': 'vkusnye-podarki',
        'Спортивные товары с логотипом': 'sportivnye-tovary',
        'Элементы брендирования и кастомизации': 'brendirovanie',

        # Подкатегории одежды
        'Брюки и шорты с логотипом': 'bryuki-i-shorty',
        'Футболки с логотипом': 'futbolki',
        'Кепки и бейсболки с логотипом': 'kepki-i-beysbolki',
        'Рубашки поло с логотипом': 'rubashki-polo',
        'Толстовки с логотипом': 'tolstovki',
        'Ветровки с логотипом': 'vetrovki',
        'Худи с логотипом': 'svitshoty-i-hudi',
        'Футболки с длинным рукавом': 'longslivy',
        'Спортивные костюмы с логотипом': 'sportivnye-kostyumy',
        'Жилеты с логотипом': 'zilety',
        'Фартуки с логотипом': 'fartuki',
        'Детская одежда с логотипом': 'detskaya-odezhda',
        'Вязаные изделия с логотипом': 'vyazanye-izdeliya',

        # Подкатегории посуды
        'Кружки с логотипом': 'kruzhki',
        'Термокружки с логотипом': 'termokruzhki',
        'Чайные наборы с логотипом': 'chaynye-nabory',
        'Кофейные наборы с логотипом': 'kofeynye-nabory',
        'Бокалы с логотипом': 'bokaly',
        'Фляжки с логотипом': 'flyazhki',
        'Ланчбоксы с логотипом': 'lanchboksy',

        # Подкатегории электроники
        'Power Bank с логотипом': 'powerbank',
        'Флешки с логотипом': 'fleshki',
        'Наушники с логотипом': 'naushniki',
        'Умные часы с логотипом': 'umnye-chasy',
        'Гаджеты с логотипом': 'gadzhety',

        # Подкатегории сумок
        'Рюкзаки с логотипом': 'ryukzaki',
        'Сумки для ноутбука с логотипом': 'sumki-dlya-noutbuka',
        'Дорожные сумки с логотипом': 'dorozhnye-sumki',
        'Эко-сумки с логотипом': 'eko-sumki',

        # Подкатегории подарков
        'Бизнес-наборы с логотипом': 'biznes-nabory',
        'Наборы из кожи с логотипом': 'kozhanye-nabory',
        'Дорожные наборы с логотипом': 'dorozhnye-nabory',
        'Винные наборы с логотипом': 'vinnye-nabory',
        'Чайные наборы с логотипом': 'chaynye-nabory',
        'Кофейные наборы с логотипом': 'kofeynye-nabory',
        'Наборы для пикника с логотипом': 'nabory-dlya-piknika',

        # Специальные категории
        'Новинки': 'novinki',
        'Хиты продаж': 'hity-prodazh',
        'Распродажа': 'rasprodazha',
        'Сезонные предложения': 'sezonnye-predlozheniya',
        'Корпоративные решения': 'korporativnye-resheniya',

        # Дополнительные категории из XML
        'Аксессуары с логотипом': 'aksessuary',
        'Канцтовары с логотипом': 'kantstovary',
        'Текстиль с логотипом': 'tekstil',
        'Пледы с логотипом': 'pledy',
        'Полотенца с логотипом': 'polotenca',
        'Зонты-трости с логотипом': 'zonty-trosti',
        'Складные зонты с логотипом': 'skladnye-zonty',
        'Детские зонты с логотипом': 'detskie-zonty',
        'Офисные аксессуары с логотипом': 'ofisnye-aksessuary',
        'Настольные наборы с логотипом': 'nastolnye-nabory',
        'Письменные принадлежности с логотипом': 'pismennye-prinadlezhnosti',
        'Упаковочные материалы': 'upakovochnye-materialy',
        'Подарочная упаковка': 'podarochnaya-upakovka',
        'Новогодняя упаковка': 'novogodnyaya-upakovka',
        'Корпоративные сувениры': 'korporativnye-suveniry',
        'Промо-продукция': 'promo-produktsiya',
        'Товары для мероприятий': 'tovary-dlya-meropriyatiy',
        'Эко-продукция': 'eko-produktsiya',
        'Премиум подарки': 'premium-podarki',
        'Аккумуляторы': 'akkumulyatory',
        'Зарядные устройства': 'zaryadnye-ustroystva',
        'Мобильные аксессуары': 'mobilnye-aksessuary',
        'Колонки и наушники': 'kolonki-i-naushniki',
        'Флешки': 'fleshki',
        'Увлажнители воздуха': 'uvlazhniteli',
        'Лампы и светильники': 'lampy-i-svetilniki',
        'Бытовая техника': 'bytovaya-tehnika',
        'Умный дом': 'umnyy-dom',
        'Кепки и бейсболки': 'kepki-i-beysbolki',
        'Панамы': 'panamy',
        'Рубашки поло': 'rubashki-polo',
        'Ветровки': 'vetrovki',
        'Свитшоты': 'svitshoty',
        'Куртки': 'kurtki',
        'Кофты из флиса': 'kofty-iz-flisa',
        'Шарфы': 'sharfy',
        'Шапки': 'shapki',
        'Перчатки и варежки': 'perchatki-i-varezhki',
        'Вязаные комплекты': 'vyazanye-komplekty',
        'Джемперы': 'dzhempery',
        'Жилеты': 'zilety',
        'Офисные рубашки': 'ofisnye-rubashki',
        'Аксессуары для одежды': 'aksessuary-dlya-odezhdy',
        'Вязальное производство': 'vyazalnoe-proizvodstvo',
        'Бутылки для воды': 'butylki-dlya-vody',
        'Чайные наборы': 'chaynye-nabory',
        'Кофейные наборы': 'kofeynye-nabory',
        'Бокалы': 'bokaly',
        'Стаканы': 'stakany',
        'Пивные бокалы': 'pivnye-bokaly',
        'Ланчбоксы': 'lanchboksy',
        'Кухонные аксессуары': 'kuhonnye-aksessuary',
        'Мельницы для специй': 'melnicy-dlya-speciy',
        'Разделочные доски': 'razdelochnye-doski',
        'Барные аксессуары': 'barnye-aksessuary',
        'Предметы сервировки': 'predmety-servirovki',
        'Костеры': 'kostery',
        'Заварочные чайники': 'zavarochnye-chayniki',
        'Карандаши': 'karandashi',
        'Эко-ручки': 'eko-ruchki',
        'Металлические ручки': 'metallicheskie-ruchki',
        'Футляры для ручек': 'futlyary-dlya-ruchek',
        'Поясные сумки': 'poyasnye-sumki',
        'Рюкзаки': 'ryukzaki',
        'Сумки для покупок': 'sumki-dlya-pokupok',
        'Сумки для ноутбука': 'sumki-dlya-noutbuka',
        'Сумки для документов': 'sumki-dlya-dokumentov',
        'Зонты-трости': 'zonty-trosti',
        'Малые зонты': 'malye-zonty',
        'Детские зонты': 'detskie-zonty',
        'Настольные аксессуары': 'nastolnye-aksessuary',
        'Кошельки': 'koshelki',
        'Визитницы': 'vizitnitsy',
        'Чехлы для карт': 'chehly-dlya-kart',
        'Чехлы для пропуска': 'chehly-dlya-propuska',
        'Бейджи и ленты': 'beydzhi-i-lenty',
        'Дорожные органайзеры': 'dorozhnye-organajzery',
        'Обложки для документов': 'oblozhki-dlya-dokumentov',
        'Папки, портфели': 'papki-portfeli',
        'Награды': 'nagrady',
        'Книги': 'knigi',
        'Фликеры': 'flikery',
        'Антистрессы': 'antistressy',
        'Брелки': 'brelki',
        'Канцтовары': 'kantstovary',
        'Зажигалки': 'zazhigalki',
        'Ежедневники': 'ezhednevniki',
        'Блокноты': 'bloknoty',
        'Калькуляторы ежедневников': 'kalkulyator-ezhednevnika',
        'Наборы с ежедневниками': 'nabory-s-ezhednevnikami',
        'Упаковка для ежедневников': 'upakovka-dlya-ezhednevnikov',
        'Ежедневники на заказ': 'ezhednevniki-na-zakaz',
        'Коробки': 'korobki',
        'Пакеты': 'pakety',
        'Упаковка на заказ': 'upakovka-na-zakaz',
        'Новогодняя упаковка': 'novogodnyaya-upakovka',
        'Бизнес-наборы': 'biznes-nabory',
        'Наборы из кожи': 'nabory-iz-kozhi',
        'Наборы Welcome Pack': 'nabory-velkom-pak',
        'Дорожные наборы': 'dorozhnye-nabory',
        'Наборы с термокружками': 'nabory-s-termokruzhkami',
        'Наборы с кружками': 'nabory-s-kruzhkami',
        'Наборы с бутылками для воды': 'nabory-s-butylkami-dlya-vody',
        'Наборы с аккумуляторами': 'nabory-s-akkumulyatorami',
        'Наборы с флешками': 'nabory-s-fleshkami',
        'Наборы с пледами': 'nabory-s-pledami',
        'Наборы с мультитулами': 'nabory-s-multitulami',
        'Винные наборы': 'vinnye-nabory',
        'Наборы для сыра': 'nabory-dlya-syra',
        'Наборы для виски': 'nabory-dlya-viski',
        'Кухонные наборы': 'kuhonnye-nabory',
        'Спортивные наборы': 'sportivnye-nabory',
        'Наборы для выращивания': 'nabory-dlya-vyrashchivaniya',
        'Наборы для мужчин': 'nabory-dlya-muzhchin',
        'Наборы для женщин': 'nabory-dlya-zhenshchin',
        'Наборы для детей': 'nabory-dlya-detey',
        'Новогодние наборы': 'novogodnie-nabory',
        'Наборы с ежедневниками': 'nabory-s-ezhednevnikami',
        'Наборы ручек': 'nabory-ruchek',
        'Мультитулы': 'multituly',
        'Фонарики': 'fonariki',
        'Термосы': 'termosy',
        'Походные ножи': 'pokhodnye-nozhi',
        'Компасы': 'compassy',
        'Походные горелки': 'pokhodnye-gorelki',
        'Спальные мешки': 'spalnye-meshki',
        'Продуктовые наборы': 'produktovye-nabory',
        'Мед': 'med',
        'Варенье': 'varene',
        'Чай': 'chaj',
        'Кофе': 'kofe',
        'Шоколад': 'shokolad',
        'Конфеты и сладости': 'konfety-i-sladosti',
        'Снеки': 'sneki',
        'Специи': 'specii',
        'Спортивный инвентарь': 'sportivnyj-inventar',
        'Массажеры': 'massazhery',
        'Самокаты и гироскутеры': 'samokaty-i-giroskutery',
        'Спортивные шейкеры': 'sportivnye-shejkery',
        'Фитнес подарки': 'fitnes-podarki',
        'Спортивные аксессуары': 'sportivnye-aksessuary',
        'Велосипедные аксессуары': 'velosipednye-aksessuary',
        'Спортивные полотенца': 'sportivnye-polotenca',
        'Мячи': 'myachi',
        'Ремувки и пуллеры': 'remuvki-i-pullery',
        'Фурнитура': 'furnitura',
        'Шевроны и стикеры': 'shevrony-i-stikery',
        'Лейблы и шильды': 'lejbly-i-shildy',
        'Ленты, стропы, шнуры': 'lenty-stropy-shnury'
    }

    def handle(self, *args, **options):
        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/tree.xml"

        try:
            response = requests.get(xml_url)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            # Сначала создаем словарь всех категорий
            categories_data = {}
            parent_child_map = defaultdict(list)

            # Собираем все категории и связи родитель-потомок
            for page in root.findall('.//page'):
                page_id_element = page.find('page_id')
                if page_id_element is None:
                    self.stdout.write(self.style.WARNING(f'Skipping page without page_id: {ET.tostring(page)}'))
                    continue
                page_id = page_id_element.text

                name_element = page.find('name')
                if name_element is None:
                    self.stdout.write(self.style.WARNING(f'Skipping page {page_id} without name'))
                    continue
                name = name_element.text

                uri_element = page.find('uri')
                uri = uri_element.text if uri_element is not None else ''

                parent_page_id = page.attrib.get('parent_page_id')

                categories_data[page_id] = {
                    'name': name,
                    'uri': uri,
                    'parent_page_id': parent_page_id
                }

                if parent_page_id:
                    parent_child_map[parent_page_id].append(page_id)

            # Сначала создаем все категории без родителей
            for page_id, data in categories_data.items():
                if not data['parent_page_id']:
                    self.create_category(page_id, data, None)

            # Затем создаем дочерние категории
            for parent_id in parent_child_map:
                if parent_id in categories_data:
                    parent_category = Category.objects.get(xml_id=parent_id)
                    for child_id in parent_child_map[parent_id]:
                        if child_id in categories_data:
                            self.create_category(child_id, categories_data[child_id], parent_category)

            self.stdout.write(self.style.SUCCESS('Successfully imported categories'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing categories: {str(e)}'))
            raise e

    def create_category(self, page_id, data, parent):
        name = data['name']
        # Используем маппинг или slugify как запасной вариант
        slug = self.CATEGORY_SLUG_MAPPING.get(name, slugify(name))

        # Делаем slug уникальным
        original_slug = slug
        counter = 1
        while Category.objects.filter(slug=slug).exclude(xml_id=page_id).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1

        category, created = Category.objects.update_or_create(
            xml_id=page_id,
            defaults={
                'name': name,
                'slug': slug,  # Теперь slug будут как в шаблонах
                'parent': parent,
                'description': '',
                'is_featured': False,
                'image': '',  # В вашем XML нет информации об изображениях
                'order': 0  # Порядок можно добавить из XML если есть
            }
        )

        if created:
            self.stdout.write(f"Created category: {name} (ID: {page_id}, slug: {slug})")
        else:
            self.stdout.write(f"Updated category: {name} (ID: {page_id}, slug: {slug})")