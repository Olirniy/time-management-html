import scrapy
import re
import json
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from collections import defaultdict
from tqdm import tqdm

class LustrofnewparsSpider(scrapy.Spider):
    name = "lustrofnewpars"
    allowed_domains = ["lustrof.ru"]
    start_urls = ["https://www.lustrof.ru/"]

    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',
        # Ускоренные параметры
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 3.0,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,

        # Настройки для обхода защиты
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
        },

        # Отключение куков
        'COOKIES_ENABLED': False,

        # Увеличенный срок кеширования
        'HTTPCACHE_EXPIRATION_SECS': 86400 * 7,  # 7 дней
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = defaultdict(int)
        self.processed_urls = set()
        # Загружаем существующие товары и создаем индекс по URL
        self.existing_items, self.url_index = self.load_existing_items()
        self.current_items = {}  # Здесь будем хранить все товары текущего запуска
        self.stats['total_products'] = len(self.existing_items)
        self.stats['updated_items'] = 0
        self.stats['new_items'] = 0

    def load_existing_items(self):
        """Загружает существующие товары и создает индекс по URL"""
        items = {}
        url_index = {}
        file_path = Path('interier_products.json')

        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf8') as f:
                    # Пробуем прочитать как JSON массив
                    try:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                item_hash = self.generate_item_hash(item)
                                items[item_hash] = item
                                url_index[item['url']] = item_hash
                            self.logger.info(f"Загружено {len(items)} существующих товаров (JSON массив)")
                            return items, url_index
                    except json.JSONDecodeError:
                        pass

                    # Пробуем прочитать как JSON Lines
                    f.seek(0)
                    for line in f:
                        try:
                            item = json.loads(line)
                            item_hash = self.generate_item_hash(item)
                            items[item_hash] = item
                            url_index[item['url']] = item_hash
                        except json.JSONDecodeError:
                            continue
                    self.logger.info(f"Загружено {len(items)} существующих товаров (JSON Lines)")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки JSON: {str(e)}")
        else:
            self.logger.info("Файл с сохраненными товарами не найден, начнем с чистого листа")
        return items, url_index

    def generate_item_hash(self, item):
        """Создаёт уникальный хеш для товара"""
        unique_str = f"{item['url']}_{item['code']}_{item['name']}"
        return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

    def has_item_changed(self, existing_item, new_item):
        """Проверяет, изменились ли важные поля товара"""
        fields_to_check = ['price', 'old_price', 'availability']
        for field in fields_to_check:
            if existing_item.get(field) != new_item.get(field):
                return True
        return False

    def parse(self, response):
        category_url = response.css('ul.dMenu__lv1 li a:contains("Интерьерные светильники")::attr(href)').get()
        if not category_url:
            category_url = response.xpath('//a[contains(text(), "Интерьерные светильники")]/@href').get()

        if category_url:
            full_url = urljoin(response.url, category_url)
            self.logger.info(f"Нашли URL категории: {full_url}")
            yield scrapy.Request(
                full_url,
                callback=self.parse_subcategories,
                meta={'base_url': full_url}
            )
        else:
            full_url = "https://www.lustrof.ru/category/osveshchenie/"
            self.logger.error(f"Не удалось найти URL категории, используем резервный: {full_url}")
            yield scrapy.Request(
                full_url,
                callback=self.parse_subcategories,
                meta={'base_url': full_url}
            )

    def parse_subcategories(self, response):
        base_url = response.meta['base_url']
        subcategories = response.css('ul.dMenu__lv2 a::attr(href), ul.dMenu__lv3 a::attr(href)').getall()
        if not subcategories:
            subcategories = response.css('div.dMenu_dop a::attr(href)').getall()

        filtered_subcategories = []
        for url in subcategories:
            if url and '/category/osveshchenie/' in url and "aksessuary" not in url:
                filtered_subcategories.append(url)
        filtered_subcategories = list(set(filtered_subcategories))

        self.logger.info(f"Найдено подкатегорий: {len(filtered_subcategories)}")

        for subcat_url in filtered_subcategories:
            full_url = urljoin(base_url, subcat_url)
            if full_url not in self.processed_urls:
                self.processed_urls.add(full_url)
                self.logger.info(f"Переходим в подкатегорию: {full_url}")
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_category,
                    meta={'category_url': full_url}
                )

        if not filtered_subcategories:
            self.logger.info("Подкатегории не найдены, парсим текущую страницу")
            yield from self.parse_category(response)

    def parse_category(self, response):
        category_url = response.meta.get('category_url', response.url)
        yield from self.parse_products(response, category_url=category_url)

        next_page = self.find_next_page(response)
        if next_page:
            next_url = urljoin(response.url, next_page)
            if next_url not in self.processed_urls:
                self.processed_urls.add(next_url)
                yield scrapy.Request(
                    next_url,
                    callback=self.parse_category,
                    meta={'category_url': category_url}
                )

    def find_next_page(self, response):
        next_page = response.css('a.pagin__next::attr(href)').get()
        if next_page:
            return next_page

        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            return next_page

        next_page = response.xpath('//a[contains(text(), "Следующая")]/@href').get()
        if next_page:
            return next_page

        current_page_url = response.css('ul.pagin li.selected a::attr(href)').get()
        if current_page_url:
            parsed = urlparse(current_page_url)
            query = parse_qs(parsed.query)
            current_page = int(query.get('page', [1])[0])
            base_url = response.url.split('?')[0]
            next_page = f"{base_url}?page={current_page + 1}"
            if response.css(f'a[href*="page={current_page + 1}"]'):
                return next_page

        last_page_link = response.css('ul.pagin li:last-child a::attr(href)').get()
        if last_page_link:
            parsed = urlparse(last_page_link)
            query = parse_qs(parsed.query)
            last_page = int(query.get('page', [1])[0])
            parsed_response = urlparse(response.url)
            query_response = parse_qs(parsed_response.query)
            current_page = int(query_response.get('page', [1])[0])
            if current_page < last_page:
                base_url = response.url.split('?')[0]
                return f"{base_url}?page={current_page + 1}"

        return None

    def parse_products(self, response, category_url=None):
        category_name = "Интерьерные светильники"
        products = response.css('div.products__item, div.products-item, div.s-blocks_item')

        self.logger.info(f"На странице {response.url} найдено {len(products)} товаров")

        for product in products:
            name = product.css('span.products__item-info-name::text').get() or \
                   product.css('span.products-item__name::text').get() or \
                   product.css('span.products_item-title::text').get()

            code = product.css('span.products__item-info-code-v::text').get() or \
                   product.css('span.products-item__article::text').get()

            price = product.css('span.products__price-new::text').get() or \
                    product.css('span.products-item__price::text').get() or \
                    product.css('span.products_price-new::text').get()

            old_price = product.css('span.products__price-old::text').get() or \
                        product.css('span.products-item__old-price::text').get()

            product_url = product.css('a::attr(href)').get()
            full_product_url = urljoin(response.url, product_url) if product_url else response.url

            item = {
                'name': self.clean_text(name),
                'code': self.clean_text(code),
                'price': self.clean_price(price),
                'old_price': self.clean_price(old_price),
                'availability': self.extract_availability(product),
                'url': full_product_url,
                'category': category_name
            }

            item_hash = self.generate_item_hash(item)

            # Проверяем, есть ли товар в существующих данных
            existing_item = None
            if full_product_url in self.url_index:
                existing_hash = self.url_index[full_product_url]
                existing_item = self.existing_items.get(existing_hash)

            if existing_item:
                # Проверяем изменения в важных полях
                if self.has_item_changed(existing_item, item):
                    self.logger.info(f"Обновлен товар: {item['name']} ({item['code']})")
                    self.stats['updated_items'] += 1
                    # Обновляем данные в текущей коллекции
                    self.current_items[item_hash] = item
                    yield item
                else:
                    self.logger.debug(f"Товар без изменений: {item['name']} ({item['code']})")
                    # Сохраняем существующую версию
                    self.current_items[existing_hash] = existing_item
            else:
                # Новый товар
                self.logger.info(f"Новый товар: {item['name']} ({item['code']})")
                self.current_items[item_hash] = item
                self.stats['new_items'] += 1
                self.stats['total_products'] += 1
                yield item



    def extract_availability(self, product):
        avail_text = product.css('span.products__available::text, span.products__available-in-stock::text').get() or \
                     product.css('span.products-item__availability::text').get()

        if avail_text and ('в наличии' in avail_text.lower() or 'есть' in avail_text.lower()):
            return 'В наличии'
        return 'Нет в наличии'

    def clean_price(self, price_str):
        if not price_str:
            return None
        cleaned = re.sub(r'[^\d]', '', price_str.strip())
        return int(cleaned) if cleaned else None

    def clean_text(self, text):
        if not text:
            return None
        return ' '.join(text.strip().split())

    def closed(self, reason):
        # Сохраняем все товары в файл
        output_file = 'interier_products.json'
        items_count = len(self.current_items)

        with open(output_file, 'w', encoding='utf8') as f:
            # Используем tqdm для отображения прогресса записи
            with tqdm(total=items_count, desc="Сохранение товаров") as pbar:
                for item in self.current_items.values():
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    pbar.update(1)

        self.logger.info(
            f"Сбор завершен. Новых товаров: {self.stats['new_items']} | "
            f"Обновлено товаров: {self.stats['updated_items']} | "
            f"Дубликатов: {self.stats.get('duplicates', 0)} | "
            f"Всего уникальных: {items_count}"
        )