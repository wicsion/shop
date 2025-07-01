# management/commands/smart_link_products_to_categories.py
from django.core.management.base import BaseCommand
from django.db.models import Q
from main.models import Category, XMLProduct
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Smart linking products to categories based on keywords and rules'

    def handle(self, *args, **options):
        # Полный набор правил для всех категорий и подкатегорий
        category_rules = {
            # Основные категории и их подкатегории
            'odezhda': {
                'keywords': ['футболка', 'толстовка', 'рубашка', 'брюки', 'шорты', 'куртка', 'ветровка',
                             'свитшот', 'худи', 'жилет', 'джемпер', 'кофта', 'платье', 'юбка', 'лонгслив',
                             'бейсболка', 'панама', 'кепка', 'футболки', 'толстовки', 'рубашки', 'брюки',
                             'шорты', 'куртки', 'ветровки', 'свитшоты', 'худи', 'жилеты', 'джемпера',
                             'кофты', 'платья', 'юбки', 'лонгсливы', 'бейсболки', 'панамы', 'кепки',
                             'фартук', 'фартуки', 'спортивная одежда', 'детская одежда', 'аксессуары для одежды',
                             'вязальное производство', 'одежда', 'костюм', 'костюмы', 'бомбер', 'джоггеры'],
                'exclude': ['кукла', 'игрушка', 'чехол', 'наволочка', 'подушка', 'белье', 'носки'],
                'subcategories': {
                    'futbolki': ['футболка', 'футболки', 'майка', 'майки', 't-shirt', 'tee'],
                    'kepki-i-beysbolki': ['кепка', 'кепки', 'бейсболка', 'бейсболки', 'cap', 'baseball'],
                    'panamy': ['панама', 'панамы', 'шляпа', 'шляпы', 'солнцезащитная', 'panama'],
                    'rubashki-polo': ['рубашка', 'рубашки', 'поло', 'polo', 'рубашка поло'],
                    'longslivy': ['лонгслив', 'лонгсливы', 'длинный рукав', 'longsleeve'],
                    'futbolki-dlya-promo': ['промо', 'рекламная', 'акционная', 'брендированная', 'promo'],
                    'vetrovki': ['ветровка', 'ветровки', 'ветрозащитная', 'windbreaker'],
                    'tolstovki': ['толстовка', 'толстовки', 'sweatshirt', 'худи', 'hoodie'],
                    'svitshoty': ['свитшот', 'свитшоты', 'sweatshirt'],
                    'kurtki': ['куртка', 'куртки', 'jacket', 'пальто', 'coat'],
                    'kofty-iz-flisa': ['кофта', 'кофты', 'флис', 'fleece'],
                    'sharfy': ['шарф', 'шарфы', 'scarf'],
                    'shapki': ['шапка', 'шапки', 'шапочка', 'beanie', 'hat'],
                    'perchatki-i-varezhki': ['перчатки', 'варежки', 'рукавицы', 'gloves', 'mittens'],
                    'vyazanye-komplekty': ['вязаный', 'комплект', 'набор', 'комплект вязаный'],
                    'dzhempery': ['джемпер', 'джемпера', 'свитер', 'sweater', 'pullover'],
                    'zilety': ['жилет', 'жилеты', 'безрукавка', 'vest'],
                    'ofisnye-rubashki': ['офисная', 'деловая', 'рубашка', 'office', 'business'],
                    'fartuki': ['фартук', 'фартуки', 'apron'],
                    'sportivnaya-odezhda': ['спортивная', 'тренировочная', 'sport', 'training'],
                    'bryuki-i-shorty': ['брюки', 'шорты', 'штаны', 'pants', 'shorts'],
                    'detskaya-odezhda': ['детская', 'для детей', 'kids', 'children'],
                    'aksessuary-dlya-odezhdy': ['аксессуар', 'ремень', 'пояс', 'accessory'],
                    'svitshoty-i-hudi': ['свитшот', 'свитшоты', 'худи', 'hoodie', 'с капюшоном'],
                    'vyazalnoe-proizvodstvo': ['вязание', 'вязаный', 'handmade', 'ручная работа']
                }
            },
            'posuda': {
                'keywords': ['кружка', 'термос', 'бокал', 'чайник', 'ложка', 'вилка', 'нож', 'тарелка',
                             'сковорода', 'кастрюля', 'ковш', 'стакан', 'фужер', 'рюмка', 'чашка',
                             'термокружка', 'набор посуды', 'столовые приборы', 'сервиз', 'кофейник',
                             'заварочный', 'кувшин', 'графин', 'подставка', 'поднос', 'блюдо',
                             'ланчбокс', 'ланчбоксы', 'кухонные аксессуары', 'мельницы для специй',
                             'разделочные доски', 'барные аксессуары', 'фляжки', 'предметы сервировки',
                             'костер', 'костеры', 'заварочные чайники', 'посуда', 'kitchen', 'стопка', 'стопки',
                             'френч-пресс', 'менжница', 'ваза', 'пепельница', 'сливочник'],
                'material': ['стекло', 'керамика', 'нерж. сталь', 'нержавеющая сталь', 'фарфор',
                             'металл', 'дерево', 'бамбук', 'силикон', 'пластик'],
                'subcategories': {
                    'kruzhki': ['кружка', 'кружки', 'mug', 'чашка', 'cup'],
                    'termokruzhki': ['термокружка', 'термокружки', 'термочашка', 'thermo', 'keepcup'],
                    'butylki-dlya-vody': ['бутылка', 'бутылки', 'фляга', 'bottle', 'water'],
                    'chaynye-nabory': ['чайный', 'чайник', 'заварочный', 'tea', 'set'],
                    'kofeynye-nabory': ['кофейный', 'кофе', 'coffee', 'набор'],
                    'bokaly': ['бокал', 'бокалы', 'фужер', 'glass', 'wine'],
                    'stakany': ['стакан', 'стаканы', 'glass', 'стаканчик'],
                    'pivnye-bokaly': ['пивной', 'пиво', 'beer', 'pint'],
                    'termosy': ['термос', 'thermos', 'термокружка'],
                    'termosy-dlya-edy': ['термос для еды', 'ланчбокс', 'food', 'контейнер'],
                    'stakany-s-kryshkoy': ['стакан с крышкой', 'travel mug', 'крышка'],
                    'lanchboksy': ['ланчбокс', 'контейнер', 'lunchbox', 'еда'],
                    'kuhonnye-aksessuary': ['кухонный', 'аксессуар', 'kitchen', 'accessory'],
                    'melnicy-dlya-speciy': ['мельница', 'специи', 'spice', 'mill'],
                    'razdelochnye-doski': ['доска', 'разделочная', 'chopping', 'board'],
                    'barnye-aksessuary': ['барный', 'бар', 'bar', 'аксессуар'],
                    'flyazhki': ['фляга', 'фляжка', 'flask', 'металлическая'],
                    'predmety-servirovki': ['сервировка', 'приборы', 'serving', 'столовые'],
                    'kostery': ['костер', 'костеры', 'camping', 'походный'],
                    'zavarochnye-chayniki': ['заварочный', 'чайник', 'teapot', 'чайный']
                }
            },
            'ruchki': {
                'keywords': ['ручка', 'карандаш', 'маркер', 'авторучка', 'шариковая', 'гелевая',
                             'перьевая', 'стилус', 'капиллярная', 'линер', 'фломастер', 'текстовыделитель',
                             'письменные принадлежности', 'канцелярия', 'пишущий', 'письмо',
                             'эко ручки', 'металлические ручки', 'пластиковые ручки', 'футляры для ручек',
                             'планинг', 'ежедневник'],
                'exclude': ['дверная', 'ручка двери', 'рукоятка', 'держатель'],
                'subcategories': {
                    'karandashi': ['карандаш', 'карандаши', 'pencil', 'механический'],
                    'eko-ruchki': ['эко', 'экологич', 'деревян', 'bamboo', 'eco'],
                    'metallicheskie-ruchki': ['металлическ', 'metal', 'сталь', 'алюминий'],
                    'plastikovye-ruchki': ['пластик', 'plastic', 'акрил'],
                    'futlyary-dlya-ruchek': ['футляр', 'чехол', 'case', 'cover']
                }
            },
            'elektronika': {
                'keywords': ['наушники', 'power bank', 'флешка', 'гаджет', 'аккумулятор', 'колонка',
                             'зарядка', 'кабель', 'адаптер', 'smart watch', 'умные часы', 'powerbank',
                             'флеш-накопитель', 'usb', 'провод', 'зарядное', 'устройство', 'батарея',
                             'аккумуляторная', 'портативная', 'беспроводная', 'bluetooth', 'динамик',
                             'аудио', 'звук', 'гарнитура', 'увлажнитель', 'увлажнители', 'лампы',
                             'светильники', 'бытовая техника', 'умный дом', 'электроника', 'рулетка',
                             'термобутылка', 'кулер'],
                'priority': True,
                'subcategories': {
                    'akkumulyatory': ['аккумулятор', 'батарея', 'battery', 'power bank'],
                    'zaryadnye-ustroystva': ['зарядка', 'зарядное', 'charger', 'адаптер'],
                    'mobilnye-aksessuary': ['аксессуар', 'чехол', 'держатель', 'mobile'],
                    'kolonki-i-naushniki': ['наушники', 'колонка', 'headphones', 'speaker'],
                    'fleshki': ['флешка', 'usb', 'flash', 'накопитель'],
                    'uvlazhniteli': ['увлажнитель', 'humidifier', 'воздух'],
                    'lampy-i-svetilniki': ['лампа', 'светильник', 'lamp', 'light'],
                    'bytovaya-tehnika': ['техника', 'бытовая', 'appliance', 'прибор'],
                    'umnyy-dom': ['умный дом', 'smart home', 'iot', 'управление']
                }
            },
            'sumki': {
                'keywords': ['сумка', 'рюкзак', 'чемодан', 'портфель', 'кейс', 'косметичка', 'мешок', 'баул', 'клатч',
                             'тоут', 'саквояж', 'дипломат', 'несессер'],
                'exclude': ['карман', 'кошелек', 'рюкзак-кенгуру', 'детский рюкзак'],
                'subcategories': {
                    'poyasnye-sumki': ['поясная', 'на пояс', 'waist', 'belt', 'бананка'],
                    'ryukzaki': ['рюкзак', 'backpack', 'ранец', 'trekking', 'hiking'],
                    'sumki-dlya-pokupok': ['шопер', 'shopper', 'покупки', 'tote', 'холщовая'],
                    'sumki-dlya-noutbuka': ['ноутбук', 'laptop', 'компьютер', 'деловой', 'business'],
                    'sumki-dlya-dokumentov': ['документы', 'папка', 'documents', 'портфель', 'дипломат']
                }
            },
            'ezhednevniki-i-bloknoty': {
                'keywords': ['ежедневник', 'блокнот', 'записная книжка', 'нотбук', 'планировщик', 'органайзер',
                             'тетрадь', 'альбом'],
                'exclude': ['школьная', 'детская', 'раскраска'],
                'subcategories': {
                    'ezhednevniki': ['ежедневник', 'планировщик', 'organizer', 'diary'],
                    'bloknoty': ['блокнот', 'notebook', 'записная', 'заметки'],
                    'kalkulyator-ezhednevnika': ['калькулятор', 'calculator', 'счеты'],
                    'nabory-s-ezhednevnikami': ['набор', 'комплект', 'подарочный', 'set'],
                    'upakovka-dlya-ezhednevnikov': ['упаковка', 'коробка', 'футляр', 'box'],
                    'ezhednevniki-na-zakaz': ['на заказ', 'персонализир', 'custom', 'лого']
                }
            },
            'upakovka': {
                'keywords': ['упаковка', 'коробка', 'пакет', 'конверт', 'футляр', 'шкатулка', 'тубус', 'пенал', 'кейс'],
                'subcategories': {
                    'korobki': ['коробка', 'box', 'деревян', 'картон', 'подарочн'],
                    'pakety': ['пакет', 'пленка', 'пакетик', 'bag', 'sachet'],
                    'podarochnaya-upakovka': ['подарочн', 'gift', 'украшен', 'лента'],
                    'upakovka-na-zakaz': ['на заказ', 'лого', 'брендир', 'custom'],
                    'novogodnyaya-upakovka': ['новый год', 'новогодн', 'ёлка', 'xmas']
                }
            },
            'podarochnye-nabory': {
                'keywords': ['набор', 'комплект', 'подарочный', 'набор', 'коллекция', 'сет', 'комплект'],
                'subcategories': {
                    'biznes-nabory': ['бизнес', 'деловой', 'office', 'премиум'],
                    'nabory-iz-kozhi': ['кожа', 'leather', 'натуральн'],
                    'nabory-velkom-pak': ['welcome', 'приветствен', 'новым сотрудникам'],
                    'dorozhnye-nabory': ['дорожный', 'travel', 'путешеств'],
                    'nabory-s-termokruzhkami': ['термокружка', 'термос', 'thermo'],
                    'nabory-s-kruzhkami': ['кружка', 'mug', 'чашка'],
                    'nabory-s-butylkami-dlya-vody': ['бутылка', 'фляга', 'bottle'],
                    'nabory-s-akkumulyatorami': ['аккумулятор', 'power bank', 'зарядка'],
                    'nabory-s-fleshkami': ['флешка', 'usb', 'накопитель'],
                    'nabory-s-pledami': ['плед', 'одеяло', 'покрывало'],
                    'nabory-s-multitulami': ['мультитул', 'ножницы', 'инструмент'],
                    'vinnye-nabory': ['вино', 'бокал', 'wine', 'пробка'],
                    'nabory-dlya-syra': ['сыр', 'сырный', 'cheese', 'доска'],
                    'nabory-dlya-viski': ['виски', 'whisky', 'бокал', 'камни'],
                    'kuhonnye-nabory': ['кухонный', 'столовый', 'приборы'],
                    'sportivnye-nabory': ['спорт', 'тренировка', 'fitness'],
                    'nabory-dlya-vyrashchivaniya': ['растение', 'сад', 'garden', 'цветок'],
                    'nabory-dlya-muzhchin': ['мужской', 'для него', 'men', 'борода'],
                    'nabory-dlya-zhenshchin': ['женский', 'для нее', 'women', 'косметика'],
                    'nabory-dlya-detey': ['детский', 'игрушка', 'kids', 'ребенок'],
                    'novogodnie-nabory': ['новый год', 'ёлка', 'xmas', 'подарок'],
                    'nabory-s-ezhednevnikami': ['ежедневник', 'блокнот', 'планировщик'],
                    'nabory-ruchek': ['ручка', 'карандаш', 'письменные']
                }
            },
            'zonty': {
                'keywords': ['зонт', 'зонтик', 'umbrella', 'дождевик', 'трость', 'складной'],
                'subcategories': {
                    'zonty-trosti': ['трость', 'тростевой', 'stick', 'деревян'],
                    'skladnye-zonty': ['складной', 'compact', 'автомат'],
                    'malye-zonty': ['маленький', 'карманный', 'mini', 'складной'],
                    'detskie-zonty': ['детский', 'kids', 'маленький']
                }
            },
            'korporativnye-podarki': {
                'keywords': ['корпоратив', 'офис', 'бизнес', 'деловой', 'подарок', 'премия', 'награда', 'кубок',
                             'стела', 'медаль'],
                'subcategories': {
                    'nastolnye-aksessuary': ['настольный', 'holder', 'подставка', 'статуэтка'],
                    'koshelki': ['кошелек', 'визитница', 'cardholder', 'портмоне'],
                    'vizitnitsy': ['визитница', 'визитка', 'card', 'бизнес карта'],
                    'chehly-dlya-kart': ['чехол', 'карта', 'credit', 'card'],
                    'chehly-dlya-propuska': ['пропуск', 'badge', 'бейдж', 'удостоверение'],
                    'beydzhi-i-lenty': ['бейдж', 'лента', 'badge', 'holder'],
                    'dorozhnye-organajzery': ['органайзер', 'organizer', 'косметичка'],
                    'oblozhki-dlya-dokumentov': ['обложка', 'папка', 'folder', 'портфель'],
                    'papki-portfeli': ['папка', 'портфель', 'дипломат', 'briefcase'],
                    'nagrady': ['награда', 'кубок', 'статуэтка', 'грамота'],
                    'knigi': ['книга', 'альбом', 'подарочное издание'],
                    'flikery': ['фликер', 'светоотражатель', 'reflector'],
                    'antistressy': ['антистресс', 'игрушка', 'мяч', 'куб'],
                    'brelki': ['брелок', 'keychain', 'подвеска'],
                    'kantstovary': ['канцтовары', 'ручка', 'карандаш', 'ластик'],
                    'zazhigalki': ['зажигалка', 'lighter', 'огонь', 'пламя']
                }
            },
            'sportivnaya-odezhda': {
                'keywords': ['спорт', 'тренировка', 'футболка', 'шорты', 'костюм', 'ветровка', 'толстовка'],
                'subcategories': {
                    'sportivnye-kostyumy': ['костюм', 'комплект', 'suit', 'тренировочный'],
                    'sportivnye-futbolki': ['футболка', 'майка', 't-shirt', 'тренировка'],
                    'shorty-dlya-trenirovok': ['шорты', 'shorts', 'тренировка'],
                    'legginsy': ['легинсы', 'leggings', 'штаны', 'лосины'],
                    'vetrovki-sportivnye': ['ветровка', 'windbreaker', 'дождевик'],
                    'termobele': ['термобелье', 'underwear', 'нижнее белье'],
                    'kompressionnaya-odezhda': ['компрессия', 'compression', 'утягивающий']
                }
            },
            'gotovye-resheniya': {
                'keywords': ['набор', 'готовый', 'решение', 'комплект', 'welcome pack', 'корпоративный'],
                'subcategories': {
                    'startovyj-nabor': ['стартовый', 'базовый', 'начальный', 'simple'],
                    'uluchshennyj-nabor': ['улучшенный', 'расширенный', 'extended'],
                    'premium-dlya-kompanij': ['премиум', 'premium', 'люкс', 'elite']
                }
            },
            'tovary-dlya-puteshestviy': {
                'keywords': ['путешествие', 'дорожный', 'travel', 'чемодан', 'косметичка', 'органайзер'],
                'subcategories': {
                    'dorozhnye-podushki': ['подушка', 'шейная', 'travel pillow', 'надувная'],
                    'dorozhnye-nabory': ['набор', 'комплект', 'travel kit', 'косметичка'],
                    'organajzery': ['органайзер', 'organizer', 'косметичка', 'чехол'],
                    'chehly-dlya-dokumentov': ['документы', 'паспорт', 'passport', 'обложка'],
                    'dorozhnye-flyagi': ['фляга', 'бутылка', 'bottle', 'термос']
                }
            },
            'nabory-dlya-piknika': {
                'keywords': ['пикник', 'набор', 'плед', 'корзина', 'коврик', 'camping', 'шашлык'],
                'subcategories': {
                    'bazovye-nabory': ['базовый', 'simple', 'начальный', 'стандарт'],
                    'premium-nabory': ['премиум', 'luxury', 'расширенный'],
                    'korporativnye-nabory': ['корпоратив', 'business', 'офисный'],
                    'nabory-s-posudoj': ['посуда', 'столовые приборы', 'plate', 'cup'],
                    'nabory-s-pledom': ['плед', 'коврик', 'blanket', 'подстилка'],
                    'nabory-dlya-kempinga': ['кемпинг', 'camping', 'поход', 'шатер'],
                    'nabory-dlya-barbekyu': ['барбекю', 'шашлык', 'grill', 'мангал']
                }
            },
            'veshchi-dlya-pohoda': {
                'keywords': ['поход', 'кемпинг', 'camping', 'палатка', 'спальник', 'костер', 'фонарь'],
                'subcategories': {
                    'multituly': ['мультитул', 'нож', 'инструмент', 'multi-tool'],
                    'fonariki': ['фонарь', 'фонарик', 'torch', 'light'],
                    'termosy': ['термос', 'thermos', 'термокружка'],
                    'pokhodnye-nozhi': ['нож', 'лезвие', 'blade', 'knife'],
                    'compassy': ['компас', 'compass', 'навигация'],
                    'pokhodnye-gorelki': ['горелка', 'плитка', 'stove', 'burner'],
                    'spalnye-meshki': ['спальник', 'sleeping bag', 'коврик']
                }
            },
            'plyazhnyy-otdyh': {
                'keywords': ['пляж', 'beach', 'отдых', 'полотенце', 'зонт', 'коврик', 'купальник'],
                'subcategories': {
                    'plyazhnye-polotentsa': ['полотенце', 'towel', 'махровое', 'пляжное'],
                    'sumki-holodilniki': ['холодильник', 'cooler', 'термосумка'],
                    'nabory-dlya-otdyha': ['набор', 'комплект', 'set', 'пляжный'],
                    'plyazhnye-zonty': ['зонт', 'umbrella', 'пляжный', 'beach'],
                    'kovriki-dlya-plyazha': ['коврик', 'mat', 'подстилка', 'пляжный'],
                    'chehly-dlya-ochkov': ['очки', 'чехол', 'glasses', 'case']
                }
            },
            'vkusnye-podarki': {
                'keywords': ['вкусный', 'съедобный', 'чай', 'кофе', 'мед', 'шоколад', 'набор', 'джем', 'варенье',
                             'конфитюр', 'печенье', 'орехи', 'смесь', 'соус', 'приправа', 'копченая паприка',
                             'чай улун'],
                'subcategories': {
                    'produktovye-nabory': ['продуктовый', 'набор', 'gourmet', 'еда'],
                    'med': ['мед', 'honey', 'пчелиный', 'липовый'],
                    'varene': ['варенье', 'джем', 'jam', 'конфитюр'],
                    'chaj': ['чай', 'tea', 'зеленый', 'черный'],
                    'kofe': ['кофе', 'coffee', 'зерна', 'молотый'],
                    'shokolad': ['шоколад', 'chocolate', 'конфеты', 'candy'],
                    'konfety-i-sladosti': ['конфеты', 'сладости', 'candy', 'sweets'],
                    'sneki': ['снеки', 'орехи', 'nuts', 'сухофрукты'],
                    'specii': ['специи', 'spices', 'приправы', 'травы']
                }
            },
            'dlya-bani-i-sauny': {
                'keywords': ['баня', 'сауна', 'рукавица', 'веник', 'шапка', 'коврик', 'ведро', 'термометр', 'ковш',
                             'аромамасла'],
                'subcategories': {
                    'rukovitsy-dlya-bani': ['рукавица', 'банная', 'варежка', 'mitt'],
                    'veniki': ['веник', 'банный', 'дубовый', 'березовый'],
                    'shapki-dlya-bani': ['шапка', 'банная', 'войлочная', 'felt'],
                    'kovriki-dlya-bani': ['коврик', 'банный', 'прорезиненный', 'mat'],
                    'aksessuary-dlya-bani': ['аксессуар', 'термометр', 'гигрометр', 'часы']
                }
            },
            'dlya-doma': {
                'keywords': ['дом', 'интерьер', 'ковер', 'плед', 'свеча', 'подсвечник', 'зеркало', 'фоторамка', 'ваза',
                             'шторы', 'подушка', 'коврик'],
                'subcategories': {
                    'tekstil-dlya-doma': ['текстиль', 'плед', 'покрывало', 'скатерть'],
                    'svechi-i-podsvechniki': ['свеча', 'подсвечник', 'ароматическая', 'candle'],
                    'zerkala': ['зеркало', 'настенное', 'карманное', 'mirror'],
                    'fotoramki': ['рамка', 'фоторамка', 'фотография', 'frame'],
                    'vazy': ['ваза', 'цветочный горшок', 'керамическая', 'vase']
                }
            },
            'detskie-tovary': {
                'keywords': ['детский', 'игрушка', 'ребенок', 'погремушка', 'конструктор', 'кукла', 'мягкая игрушка',
                             'головоломка', 'развивающая игра', 'пазл'],
                'subcategories': {
                    'igrushki': ['игрушка', 'мягкая', 'плюшевая', 'toy'],
                    'golovolomki': ['головоломка', 'пазл', 'кубик', 'puzzle'],
                    'razvivayushchie-igry': ['развивающая', 'обучающая', 'educational'],
                    'detskaya-odezhda': ['одежда', 'детская', 'для малышей', 'kids']
                }
            }
        }

        # Сначала обрабатываем приоритетные категории
        priority_categories = [slug for slug, rules in category_rules.items()
                               if rules.get('priority', False)]

        existing_priority_categories = []

        for slug in priority_categories:
            try:
                category = Category.objects.get(slug=slug)
                existing_priority_categories.append(slug)
                rules = category_rules[slug]

                # Основной запрос для категории
                query = Q()
                for keyword in rules['keywords']:
                    query |= Q(name__icontains=keyword) | Q(description__icontains=keyword)

                if 'exclude' in rules:
                    for excl in rules['exclude']:
                        query &= ~Q(name__icontains=excl) & ~Q(description__icontains=excl)

                # Обрабатываем подкатегории
                if 'subcategories' in rules:
                    for sub_slug, sub_keywords in rules['subcategories'].items():
                        try:
                            subcategory = Category.objects.get(slug=sub_slug)
                            sub_query = Q()
                            for keyword in sub_keywords:
                                sub_query |= Q(name__icontains=keyword) | Q(description__icontains=keyword)

                            sub_products = XMLProduct.objects.filter(query & sub_query).distinct()
                            subcategory.xml_products.add(*sub_products)
                            self.stdout.write(self.style.SUCCESS(
                                f"Подкатегория '{subcategory.name}': добавлено {sub_products.count()} товаров"
                            ))

                        except Category.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f"Подкатегория с slug '{sub_slug}' не найдена. Пропускаем."
                            ))
                            continue

                # Добавляем товары в основную категорию
                products = XMLProduct.objects.filter(query).distinct()
                category.xml_products.add(*products)
                self.stdout.write(self.style.SUCCESS(
                    f"Приоритетная категория '{category.name}': добавлено {products.count()} товаров"
                ))

            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Категория с slug '{slug}' не найдена в базе данных. Пропускаем."
                ))
                continue

        # Затем обрабатываем остальные категории
        for category in Category.objects.all():
            if category.slug in existing_priority_categories:
                continue  # Уже обработали

            rules = category_rules.get(category.slug, {
                'keywords': [category.name.split()[0].lower()],
                'exclude': []
            })

            query = Q()
            for keyword in rules['keywords']:
                query |= Q(name__icontains=keyword) | Q(description__icontains=keyword)

            if 'exclude' in rules:
                for excl in rules['exclude']:
                    query &= ~Q(name__icontains=excl) & ~Q(description__icontains=excl)

            if existing_priority_categories:
                query &= ~Q(categories__slug__in=existing_priority_categories)

            # Обрабатываем подкатегории
            if 'subcategories' in rules:
                for sub_slug, sub_keywords in rules['subcategories'].items():
                    try:
                        subcategory = Category.objects.get(slug=sub_slug)
                        sub_query = Q()
                        for keyword in sub_keywords:
                            sub_query |= Q(name__icontains=keyword) | Q(description__icontains=keyword)

                        sub_products = XMLProduct.objects.filter(query & sub_query).distinct()
                        subcategory.xml_products.add(*sub_products)
                        self.stdout.write(self.style.SUCCESS(
                            f"Подкатегория '{subcategory.name}': добавлено {sub_products.count()} товаров"
                        ))

                    except Category.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Подкатегория с slug '{sub_slug}' не найдена. Пропускаем."
                        ))
                        continue

            # Добавляем товары в основную категорию
            products = XMLProduct.objects.filter(query).distinct()
            category.xml_products.add(*products)
            self.stdout.write(self.style.SUCCESS(
                f"Категория '{category.name}': добавлено {products.count()} товаров"
            ))

        # Проверка товаров без категорий
        no_category_products = XMLProduct.objects.filter(categories__isnull=True)
        if no_category_products.exists():
            self.stdout.write(self.style.WARNING(
                f"\nОсталось товаров без категорий: {no_category_products.count()}"
            ))
            self.stdout.write("Примеры:")
            for p in no_category_products[:5]:
                self.stdout.write(f"- {p.name} (ID: {p.id})")
            self.stdout.write("\nРекомендации:")
            self.stdout.write("1. Проверьте ключевые слова для категорий")
            self.stdout.write("2. Добавьте новые категории для оставшихся товаров")
            self.stdout.write("3. Расширьте правила для существующих категорий")