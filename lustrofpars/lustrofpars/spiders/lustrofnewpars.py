import scrapy
import re
from urllib.parse import urljoin
from collections import defaultdict
import math


class LustrofnewparsSpider(scrapy.Spider):
    name = "lustrofnewpars"
    allowed_domains = ["lustrof.ru"]
    start_urls = ["https://www.lustrof.ru/category/osveshchenie/lyustry/"]

    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DOWNLOAD_DELAY': 2.0,
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            'products.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['name', 'code', 'price', 'old_price', 'availability', 'url', 'page'],
                'overwrite': True
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = defaultdict(int)
        self.products_per_page = 96

    def parse(self, response):
        # Простой метод определения страниц
        last_page = response.css('ul.pagin a::attr(href)').re(r'page=(\d+)')
        self.stats['total_pages'] = max(map(int, last_page)) if last_page else 1

        self.logger.info(f'Найдено страниц: {self.stats["total_pages"]}')

        yield from self.parse_products(response)

        if self.stats['total_pages'] > 1:
            for page in range(2, self.stats["total_pages"] + 1):
                yield response.follow(
                    f"{response.url}?page={page}",
                    callback=self.parse_products,
                    meta={'page': page}
                )

    def parse_products(self, response):
        page = response.meta.get('page', 1)
        products = response.css('div.products__item')

        for product in products:
            yield {
                'name': self.clean_text(product.css('span.products__item-info-name::text').get()),
                'code': product.css('span.products__item-info-code-v::text').get(),
                'price': self.clean_price(product.css('span.products__price-new::text').get()),
                'old_price': self.clean_price(product.css('span.products__price-old::text').get()),
                'availability': self.extract_availability(product),
                'url': urljoin(response.url, product.css('a::attr(href)').get()),
                'page': page
            }

    def extract_availability(self, product):
        avail_text = product.css('span.products__available::text, span.products__available-in-stock::text').get()
        return 'В наличии' if avail_text and 'в наличии' in avail_text.lower() else 'Нет в наличии'

    def clean_price(self, price_str):
        if not price_str:
            return None
        return int(re.sub(r'[^\d]', '', price_str.strip()))

    def clean_text(self, text):
        if not text:
            return None
        return ' '.join(text.strip().split())