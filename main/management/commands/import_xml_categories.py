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
        'Корпоративная одежда с логотипом': 'odejda',
        'Дом': 'dom',
        'Отдых': 'otdyh',
        'Посуда': 'posuda',
        'Ручки с логотипом': 'ruchki',
        'Сумки': 'sumki',
        'Зонты с логотипом': 'zonty',
        'Электроника и гаджеты': 'elektronika',
        'Корпоративные подарки': 'korporativnye-podarki',
        'Ежедневники и блокноты': 'ejednevniki-i-bloknoty',
        'Корпоративные подарки на Новый год': 'novyy-god',
        'Сувениры к праздникам': 'suveniry-k-prazdnikam',
        'Упаковка': 'upakovka',
        'Подарочные наборы': 'podarochnye-nabory',
        'Коллекции с принтами': 'podarki-s-printami',
        'Съедобные корпоративные подарки с логотипом': 'sjedobnye-podarki',
        'Спортивные товары с логотипом': 'sportivnye-tovary',
        'Элементы брендирования и кастомизации': 'elementy-kastomizatsii',

        # Подкатегории одежды
        'Брюки и шорты с логотипом': 'bryuki-i-shorty',
        'Ветровки': 'odejda-vetrovki',
        'Промо футболки': 'futbolki-futbolki-dlya-promo',
        'Спортивная одежда': 'odejda-sportivnaya-odezhda',
        'Офисные рубашки': 'odejda-rubashki',
        'Вязаные комплекты': 'odejda-vyazanye-komplekty',
        'Флисовые куртки и кофты': 'flisovye-kurtki-i-kofty',
        'Детская одежда': 'detskaya-odejda',
        'Футболки с логотипом': 'futbolki',
        'Фартуки с логотипом': 'odejda-fartuki',
        'Футболки с длинным рукавом': 'longsleeve',
        'Футболки поло': 'polo-s-logotipom',
        'Шарфы': 'odejda-sharfy',
        'Джемперы и кардиганы': 'odejda-jumper',
        'Дождевики': 'odejda-dojdeviki',
        'Жилеты': 'odejda-jilety',
        'Панамы': 'odejda-panamy',
        'Толстовки с логотипом': 'odejda-tolstovki',
        'Свитшоты под нанесение логотипа': 'sweatshirts',
        'Аксессуары': 'odejda-aksessuary',
        'Трикотажные шапки': 'odejda-trikotajnye-shapki',
        'Перчатки и варежки с логотипом': 'perchatki-i-varejki-s-logotipom',
        'Кепки и бейсболки': 'odejda-kepki',
        'Куртки': 'odejda-kurtki',
        'Худи под нанесение логотипа': 'hoodie',

        # Подкатегории дома
        'Декоративные свечи и подсвечники': 'dom-dekorativnye-svechi',
        'Интерьерные подарки': 'dom-interernye-podarki',
        'Игрушки': 'dom-igrushki',
        'Полотенца с логотипом': 's-polotenca-s-logotipom',
        'Аксессуары и средства для ухода': 'aksessuary-i-sredstva-dlya-uhoda',
        'Пледы': 'dom-pledy',
        'Часы и метеостанции': 'chasy',
        'Домашний текстиль': 'dom-tekstil',

        # Подкатегории отдыха
        'Подушки под шею': 's-podushki-pod-sheyu',
        'Складные ножи с логотипом': 'skladnye-nozhi',
        'Игры и головоломки': 'otdyh-igry',
        'Оптические приборы': 'opticheskie-pribory',
        'Товары для путешествий': 'otdyh-dorojnye-aksessuary',
        'Светодиодные фонарики': 's-svetodiodnye-fonariki',
        'Подарки для дачи': 'podarki-dlya-dachi',
        'Инструменты': 'dom-instrumenty',
        'Автомобильные аксессуары': 'otdyh-avtoprinadlejnosti',
        'Туристические принадлежности': 'otdyh-turisticheskiye-prinadlezhnosti',
        'Мультитулы с логотипом': 'multituly',
        'Пляжный отдых': 'otdyh-plyajnyy-otdyh',
        'Банные принадлежности': 's-bannye-nabory-dlya-mujchin',
        'Наборы для пикника и барбекю с логотипом': 'otdyh-nabory-dlya-piknika',

        # Подкатегории посуды
        'Термокружки с логотипом': 'posuda-termokruzhki',
        'Пивные бокалы с логотипом': 'posuda-pivnye-bokaly',
        'Многоразовые стаканы с крышкой': 'mnogorazovye-stakany-s-kryshkoy',
        'Стаканы': 'posuda-stakany',
        'Термосы для еды с логотипом': 'termosy-dlia-edy',
        'Фляжки с логотипом': 'flyajki-s-logotipom',
        'Кофейные наборы': 's-kofeynye-nabory',
        'Термосы с логотипом': 's-otdyh-thermos',
        'Барные аксессуары': 'posuda-barnye-aksessuary',
        'Разделочные доски': 'razdelochnye-doski',
        'Мельницы для специй': 'melnicy-dlya-speciy',
        'Бокалы': 'posuda-bokaly',
        'Ланч-боксы': 's-lanch-boksy',
        'Кухонные принадлежности': 'dom-kuhonnye-prisposobleniya',
        'Чайные наборы': 's-chaynye-nabory',
        'Кружки с логотипом': 'posuda-krujki',
        'Предметы сервировки': 'posuda-predmety-servirovki',
        'Бутылки для воды': 's-butylka-dlya-vody',
        'Заварочные чайники': 'posuda-zavarochnye-chainiki',
        'Костеры с логотипом': 'kostery',

        # Подкатегории ручек
        'Бумажные и эко ручки с логотипом': 'eko-ruchki-bumazhnye',
        'Наборы с ручками под логотип': 'ruchki-nabory-ruchek',
        'Карандаши с логотипом': 'ruchki-karandashi',
        'Пластиковые ручки с логотипом': 'ruchki-plastikovye',
        'Футляры для ручек': 'futlyary-dlya-ruchek',
        'Металлические ручки с логотипом': 'ruchki-metallicheskie',

        # Подкатегории сумок
        'Сумки через плечо с логотипом': 'sumki-cherez-plecho',
        'Сумки для документов': 'sumki-konferenc-sumki',
        'Сумки для пикника': 'sumki-dlya-piknika',
        'Чемоданы': 'sumki-chemodany',
        'Несессеры и косметички': 'sumki-nesessery',
        'Дорожные сумки': 'sumki-dorojnye',
        'Поясные сумки': 's-sumki-na-poyas',
        'Сумки для ноутбука': 'sumki-sumki-dlya-noutbuka',
        'Рюкзаки': 'sumki-ryukzaki',
        'Шоперы с логотипом': 'sumki-sumki-dlya-pokupok',

        # Подкатегории зонтов
        'Складные зонты с логотипом': 'zonty-skladnye-zonty',
        'Зонты трости с логотипом': 'zonty-zonty-trosti',

        # Подкатегории электроники
        'Лампы и светильники': 'electronica-lampy-i-svetilniki-s-logotipom',
        'Гаджеты для умного дома с логотипом': 'ustroystva-dlya-umnogo-doma',
        'Бытовая техника': 'elektronika-bytovaya-tehnika',
        'Внешние аккумуляторы power bank с логотипом': 'vneshniye-akkumulyatory-powerbanks',
        'Флешки': 'fleshki',
        'Увлажнители воздуха с логотипом': 'uvlajniteli-vozduha',
        'Портативные колонки и наушники': 'elektronika-portativnye-kolonki',
        'Зарядные устройства для телефона с логотипом': 'zariadnye-ustroistva-i-adaptery',
        'Компьютерные и мобильные аксессуары': 'elektronika-aksessuary-dlya-mobilnyh-ustroystv',

        # Подкатегории корпоративных подарков
        'Светоотражатели': 'promo-svetootrajateli',
        'Дорожные органайзеры': 'personalnye-dorojnye-organayzery',
        'Визитницы': 'personalnye-vizitnicy',
        'Настольные аксессуары': 'ofis-nastolnye-aksessuary',
        'Антистрессы': 'promo-antistressy',
        'Бейджи и аксессуары': 'beydzhi-i-aksessuary',
        'Чехлы для пропуска': 'chehly-dlya-propuska',
        'Подарочные книги': 'vip-podarochnye-knigi',
        'Чехлы для карт': 'korporativnye-cartholdery',
        'Кошельки': 'personalnye-koshelki',
        'Зажигалки': 'promo-zajigalki',
        'Канцелярские принадлежности': 'kancelyarskie-prinadlejnosti',
        'Обложки для документов': 'personalnye-oblojki-dlya-dokumentov',
        'Брелки с логотипом': 'brelki-s-logotipom',
        'Папки, портфели': 'korporativnye-papki-portfeli',
        'Награды': 'nagrady',

        # Подкатегории ежедневников
        'Упаковка для ежедневников': 'ejednevniki-upakovka',
        'Блокноты с логотипом': 'bloknoty',
        'Ежедневники с логотипом': 'ejednevniki',
        'Наборы с ежедневниками': 'nabori-s-ejednevnikami',

        # Подкатегории новогодних подарков
        'Новогодние елочные шары': 's-novogodnie-shary',
        'Оригинальные календари': 'novyy-god-originalnye-kalendari',
        'Новогодние подушки и пледы': 'novogodnie-podushki-i-pledy',
        'Новогодние наборы для творчества': 'novogodnie-nabory-dlya-tvorchestva',
        'Новогодние елки с логотипом': 'korporativnye-elki-s-logotipom',
        'Новогодние свечи и подсвечники': 's-novogodnie-svechi',
        'Подарки с символом 2025 года': 'novyy-god-simvol-goda',
        'Новогодние наборы': 's-novogodnie-nabory',
        'Новогодняя вязаная одежда': 'novogodniaia-viazanaia-odezhda',
        'Новогодний стол': 'novogodnie-ukrasheniya-dlya-stola',
        'Новогодние гирлянды и светильники': 'novogodnie-girlyandy-i-svetilniki',
        'Новогодняя упаковка для подарков': 'upakovka-dlya-novogodnih-podarkov',
        'Новогодние елочные игрушки': 'novogodnie-igrushki',
        'Украшения для офиса к новому году': 'novyy-god-dekor-dlya-ofisa',

        # Подкатегории сувениров к праздникам
        'Подарки на День геолога': 'den-geologa',
        'Подарки на День юриста 3 декабря': 'den-yurista',
        'Подарки на День химика': 'den-himika',
        'Подарки на День энергетика 22 декабря': 'podarki-na-den-energetika',
        'Подарки на День России 12 июня': 'podarki-na-den-rossii',
        'Подарки детям': 'den-zashhity-detey',
        'Подарки морякам': 'podarki-moryakam',
        'Подарки на День медицинского работника': 'den-medrabotnika',
        'Подарки начальнику': 'podarki-nachalniku',
        'Подарки на День рождения компании': 'podarki-na-den-rozhdeniya-kompanii',
        'Подарки на День строителя': 'den-stroitelya',
        'Подарки на День учителя 5 октября': 'podarki-na-den-uchitelya',
        'Подарки автомобилисту': 'podarki-avtomobilistu',
        'Подарки программистам': 'podarki-programmistam',
        'Подарки на День железнодорожника': 'den-jeleznodorojnika',
        'Подарки на День авиации': 'den-aviacii',
        'Подарки на 14 февраля': '14-fevralya',
        'Подарки на День Победы 9 мая': 'den-pobedy-9-maya',
        'Подарки на День электросвязи 17 мая': 'den-elektrosvyazi',
        'Подарки на День банковского работника 2 декабря': 'den-bankovskogo-rabotnika',
        'Подарки ко Дню нефтяника': 'den-neftyanika',
        'Подарки на День знаний 1 сентября': 'den-znaniy-1-sentyabrya',
        'Подарки системным администраторам': 'podarki-sistemnym-administratoram',
        'Подарки ко Дню шахтера': 'den-shahtera',
        'Подарки на День полиции (милиции) 10 ноября': 'podarki-na-den-policii',
        'Сувениры к 23 февраля': 'suveniry-k-23-fevralya',
        'Подарки на День металлурга': 'den-metallurga',
        'Сувениры к 8 марта': 'suveniry-k-8-marta',
        'Подарок коллеге': 'podarki-kollege',

        # Подкатегории упаковки
        'Производство полноцветной самосборной упаковки на заказ': 'proizvodstvo-upakovki-na-zakaz',
        'Подарочные коробки': 'podarochnye-korobki',
        'Подарочная упаковка': 'podarochnaya-upakovka',
        'Подарочные пакеты': 'podarochnye-pakety',

        # Подкатегории подарочных наборов
        'Подарочные наборы с мультитулами': 'podarochnye-nabory-s-multitulami',
        'Кухонные подарочные наборы': 'kuhonnye-podarochnye-nabory',
        'Спортивные наборы': 'sportivnye-nabory',
        'Подарочные наборы изделий из кожи с логотипом': 'podarochnye-nabory-iz-koji',
        'Винные наборы': 'dom-vinnye-nabory',
        'Наборы стаканов и камни для виски': 's-nabory-dlya-viski',
        'Наборы для выращивания растений': 'nabory-dlya-vyrashhivaniya-rasteniy',
        'Наборы для сыра': 'podarochnye-nabory-dlya-syra',
        'Подарочные наборы с пледами': 'podarochnye-nabory-s-pledami',
        'Подарочные наборы с флешками': 'podarochnye-nabory-s-fleshkami',
        'Подарочные наборы для женщин': 's-podarochnye-nabory-dlya-jenshhin',
        'Подарочные наборы с аккумуляторами': 's-podarochnye-nabory-s-vneshnimi-akkumulyatorami',
        'Подарочные наборы для детей': 'podarochnye-nabory-dlya-detey',
        'Подарочные наборы с кружками': 'podarochnye-nabory-s-krujkami',
        'Подарочные наборы welcome pack': 'podarochnye-nabory-welcome-pack',
        'Подарочные наборы с термокружками': 's-podarochnye-nabory-s-termokrujkami',
        'Бизнес наборы': 'podarochnye-biznes-nabory',
        'Подарочные наборы с бутылками для воды': 'podarochnye-nabory-s-butylkami-dlya-vody',
        'Дорожные наборы для путешествий': 'dorojnye-nabory-dlya-puteshestviy',
        'Подарочные наборы для мужчин': 's-podarochnye-nabory-dlya-mujchin',

        # Подкатегории коллекций с принтами
        'Оригинальные ежедневники с принтом': 'ejednevniki-originalnye',
        'Плащи-дождевики с принтом': 'dozhdeviki-s-printom',
        'Кружки с принтом': 'krujki-s-printom',
        'Бейсболки, панамы и шапки с принтом': 'beysbolki-i-panamy-s-printom',
        'Футболки с принтом': 'odejda-futbolki-s-printom',
        'Сумки и рюкзаки с принтом': 'sumki-s-printom',
        'Шарфы с принтом': 'sharfy-s-printom',
        'Джемперы с принтом': 'jumpery-s-printom',
        'Новогодний мерч': 'novogodniy-merch',
        'Толстовки с принтом': 'tolstovki-s-printom',
        'Детские футболки с принтом': 'detskie-futbolki-s-printom',
        'Худи с принтом': 'hudi-s-printom',
        'Зонты с принтом': 'zonty-s-printom',
        'Оригинальные подарки с принтом': 'originalnye-podarki-s-printom',

        # Подкатегории съедобных подарков
        'Наборы специй с логотипом': 'nabory-spetsii-s-logotipom',
        'Подарочные наборы с медом': 'podarochnye-nabory-s-medom',
        'Подарочные наборы с вареньем': 'podarochnye-nabory-s-varenem',
        'Наборы шоколада с логотипом': 'shokoladnye-nabory-s-logotipom',
        'Снеки, орехи, сухофрукты': 'orekhi-iagody-sukhofrukty-s-logotipom',
        'Подарочные наборы с кофе': 'podarochnye-nabory-s-kofe',
        'Подарочные наборы с чаем': 'podarochnye-nabory-s-chaem',
        'Подарочные продуктовые наборы': 's-podarochnye-produktovye-nabory',
        'Конфеты, сладости, печенье': 'ledentsy-s-logotipom',

        # Подкатегории спортивных товаров
        'Спортивный инвентарь с логотипом': 'sportivnyi-inventar',
        'Массажеры': 'massajery',
        'Самокаты и гироскутеры': 'samokaty-i-giroskutery',
        'Спортивные шейкеры с логотипом': 'sportivnye-sheykery',
        'Фитнес подарки с логотипом': 'tovary-dlya-fitnesa',
        'Спортивные аксессуары с логотипом': 'sportivnye-aksessuary',
        'Велосипедные аксессуары': 'velosipednye-aksessuary',
        'Спортивные полотенца с логотипом': 'sportivnye-polotenca',
        'Мячи с логотипом': 'myachi-s-logotipom',

        # Подкатегории брендирования
        'Ремувки и пуллеры': 'remuvki-i-pullery',
        'Фурнитура': 'furnitura',
        'Шевроны и стикеры': 'shevrony-nashivki',
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
                'slug': slug,
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