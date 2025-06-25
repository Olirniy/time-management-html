import scrapy
import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from collections import defaultdict

class LustrofnewparsSpider(scrapy.Spider):
    name = "lustrofnewpars"
    allowed_domains = ["lustrof.ru"]
    start_urls = ["https://www.lustrof.ru/"]

    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS': 2,
        'RETRY_TIMES': 3,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            'interier_products.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['name', 'code', 'price', 'old_price', 'availability', 'url', 'category'],
                'overwrite': True
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = defaultdict(int)
        self.processed_urls = set()
        self.category_page_count = defaultdict(int)

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

        # Сбор подкатегорий
        subcategories = response.css('ul.dMenu__lv2 a::attr(href), ul.dMenu__lv3 a::attr(href)').getall()
        if not subcategories:
            subcategories = response.css('div.dMenu_dop a::attr(href)').getall()

        # Фильтрация и дедупликация
        filtered_subcategories = []
        for url in subcategories:
            if url and '/category/osveshchenie/' in url and "aksessuary" not in url:
                filtered_subcategories.append(url)
        filtered_subcategories = list(set(filtered_subcategories))

        self.logger.info(f"Найдено подкатегорий: {len(filtered_subcategories)}")

        for subcat_url in filtered_subcategories:
            full_url = urljoin(base_url, subcat_url)
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

        # Парсим товары на текущей странице
        yield from self.parse_products(response, category_url=category_url)

        # УЛУЧШЕННАЯ ПАГИНАЦИЯ
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
        """Находит URL следующей страницы всеми возможными способами"""
        # 1. Стандартная кнопка "Следующая"
        next_page = response.css('a.pagin__next::attr(href)').get()
        if next_page:
            return next_page

        # 2. Ссылка с rel="next"
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            return next_page

        # 3. Текстовая ссылка "Следующая"
        next_page = response.xpath('//a[contains(text(), "Следующая")]/@href').get()
        if next_page:
            return next_page

        # 4. Вычисление следующей страницы через номер текущей
        current_page_url = response.css('ul.pagin li.selected a::attr(href)').get()
        if current_page_url:
            # Извлекаем номер текущей страницы
            parsed = urlparse(current_page_url)
            query = parse_qs(parsed.query)
            current_page = int(query.get('page', [1])[0])

            # Формируем URL следующей страницы
            base_url = response.url.split('?')[0]
            next_page = f"{base_url}?page={current_page + 1}"

            # Проверяем есть ли такая страница в пагинации
            if response.css(f'a[href*="page={current_page + 1}"]'):
                return next_page

        # 5. Попытка определить общее количество страниц
        last_page_link = response.css('ul.pagin li:last-child a::attr(href)').get()
        if last_page_link:
            parsed = urlparse(last_page_link)
            query = parse_qs(parsed.query)
            last_page = int(query.get('page', [1])[0])

            # Если текущая страница не последняя
            if 'page=' in response.url:
                current_page = int(parse_qs(urlparse(response.url).query.get('page', [1])[0]))
                if current_page < last_page:
                    return f"?page={current_page + 1}"
            else:
                return f"?page=2"

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

            item = {
                'name': self.clean_text(name),
                'code': self.clean_text(code),
                'price': self.clean_price(price),
                'old_price': self.clean_price(old_price),
                'availability': self.extract_availability(product),
                'url': urljoin(response.url, product_url) if product_url else response.url,
                'category': category_name
            }

            self.stats['total_products'] = self.stats.get('total_products', 0) + 1
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
        products = self.stats.get('total_products', 0)
        self.logger.info(f"Сбор данных завершен. Товаров собрано: {products}")