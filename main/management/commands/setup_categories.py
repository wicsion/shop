from django.core.management.base import BaseCommand
from main.models import Category
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Создает полную структуру категорий с xml_id'

    def handle(self, *args, **options):
        # Очистка старых категорий
        Category.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Все существующие категории удалены'))

        # Полная структура категорий с xml_id
        # Полная структура категорий с xml_id
        CATEGORIES = [
            # Корневая категория
            {
                'name': 'Каталог',
                'icon': '',
                'xml_id': '1',
                'slug': 'catalog',
                'children': []
            },

            # Основные категории
            {
                'name': 'Корпоративная одежда с логотипом',
                'icon': 'fas fa-tshirt',
                'xml_id': '1104129',
                'slug': 'odezhda',
                'children': [
                    {'name': 'Футболки с логотипом', 'xml_id': '1104128', 'slug': 'futbolki'},
                    {'name': 'Брюки и шорты с логотипом', 'xml_id': '1112561', 'slug': 'bryuki-i-shorty'},
                    {'name': 'Ветровки', 'xml_id': '1105702', 'slug': 'vetrovki'},
                    {'name': 'Промо футболки', 'xml_id': '1105693', 'slug': 'promo-futbolki'},
                    {'name': 'Спортивная одежда', 'xml_id': '1106755', 'slug': 'sportivnaya-odezhda'},

                    {'name': 'Вязаные комплекты', 'xml_id': '1108055', 'slug': 'vyazanye-komplekty'},
                    {'name': 'Флисовые куртки и кофты', 'xml_id': '1106932', 'slug': 'flisovye-kurtki'},
                    {'name': 'Детская одежда', 'xml_id': '1106007', 'slug': 'detskaya-odezhda'},
                    {'name': 'Фартуки с логотипом', 'xml_id': '1108599', 'slug': 'fartuki'},
                    {'name': 'Футболки с длинным рукавом', 'xml_id': '1109179', 'slug': 'longslivy'},
                    {'name': 'Футболки поло', 'xml_id': '1105688', 'slug': 'futbolki-polo'},
                    {'name': 'Шарфы', 'xml_id': '1105700', 'slug': 'sharfy'},
                    {'name': 'Джемперы и кардиганы', 'xml_id': '1107096', 'slug': 'dzhempery'},
                    {'name': 'Дождевики', 'xml_id': '1110445', 'slug': 'dozhdeviki'},


                    {'name': 'Толстовки с логотипом', 'xml_id': '1105701', 'slug': 'tolstovki'},
                    {'name': 'Свитшоты под нанесение логотипа', 'xml_id': '1111832', 'slug': 'svitshoty'},
                    {'name': 'Аксессуары', 'xml_id': '1105853', 'slug': 'aksessuary'},
                    {'name': 'Трикотажные шапки', 'xml_id': '1106914', 'slug': 'trikotazhnye-shapki'},
                    {'name': 'Перчатки и варежки с логотипом', 'xml_id': '1111983', 'slug': 'perchatki'},

                    {'name': 'Куртки', 'xml_id': '1105846', 'slug': 'kurtki'},
                    {'name': 'Худи под нанесение логотипа', 'xml_id': '1111833', 'slug': 'hudi'},
                    {'name': 'Кепки и бейсболки', 'xml_id': '1115055', 'slug': 'kepki-i-beysbolki'},
                    {'name': 'Панамы', 'xml_id': '1115056', 'slug': 'panamy'},
                    {'name': 'Рубашки поло', 'xml_id': '1115057', 'slug': 'rubashki-polo'},

                    {'name': 'Свитшоты', 'xml_id': '1115059', 'slug': 'svitshoty'},

                    {'name': 'Кофты из флиса', 'xml_id': '1115061', 'slug': 'kofty-iz-flisa'},

                    {'name': 'Шапки', 'xml_id': '1115063', 'slug': 'shapki'},
                    {'name': 'Перчатки и варежки', 'xml_id': '1115064', 'slug': 'perchatki-i-varezhki'},

                    {'name': 'Джемперы', 'xml_id': '1115066', 'slug': 'dzhempery'},
                    {'name': 'Жилеты', 'xml_id': '1115067', 'slug': 'zilety'},
                    {'name': 'Офисные рубашки', 'xml_id': '1115068', 'slug': 'ofisnye-rubashki'},
                    {'name': 'Аксессуары для одежды', 'xml_id': '1115069', 'slug': 'aksessuary-dlya-odezhdy'},
                    {'name': 'Вязальное производство', 'xml_id': '1115070', 'slug': 'vyazalnoe-proizvodstvo'},

                ]
            },
            {
                'name': 'Свитшоты и худи',
                'icon': 'fas fa-tshirt',
                'xml_id': '1115001',
                'slug': 'svitshoty-i-hudi',
                'children': [
                    {'name': 'Свитшоты с принтом', 'xml_id': '1115002', 'slug': 'svitshoty-s-printom'},
                    {'name': 'Худи с капюшоном', 'xml_id': '1115003', 'slug': 'hudi-s-kapyushonom'},
                    {'name': 'Спортивные худи', 'xml_id': '1115004', 'slug': 'sportivnye-hudi'},
                    {'name': 'Зимние худи', 'xml_id': '1115005', 'slug': 'zimnie-hudi'},
                    {'name': 'Оверсайз худи', 'xml_id': '1115006', 'slug': 'oversayz-hudi'},
                    {'name': 'Детские худи', 'xml_id': '1115007', 'slug': 'detskie-hudi'},
                ]
            },
            {
                'name': 'Вещи для похода',
                'icon': 'fas fa-hiking',
                'xml_id': '1115012',
                'slug': 'veshchi-dlya-pohoda',
                'children': [
                    {'name': 'Мультитулы', 'xml_id': '1115146', 'slug': 'multituly'},
                    {'name': 'Фонарики', 'xml_id': '1115147', 'slug': 'fonariki'},
                    {'name': 'Термосы', 'xml_id': '1115148', 'slug': 'termosy'},
                    {'name': 'Походные ножи', 'xml_id': '1115149', 'slug': 'pokhodnye-nozhi'},
                    {'name': 'Компасы', 'xml_id': '1115150', 'slug': 'compassy'},
                    {'name': 'Походные горелки', 'xml_id': '1115151', 'slug': 'pokhodnye-gorelki'},
                    {'name': 'Спальные мешки', 'xml_id': '1115152', 'slug': 'spalnye-meshki'},
                    # Остальные...
                ]
            },
            {
                'name': 'Готовые решения',
                'icon': 'fas fa-hands-helping',
                'xml_id': '1115008',
                'slug': 'gotovye-resheniya',
                'children': [
                    {'name': 'Стартовый набор', 'xml_id': '1115009', 'slug': 'startovyj-nabor'},
                    {'name': 'Улучшенный набор', 'xml_id': '1115010', 'slug': 'uluchshennyj-nabor'},
                    {'name': 'Премиум для компаний', 'xml_id': '1115011', 'slug': 'premium-dlya-kompanij'},
                ]
            },

            {
                'name': 'Вкусные подарки',
                'icon': 'fas fa-gift',
                'xml_id': '1115020',
                'slug': 'vkusnye-podarki',
                'children': [
                    {'name': 'Продуктовые наборы', 'xml_id': '1115021', 'slug': 'produktovye-nabory'},
                    {'name': 'Мед', 'xml_id': '1115022', 'slug': 'med'},
                    {'name': 'Варенье', 'xml_id': '1115023', 'slug': 'varene'},
                    {'name': 'Чай', 'xml_id': '1115024', 'slug': 'chaj'},
                    {'name': 'Кофе', 'xml_id': '1115025', 'slug': 'kofe'},
                    {'name': 'Шоколад', 'xml_id': '1115026', 'slug': 'shokolad'},
                    {'name': 'Конфеты и сладости', 'xml_id': '1115027', 'slug': 'konfety-i-sladosti'},
                    {'name': 'Снеки', 'xml_id': '1115028', 'slug': 'sneki'},
                    {'name': 'Специи', 'xml_id': '1115029', 'slug': 'specii'},
                ]
            },
            {
                'name': 'Спортивные товары с логотипом',
                'icon': 'fas fa-running',
                'xml_id': '1115030',
                'slug': 'sportivnye-tovary',
                'children': [
                    {'name': 'Спортивный инвентарь', 'xml_id': '1115031', 'slug': 'sportivnyj-inventar'},
                    {'name': 'Массажеры', 'xml_id': '1115032', 'slug': 'massazhery'},
                    {'name': 'Самокаты и гироскутеры', 'xml_id': '1115033', 'slug': 'samokaty-i-giroskutery'},
                    {'name': 'Спортивные шейкеры', 'xml_id': '1115034', 'slug': 'sportivnye-shejkery'},
                    {'name': 'Фитнес подарки', 'xml_id': '1115035', 'slug': 'fitnes-podarki'},
                    {'name': 'Спортивные аксессуары', 'xml_id': '1115036', 'slug': 'sportivnye-aksessuary'},
                    {'name': 'Велосипедные аксессуары', 'xml_id': '1115037', 'slug': 'velosipednye-aksessuary'},
                    {'name': 'Спортивные полотенца', 'xml_id': '1115038', 'slug': 'sportivnye-polotenca'},
                    {'name': 'Мячи', 'xml_id': '1115039', 'slug': 'myachi'},
                ]
            },
            {
                'name': 'Элементы брендирования и кастомизации',
                'icon': 'fas fa-tags',
                'xml_id': '1115040',
                'slug': 'brendirovanie',
                'children': [
                    {'name': 'Ремувки и пуллеры', 'xml_id': '1115041', 'slug': 'remuvki-i-pullery'},
                    {'name': 'Фурнитура', 'xml_id': '1115042', 'slug': 'furnitura'},
                    {'name': 'Шевроны и стикеры', 'xml_id': '1115043', 'slug': 'shevrony-i-stikery'},
                    {'name': 'Лейблы и шильды', 'xml_id': '1115044', 'slug': 'lejbly-i-shildy'},
                    {'name': 'Ленты, стропы, шнуры', 'xml_id': '1115045', 'slug': 'lenty-stropy-shnury'},
                ]
            },
            {
                'name': 'Дом',
                'icon': 'fas fa-home',
                'xml_id': '1104130',
                'slug': 'dom',
                'children': [
                    {'name': 'Декоративные свечи и подсвечники', 'xml_id': '1108476', 'slug': 'svechi'},
                    {'name': 'Интерьерные подарки', 'xml_id': '1105712', 'slug': 'interernye-podarki'},
                    {'name': 'Игрушки', 'xml_id': '1105856', 'slug': 'igrushki'},
                    {'name': 'Полотенца с логотипом', 'xml_id': '1106959', 'slug': 'polotenca'},
                    {'name': 'Аксессуары и средства для ухода', 'xml_id': '1111189',
                     'slug': 'aksessuary-dlya-uhoda'},
                    {'name': 'Пледы', 'xml_id': '1106953', 'slug': 'pledy'},
                    {'name': 'Часы и метеостанции', 'xml_id': '1104143', 'slug': 'chasy'},
                    {'name': 'Домашний текстиль', 'xml_id': '1105866', 'slug': 'domashniy-tekstil'},
                ]
            },
            {
                'name': 'Отдых',
                'icon': 'fas fa-umbrella-beach',
                'xml_id': '1104131',
                'slug': 'otdyh',
                'children': [
                    {'name': 'Подушки под шею', 'xml_id': '1106904', 'slug': 'podushki-pod-sheyu'},
                    {'name': 'Складные ножи с логотипом', 'xml_id': '1112317', 'slug': 'skladnye-nozhi'},
                    {'name': 'Игры и головоломки', 'xml_id': '1105721', 'slug': 'igry-i-golovolomki'},
                    {'name': 'Оптические приборы', 'xml_id': '1111862', 'slug': 'opticheskie-pribory'},
                    {'name': 'Товары для путешествий', 'xml_id': '1105724', 'slug': 'tovary-dlya-puteshestviy'},
                    {'name': 'Светодиодные фонарики', 'xml_id': '1106824', 'slug': 'fonariki'},
                    {'name': 'Подарки для дачи', 'xml_id': '1108937', 'slug': 'podarki-dlya-dachi'},
                    {'name': 'Инструменты', 'xml_id': '1105716', 'slug': 'instrumenty'},
                    {'name': 'Автомобильные аксессуары', 'xml_id': '1105718', 'slug': 'avtomobilnye-aksessuary'},
                    {'name': 'Туристические принадлежности', 'xml_id': '1106109',
                     'slug': 'turisticheskie-prinadlezhnosti'},
                    {'name': 'Мультитулы с логотипом', 'xml_id': '1105722', 'slug': 'multituly'},
                    {'name': 'Пляжный отдых', 'xml_id': '1105850', 'slug': 'plyazhnyy-otdyh'},
                    {'name': 'Банные принадлежности', 'xml_id': '1108978', 'slug': 'bannye-prinadlezhnosti'},
                    {'name': 'Наборы для пикника и барбекю с логотипом', 'xml_id': '1105723',
                     'slug': 'nabory-dlya-piknika'},
                ]
            },
            {
                'name': 'Посуда',
                'icon': 'fas fa-mug-hot',
                'xml_id': '1104132',
                'slug': 'posuda',
                'children': [
                    {'name': 'Термокружки с логотипом', 'xml_id': '1106906', 'slug': 'termokruzhki'},
                    {'name': 'Пивные бокалы с логотипом', 'xml_id': '1109708', 'slug': 'pivnye-bokaly'},
                    {'name': 'Многоразовые стаканы с крышкой', 'xml_id': '1112033', 'slug': 'stakany-s-kryshkoy'},
                    {'name': 'Стаканы', 'xml_id': '1108474', 'slug': 'stakany'},
                    {'name': 'Термосы для еды с логотипом', 'xml_id': '1110074', 'slug': 'termosy-dlya-edy'},
                    {'name': 'Фляжки с логотипом', 'xml_id': '1114130', 'slug': 'flyazhki'},

                    {'name': 'Термосы с логотипом', 'xml_id': '1107498', 'slug': 'termosy'},
                    {'name': 'Барные аксессуары', 'xml_id': '1109691', 'slug': 'barnye-aksessuary'},
                    {'name': 'Разделочные доски', 'xml_id': '1110064', 'slug': 'razdelochnye-doski'},
                    {'name': 'Мельницы для специй', 'xml_id': '1111959', 'slug': 'melnitsy-dlya-speciy'},

                    {'name': 'Ланч-боксы', 'xml_id': '1107473', 'slug': 'lanch-boksy'},
                    {'name': 'Кухонные принадлежности', 'xml_id': '1105711', 'slug': 'kuhonnye-prinadlezhnosti'},

                    {'name': 'Кружки с логотипом', 'xml_id': '1105730', 'slug': 'kruzhki'},
                    {'name': 'Предметы сервировки', 'xml_id': '1108809', 'slug': 'predmety-servirovki'},
                    {'name': 'Бутылки для воды', 'xml_id': '1107466', 'slug': 'butylki-dlya-vody'},
                    {'name': 'Заварочные чайники', 'xml_id': '1108861', 'slug': 'zavarochnye-chayniki'},
                    {'name': 'Костры с логотипом', 'xml_id': '1110066', 'slug': 'kostery'},

                    {'name': 'Чайные наборы', 'xml_id': '1115072', 'slug': 'chaynye-nabory'},
                    {'name': 'Кофейные наборы', 'xml_id': '1115073', 'slug': 'kofeynye-nabory'},
                    {'name': 'Бокалы', 'xml_id': '1115074', 'slug': 'bokaly'},



                    {'name': 'Кухонные аксессуары', 'xml_id': '1115078', 'slug': 'kuhonnye-aksessuary'},

                ]
            },
            {
                'name': 'Ручки с логотипом',
                'icon': 'fas fa-pen',
                'xml_id': '1104133',
                'slug': 'ruchki',
                'children': [
                    {'name': 'Бумажные и эко ручки с логотипом', 'xml_id': '1105733', 'slug': 'eko-ruchki'},
                    {'name': 'Наборы с ручками под логотип', 'xml_id': '1105734', 'slug': 'nabory-s-ruchkami'},
                    {'name': 'Карандаши с логотипом', 'xml_id': '1105732', 'slug': 'karandashi'},
                    {'name': 'Пластиковые ручки с логотипом', 'xml_id': '1105736', 'slug': 'plastikovye-ruchki'},
                    {'name': 'Футляры для ручек', 'xml_id': '1106909', 'slug': 'futlyary-dlya-ruchek'},
                    {'name': 'Металлические ручки с логотипом', 'xml_id': '1105735',
                     'slug': 'metallicheskie-ruchki'},

                    {'name': 'Эко-ручки', 'xml_id': '1115086', 'slug': 'eko-ruchki'},

                    # Остальные...
                ]
            },
            {
                'name': 'Сумки',
                'icon': 'fas fa-shopping-bag',
                'xml_id': '1104134',
                'slug': 'sumki',
                'children': [
                    {'name': 'Сумки через плечо с логотипом', 'xml_id': '1111867', 'slug': 'sumki-cherez-plecho'},
                    {'name': 'Сумки для документов', 'xml_id': '1105742', 'slug': 'sumki-dlya-dokumentov'},
                    {'name': 'Сумки для пикника', 'xml_id': '1106108', 'slug': 'sumki-dlya-piknika'},
                    {'name': 'Чемоданы', 'xml_id': '1107028', 'slug': 'chemodany'},
                    {'name': 'Несессеры и косметички', 'xml_id': '1105738', 'slug': 'nessesery'},
                    {'name': 'Шоперы с логотипом', 'xml_id': '1105739', 'slug': 'shopery'},
                    {'name': 'Дорожные сумки', 'xml_id': '1105740', 'slug': 'dorozhnye-sumki'},
                    {'name': 'Поясные сумки', 'xml_id': '1109473', 'slug': 'poyasnye-sumki'},
                    {'name': 'Сумки для ноутбука', 'xml_id': '1105744', 'slug': 'sumki-dlya-noutbuka'},
                    {'name': 'Рюкзаки', 'xml_id': '1105743', 'slug': 'ryukzaki'},

                ]
            },
            {
                'name': 'Зонты с логотипом',
                'icon': 'fas fa-umbrella',
                'xml_id': '1104136',
                'slug': 'zonty',
                'children': [
                    {'name': 'Складные зонты с логотипом', 'xml_id': '1105767', 'slug': 'skladnye-zonty'},
                    {'name': 'Зонты трости с логотипом', 'xml_id': '1105768', 'slug': 'zonty-trosti'},
                    {'name': 'Зонты-трости', 'xml_id': '1115094', 'slug': 'zonty-trosti'},
                    {'name': 'Малые зонты', 'xml_id': '1115095', 'slug': 'malye-zonty'},
                    {'name': 'Детские зонты', 'xml_id': '1115096', 'slug': 'detskie-zonty'},
                ]
            },
            {
                'name': 'Электроника и гаджеты',
                'icon': 'fas fa-mobile-alt',
                'xml_id': '1104139',
                'slug': 'elektronika',
                'children': [
                    {'name': 'Лампы и светильники', 'xml_id': '1109305', 'slug': 'lampy-i-svetilniki'},
                    {'name': 'Компьютерные и мобильные аксессуары', 'xml_id': '1105746',
                     'slug': 'kompyuternye-aksessuary'},
                    {'name': 'Гаджеты для умного дома с логотипом', 'xml_id': '1114013', 'slug': 'umnyy-dom'},
                    {'name': 'Бытовая техника', 'xml_id': '1108533', 'slug': 'bytovaya-tehnika'},
                    {'name': 'Внешние аккумуляторы power bank с логотипом', 'xml_id': '1106025',
                     'slug': 'power-bank'},

                    {'name': 'Увлажнители воздуха с логотипом', 'xml_id': '1112145', 'slug': 'uvlazhniteli'},
                    {'name': 'Портативные колонки и наушники', 'xml_id': '1106929', 'slug': 'kolonki-i-naushniki'},
                    {'name': 'Зарядные устройства для телефона с логотипом', 'xml_id': '1105855',
                     'slug': 'zaryadnye-ustroystva'},

                    {'name': 'Аккумуляторы', 'xml_id': '1115046', 'slug': 'akkumulyatory'},
                    {'name': 'Зарядные устройства', 'xml_id': '1115047', 'slug': 'zaryadnye-ustroystva'},
                    {'name': 'Мобильные аксессуары', 'xml_id': '1115048', 'slug': 'mobilnye-aksessuary'},
                    {'name': 'Колонки и наушники', 'xml_id': '1115049', 'slug': 'kolonki-i-naushniki'},
                    {'name': 'Флешки', 'xml_id': '1115050', 'slug': 'fleshki'},
                    {'name': 'Увлажнители воздуха', 'xml_id': '1115051', 'slug': 'uvlazhniteli'},


                    {'name': 'Умный дом', 'xml_id': '1115054', 'slug': 'umnyy-dom'},
                ]
            },
            {
                'name': 'Корпоративные подарки',
                'icon': 'fas fa-building',
                'xml_id': '1104141',
                'slug': 'korporativnye-podarki',
                'children': [
                    {'name': 'Светоотражатели', 'xml_id': '1105789', 'slug': 'svetootrazhateli'},
                    {'name': 'Дорожные органайзеры', 'xml_id': '1105809', 'slug': 'dorozhnye-organayzery'},
                    {'name': 'Визитницы', 'xml_id': '1105810', 'slug': 'vizitnicy'},
                    {'name': 'Настольные аксессуары', 'xml_id': '1105762', 'slug': 'nastolnye-aksessuary'},
                    {'name': 'Антистрессы', 'xml_id': '1105792', 'slug': 'antistressy'},
                    {'name': 'Бейджи и аксессуары', 'xml_id': '1111600', 'slug': 'beydzhi'},
                    {'name': 'Чехлы для пропуска', 'xml_id': '1112876', 'slug': 'chehly-dlya-propuska'},
                    {'name': 'Подарочные книги', 'xml_id': '1105817', 'slug': 'podarochnye-knigi'},
                    {'name': 'Чехлы для карт', 'xml_id': '1107985', 'slug': 'chehly-dlya-kart'},
                    {'name': 'Кошельки', 'xml_id': '1105811', 'slug': 'koshelki'},
                    {'name': 'Зажигалки', 'xml_id': '1105783', 'slug': 'zazhigalki'},
                    {'name': 'Канцелярские принадлежности', 'xml_id': '1111200',
                     'slug': 'kancelyarskie-prinadlezhnosti'},
                    {'name': 'Обложки для документов', 'xml_id': '1105808', 'slug': 'oblozhki-dlya-dokumentov'},

                    {'name': 'Папки, портфели', 'xml_id': '1105804', 'slug': 'papki-portfeli'},
                    {'name': 'Награды', 'xml_id': '1113924', 'slug': 'nagrady'},


                    {'name': 'Бейджи и ленты', 'xml_id': '1115102', 'slug': 'beydzhi-i-lenty'},

                    {'name': 'Книги', 'xml_id': '1115107', 'slug': 'knigi'},
                    {'name': 'Фликеры', 'xml_id': '1115108', 'slug': 'flikery'},
                    {'name': 'Антистрессы', 'xml_id': '1115109', 'slug': 'antistressy'},
                    {'name': 'Брелки', 'xml_id': '1115110', 'slug': 'brelki'},
                    {'name': 'Канцтовары', 'xml_id': '1115111', 'slug': 'kantstovary'},

                ]
            },
            {
                'name': 'Ежедневники и блокноты',
                'icon': 'fas fa-book',
                'xml_id': '1104144',
                'slug': 'ezhednevniki-i-bloknoty',
                'children': [
                    {'name': 'Упаковка для ежедневников', 'xml_id': '1105828',
                     'slug': 'upakovka-dlya-ezhednevnikov'},
                    {'name': 'Блокноты с логотипом', 'xml_id': '1106110', 'slug': 'bloknoty'},
                    {'name': 'Ежедневники с логотипом', 'xml_id': '1108650', 'slug': 'ezhednevniki'},
                    {'name': 'Наборы с ежедневниками', 'xml_id': '1107316', 'slug': 'nabory-s-ezhednevnikami'},
                    {'name': 'Ежедневники', 'xml_id': '1115113', 'slug': 'ezhednevniki'},
                    {'name': 'Блокноты', 'xml_id': '1115114', 'slug': 'bloknoty'},
                    {'name': 'Калькуляторы ежедневников', 'xml_id': '1115115', 'slug': 'kalkulyator-ezhednevnika'},
                    {'name': 'Упаковка для ежедневников', 'xml_id': '1115117', 'slug': 'upakovka-dlya-ezhednevnikov'},
                    {'name': 'Ежедневники на заказ', 'xml_id': '1115118', 'slug': 'ezhednevniki-na-zakaz'},

                    # Остальные...
                ]
            },
            {
                'name': 'Корпоративные подарки на Новый год',
                'icon': 'fas fa-gift',
                'xml_id': '1105845',
                'slug': 'novogodnie-podarki',
                'children': [
                    {'name': 'Новогодние елочные шары', 'xml_id': '1106045', 'slug': 'eloshnye-shary'},
                    {'name': 'Оригинальные календари', 'xml_id': '1107027', 'slug': 'kalendari'},
                    {'name': 'Новогодние подушки и пледы', 'xml_id': '1106895', 'slug': 'novogodnie-pledy'},
                    {'name': 'Новогодние наборы для творчества', 'xml_id': '1111744',
                     'slug': 'nabory-dlya-tvorchestva'},
                    {'name': 'Новогодние елки с логотипом', 'xml_id': '1106902', 'slug': 'elki'},
                    {'name': 'Новогодние свечи и подсвечники', 'xml_id': '1107355', 'slug': 'novogodnie-svechi'},
                    {'name': 'Подарки с символом 2025 года', 'xml_id': '1105857', 'slug': 'simvol-2025'},
                    {'name': 'Новогодние наборы', 'xml_id': '1107252', 'slug': 'novogodnie-nabory'},
                    {'name': 'Новогодняя вязаная одежда', 'xml_id': '1105877', 'slug': 'vyazanye-izdeliya'},
                    {'name': 'Новогодний стол', 'xml_id': '1105858', 'slug': 'novogodniy-stol'},
                    {'name': 'Новогодние гирлянды и светильники', 'xml_id': '1111733', 'slug': 'girlyandy'},
                    {'name': 'Новогодняя упаковка для подарков', 'xml_id': '1105997',
                     'slug': 'novogodnyaya-upakovka'},
                    {'name': 'Новогодние елочные игрушки', 'xml_id': '1105861', 'slug': 'eloshnye-igrushki'},
                    {'name': 'Украшения для офиса к новому году', 'xml_id': '1105862',
                     'slug': 'ukrasheniya-dlya-ofisa'},
                ]
            },
            {
                'name': 'Сувениры к праздникам',
                'icon': 'fas fa-gifts',
                'xml_id': '1105899',
                'slug': 'suveniry',
                'children': [
                    {'name': 'Подарки на День юриста 3 декабря', 'xml_id': '1105919', 'slug': 'den-yurista'},
                    {'name': 'Подарки на День России 12 июня', 'xml_id': '1106924', 'slug': 'den-rossii'},
                    {'name': 'Подарки детям', 'xml_id': '1105905', 'slug': 'podarki-detyam'},
                    {'name': 'Подарки на День медицинского работника', 'xml_id': '1105907', 'slug': 'den-medika'},
                    {'name': 'Подарки морякам', 'xml_id': '1106945', 'slug': 'podarki-moryakam'},
                    {'name': 'Подарки начальнику', 'xml_id': '1106882', 'slug': 'podarki-nachalniku'},
                    {'name': 'Подарки на День рождения компании', 'xml_id': '1106921',
                     'slug': 'den-rozhdeniya-kompanii'},
                    {'name': 'Подарки на День энергетика 22 декабря', 'xml_id': '1106920',
                     'slug': 'den-energetika'},
                    {'name': 'Подарки на День строителя', 'xml_id': '1105909', 'slug': 'den-stroitelya'},
                    {'name': 'Подарки на День учителя 5 октября', 'xml_id': '1106885', 'slug': 'den-uchitelya'},
                    {'name': 'Подарки на День геолога', 'xml_id': '1105900', 'slug': 'den-geologa'},
                    {'name': 'Подарки автомобилисту', 'xml_id': '1106884', 'slug': 'podarki-avtomobilistu'},
                    {'name': 'Подарки программистам', 'xml_id': '1110231', 'slug': 'podarki-programmistam'},
                    {'name': 'Подарки на День химика', 'xml_id': '1106944', 'slug': 'den-himika'},
                    {'name': 'Подарки на День железнодорожника', 'xml_id': '1106941',
                     'slug': 'den-zheleznodorozhnika'},
                    {'name': 'Подарки на День авиации', 'xml_id': '1105910', 'slug': 'den-aviatsii'},
                    {'name': 'Подарки на 14 февраля', 'xml_id': '1105892', 'slug': 'den-vlyublennyh'},
                    {'name': 'Подарки на День Победы 9 мая', 'xml_id': '1106943', 'slug': 'den-pobedy'},
                    {'name': 'Подарки на День электросвязи 17 мая', 'xml_id': '1105903',
                     'slug': 'den-elektrosvyazi'},
                    {'name': 'Подарки на День банковского работника 2 декабря', 'xml_id': '1105918',
                     'slug': 'den-bankira'},
                    {'name': 'Подарки ко Дню нефтяника', 'xml_id': '1105912', 'slug': 'den-neftyanika'},
                    {'name': 'Подарки на День знаний 1 сентября', 'xml_id': '1106946', 'slug': 'den-znaniy'},
                    {'name': 'Подарки системным администраторам', 'xml_id': '1110232', 'slug': 'den-sysadmina'},
                    {'name': 'Подарки ко Дню шахтера', 'xml_id': '1105911', 'slug': 'den-shahtyora'},
                    {'name': 'Подарки на День полиции (милиции) 10 ноября', 'xml_id': '1105916',
                     'slug': 'den-policii'},
                    {'name': 'Сувениры к 23 февраля', 'xml_id': '1105893', 'slug': '23-fevralya'},
                    {'name': 'Подарки на День металлурга', 'xml_id': '1106942', 'slug': 'den-metallurga'},
                    {'name': 'Сувениры к 8 марта', 'xml_id': '1105895', 'slug': '8-marta'},
                    {'name': 'Подарок коллеге', 'xml_id': '1106883', 'slug': 'podarki-kollegam'},
                ]
            },
            {
                'name': 'Упаковка',
                'icon': 'fas fa-box-open',
                'xml_id': '1105994',
                'slug': 'upakovka',
                'children': [
                    {'name': 'Производство полноцветной самосборной упаковки на заказ', 'xml_id': '1114622',
                     'slug': 'upakovka-na-zakaz'},
                    {'name': 'Подарочные коробки', 'xml_id': '1107407', 'slug': 'podarochnye-korobki'},
                    {'name': 'Подарочная упаковка', 'xml_id': '1105995', 'slug': 'podarochnaya-upakovka'},
                    {'name': 'Подарочные пакеты', 'xml_id': '1105998', 'slug': 'podarochnye-pakety'},
                    {'name': 'Коробки', 'xml_id': '1115119', 'slug': 'korobki'},
                    {'name': 'Пакеты', 'xml_id': '1115120', 'slug': 'pakety'},
                    {'name': 'Упаковка на заказ', 'xml_id': '1115121', 'slug': 'upakovka-na-zakaz'},
                    {'name': 'Новогодняя упаковка', 'xml_id': '1115122', 'slug': 'novogodnyaya-upakovka'},
                    {'name': 'Бизнес-наборы', 'xml_id': '1115123', 'slug': 'biznes-nabory'},
                    {'name': 'Наборы из кожи', 'xml_id': '1115124', 'slug': 'nabory-iz-kozhi'},
                    {'name': 'Наборы Welcome Pack', 'xml_id': '1115125', 'slug': 'nabory-velkom-pak'},
                    {'name': 'Дорожные наборы', 'xml_id': '1115126', 'slug': 'dorozhnye-nabory'},
                    {'name': 'Наборы с термокружками', 'xml_id': '1115127', 'slug': 'nabory-s-termokruzhkami'},
                    {'name': 'Наборы с кружками', 'xml_id': '1115128', 'slug': 'nabory-s-kruzhkami'},
                    {'name': 'Наборы с бутылками для воды', 'xml_id': '1115129',
                     'slug': 'nabory-s-butylkami-dlya-vody'},
                    {'name': 'Наборы с аккумуляторами', 'xml_id': '1115130', 'slug': 'nabory-s-akkumulyatorami'},
                    {'name': 'Наборы с флешками', 'xml_id': '1115131', 'slug': 'nabory-s-fleshkami'},
                    {'name': 'Наборы с пледами', 'xml_id': '1115132', 'slug': 'nabory-s-pledami'},
                    {'name': 'Наборы с мультитулами', 'xml_id': '1115133', 'slug': 'nabory-s-multitulami'},
                    {'name': 'Винные наборы', 'xml_id': '1115134', 'slug': 'vinnye-nabory'},
                    {'name': 'Наборы для сыра', 'xml_id': '1115135', 'slug': 'nabory-dlya-syra'},
                    {'name': 'Наборы для виски', 'xml_id': '1115136', 'slug': 'nabory-dlya-viski'},
                    {'name': 'Кухонные наборы', 'xml_id': '1115137', 'slug': 'kuhonnye-nabory'},
                    {'name': 'Спортивные наборы', 'xml_id': '1115138', 'slug': 'sportivnye-nabory'},
                    {'name': 'Наборы для выращивания', 'xml_id': '1115139', 'slug': 'nabory-dlya-vyrashchivaniya'},
                    {'name': 'Наборы для мужчин', 'xml_id': '1115140', 'slug': 'nabory-dlya-muzhchin'},
                    {'name': 'Наборы для женщин', 'xml_id': '1115141', 'slug': 'nabory-dlya-zhenshchin'},
                    {'name': 'Наборы для детей', 'xml_id': '1115142', 'slug': 'nabory-dlya-detey'},
                    {'name': 'Новогодние наборы', 'xml_id': '1115143', 'slug': 'novogodnie-nabory'},
                    {'name': 'Наборы с ежедневниками', 'xml_id': '1115144', 'slug': 'nabory-s-ezhednevnikami'},
                    {'name': 'Наборы ручек', 'xml_id': '1115145', 'slug': 'nabory-ruchek'}
                ]
            },
            {
                'name': 'Подарочные наборы',
                'icon': 'fas fa-gift',
                'xml_id': '1107210',
                'slug': 'podarochnye-nabory',
                'children': [
                    {'name': 'Подарочные наборы с мультитулами', 'xml_id': '1109606',
                     'slug': 'nabory-s-multitulami'},
                    {'name': 'Кухонные подарочные наборы', 'xml_id': '1112973', 'slug': 'kuhonnye-nabory'},
                    {'name': 'Спортивные наборы', 'xml_id': '1110525', 'slug': 'sportivnye-nabory'},
                    {'name': 'Подарочные наборы изделий из кожи с логотипом', 'xml_id': '1111508',
                     'slug': 'nabory-iz-kozhi'},
                    {'name': 'Винные наборы', 'xml_id': '1105715', 'slug': 'vinnye-nabory'},
                    {'name': 'Наборы стаканов и камни для виски', 'xml_id': '1107058', 'slug': 'nabory-dlya-viski'},
                    {'name': 'Наборы для выращивания растений', 'xml_id': '1109068',
                     'slug': 'nabory-dlya-vyrashchivaniya'},
                    {'name': 'Наборы для сыра', 'xml_id': '1108609', 'slug': 'nabory-dlya-syra'},
                    {'name': 'Подарочные наборы с пледами', 'xml_id': '1110027', 'slug': 'nabory-s-pledami'},
                    {'name': 'Подарочные наборы с флешками', 'xml_id': '1109501', 'slug': 'nabory-s-fleshkami'},
                    {'name': 'Подарочные наборы для женщин', 'xml_id': '1108072', 'slug': 'nabory-dlya-zhenshchin'},
                    {'name': 'Подарочные наборы с аккумуляторами', 'xml_id': '1108065',
                     'slug': 'nabory-s-akkumulyatorami'},
                    {'name': 'Подарочные наборы для детей', 'xml_id': '1112024', 'slug': 'nabory-dlya-detey'},
                    {'name': 'Подарочные наборы с кружками', 'xml_id': '1117541', 'slug': 'nabory-s-kruzhkami'},
                    {'name': 'Подарочные наборы welcome pack', 'xml_id': '1115013', 'slug': 'welcome-pack'},
                    {'name': 'Подарочные наборы с термокружками', 'xml_id': '1108069',
                     'slug': 'nabory-s-termokruzhkami'},
                    {'name': 'Бизнес наборы', 'xml_id': '1105807', 'slug': 'biznes-nabory'},
                    {'name': 'Подарочные наборы с бутылками для воды', 'xml_id': '1117567',
                     'slug': 'nabory-s-butylkami'},
                    {'name': 'Дорожные наборы для путешествий', 'xml_id': '1109500', 'slug': 'dorozhnye-nabory'},
                    {'name': 'Подарочные наборы для мужчин', 'xml_id': '1108073', 'slug': 'nabory-dlya-muzhchin'},
                ]
            },
            {
                'name': 'Коллекции с принтами',
                'icon': 'fas fa-paint-brush',
                'xml_id': '1109719',
                'slug': 'kollekcii',
                'children': [
                    {'name': 'Оригинальные ежедневники с принтом', 'xml_id': '1109724',
                     'slug': 'ezhednevniki-s-printom'},
                    {'name': 'Плащи-дождевики с принтом', 'xml_id': '1109755', 'slug': 'plashi-s-printom'},
                    {'name': 'Кружки с принтом', 'xml_id': '1109723', 'slug': 'kruzhki-s-printom'},
                    {'name': 'Бейсболки, панамы и шапки с принтом', 'xml_id': '1110649',
                     'slug': 'golovnye-ubory-s-printom'},
                    {'name': 'Футболки с принтом', 'xml_id': '1108956', 'slug': 'futbolki-s-printom'},
                    {'name': 'Сумки и рюкзаки с принтом', 'xml_id': '1109722', 'slug': 'sumki-s-printom'},
                    {'name': 'Шарфы с принтом', 'xml_id': '1111040', 'slug': 'sharfy-s-printom'},
                    {'name': 'Джемперы с принтом', 'xml_id': '1111041', 'slug': 'dzhempery-s-printom'},
                    {'name': 'Новогодний мерч', 'xml_id': '1111059', 'slug': 'novogodniy-merch'},
                    {'name': 'Толстовки с принтом', 'xml_id': '1109721', 'slug': 'tolstovki-s-printom'},
                    {'name': 'Детские футболки с принтом', 'xml_id': '1110647',
                     'slug': 'detskie-futbolki-s-printom'},
                    {'name': 'Худи с принтом', 'xml_id': '1111958', 'slug': 'hudi-s-printom'},
                    {'name': 'Зонты с принтом', 'xml_id': '1111179', 'slug': 'zonty-s-printom'},
                    {'name': 'Оригинальные подарки с принтом', 'xml_id': '1109728', 'slug': 'podarki-s-printom'},
                ]
            },
            {
                'name': 'Другое',
                'icon': 'fas fa-question-circle',
                'xml_id': '999999',
                'slug': 'drugoe',
                'children': []
            }
        ]

        # Создаем категории
        for category_data in CATEGORIES:
            parent = self.create_category(
                name=category_data['name'],
                slug=category_data['slug'],  # Гарантируем, что slug всегда передается
                icon=category_data['icon'],
                xml_id=category_data['xml_id'],
                parent=None
            )

            # Создаем подкатегории
            for child_data in category_data.get('children', []):
                self.create_category(
                    name=child_data['name'],
                    slug=child_data['slug'],  # Гарантируем, что slug всегда передается
                    xml_id=child_data['xml_id'],
                    parent=parent
                )

        self.stdout.write(self.style.SUCCESS('Полная структура категорий успешно создана!'))

    def create_category(self, name, slug, xml_id, parent=None, icon=''):
        """Создает категорию с проверкой уникальности slug"""
        # Убедимся, что slug не пустой
        if not slug:
            slug = slugify(name)

        original_slug = slug
        counter = 1

        # Проверяем уникальность slug только среди категорий с другим xml_id
        while Category.objects.filter(slug=slug).exclude(xml_id=xml_id).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1

        category, created = Category.objects.update_or_create(
            xml_id=xml_id,
            defaults={
                'name': name,
                'slug': slug,
                'icon': icon,
                'parent': parent,
                'is_featured': True,
                'order': 0
            }
        )

        action = "Создана" if created else "Обновлена"
        self.stdout.write(self.style.SUCCESS(
            f"{action} категория: {name} (slug: {slug}, xml_id: {xml_id})"
        ))
        return category