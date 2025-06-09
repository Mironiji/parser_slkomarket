import scrapy
import json
from ..items import AlcomarketItems


class AlkotekaSpider(scrapy.Spider):
    name = 'alcomarket_spider'
    allowed_domains = ['alkoteka.com']

    proxies = {
        'http': 'http://user:password@yourproxy.com:port',
        'https': 'https://user:password@yourproxy.com:port'
    }

    cookies = {
        'alkoteka_locality': '%7B%22uuid%22%3A%224a70f9e0-46ae-11e7-83ff-00155d026416%22%2C%22name%22%3A%22%D0%9A%D1%80%D0%B0%D1%81%D0%BD%D0%BE%D0%B4%D0%B0%D1%80%22%2C%22slug%22%3A%22krasnodar%22%2C%22longitude%22%3A%2238.975996%22%2C%22latitude%22%3A%2245.040216%22%2C%22accented%22%3Atrue%7D'
    }

    start_urls = ['https://alkoteka.com/catalog/slaboalkogolnye-napitki-2']
    RPC_current_code = 0

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, cookies=self.cookies, callback=self.parse)

    def parse(self, response, **kwargs):
        product_links = response.xpath('//*[@id="root"]/main/section/div[2]/div[3]/div[2]/a').getall()
        print(product_links)
        for link in product_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, cookies=self.cookies, callback=self.parse_product)

        next_page = response.xpath('//a[contains(@class, "next") and contains(@class, "page-numbers")]/@href').get()
        if next_page:
            yield response.follow(next_page, cookies=self.cookies, callback=self.parse)

    def parse_product(self, response):
        item = AlcomarketItems()
        self.url_parsing(response, item)
        self.rpc(item)
        self.title_parsing(response, item)
        self.brand_parsing(response, item)
        self.section_parsing(response, item)
        self.tags_parsing(response, item)
        self.price_parsing(response, item)
        self.image_parsing(response, item)
        self.metadata_parsing(response, item)
        self.variants_parsing(response, item)
        self.stock_parsing(response, item)
        yield item

    def title_parsing(self, response, item):
        title = response.xpath('//h1/text()').get(default='').strip()
        characteristics = response.xpath('//ul[@class="props"]/li')
        extra_info_parts = []
        for char in characteristics:
            label = char.xpath('strong/text()').get(default='').strip().lower()
            value = char.xpath('text()').get(default='').strip()

            if label in ['цвет', 'объем', 'объём']:
                extra_info_parts.append(value)
        if extra_info_parts:
            for part in extra_info_parts:
                if part.lower() not in title.lower():
                    title += f", {part}"
        item['title'] = title.strip()

    def url_parsing(self, response, item):
        item['url'] = response.url

    def brand_parsing(self, response, item):
        item['brand'] = response.xpath('//div[@class="brand"]/text()').get()

    def section_parsing(self, response, item):
        breadcrumbs = response.xpath('//nav[contains(@class,"breadcrumbs")]//a/text()').getall()
        item['section'] = [bc.strip() for bc in breadcrumbs if bc.strip()]

    def tags_parsing(self, response, item):
        item['marketing_tags'] = response.xpath('//div[contains(@class,"product-item-label")]/text()').getall()

    def rpc(self, item):
        item['RPC'] = self.rpc
        self.rpc += 1

    def price_parsing(self, response, item):
        current_price = self.extract_price(response.xpath('//span[@class="price"]/text()').get())
        original_price = self.extract_price(response.xpath('//span[@class="old-price"]/text()').get())
        if not original_price or original_price == current_price:
            original_price = current_price
            sale_tag = None
        else:
            discount = round((original_price - current_price) / original_price * 100)
            sale_tag = f"Скидка {discount}%"
        item['price_data'] = {
            'current': current_price,
            'original': original_price,
            'sale_tag': sale_tag
        }

    def stock_parsing(self, response, item):
        in_stock = bool(response.xpath('//button[contains(text(), "В корзину") or contains(text(), "Купить")]'))
        count_text = response.xpath('//div[contains(text(), "Осталось")]/text()').get()
        count = 0
        if count_text:
            import re
            match = re.search(r'Осталось\s+(\d+)', count_text)
            if match:
                count = int(match.group(1))
        item['stock'] = {
            'in_stock': in_stock,
            'count': count
        }

    def metadata_parsing(self, response, item):
        description = response.xpath('//div[contains(@class, "description")]/descendant::text()').getall()
        description = ' '.join([d.strip() for d in description if d.strip()])
        metadata = {'__description': description}
        char_blocks = response.xpath('//ul[contains(@class,"props")]/li')
        for li in char_blocks:
            key = li.xpath('strong/text()').get()
            value = li.xpath('text()').get()
            if key and value:
                metadata[key.strip()] = value.strip()
        item['metadata'] = metadata

    def variants_parsing(self, response, item):
        variant_texts = response.xpath(
            '//div[contains(@class,"offer-item") or contains(@class,"product-options")]//text()').getall()
        variant_texts = [v.lower().strip() for v in variant_texts if v.strip()]
        keywords = ['мл', 'л', 'литр', 'объем', 'цвет', 'масса', 'г', 'кг']
        variant_count = sum(1 for v in variant_texts if any(k in v for k in keywords))
        item['variants'] = variant_count

    def image_parsing(self, response, item):
        images = response.xpath('//div[contains(@class,"product-gallery")]//img/@src').getall()
        images = [response.urljoin(img) for img in images if img]

        main_image = images[0] if images else None

        videos = response.xpath('//video/source/@src | //iframe[contains(@src, "youtube")]/@src').getall()
        videos = [response.urljoin(v) for v in videos]
        view360 = response.xpath(
            '//div[contains(@class,"360") or contains(@class,"viewer") or contains(@class,"three-sixty")]//img/@src').getall()
        view360 = [response.urljoin(v) for v in view360]
        item['assets'] = {
            "main_image": main_image,
            "set_images": images,
            "view360": view360,
            "video": videos
        }

    def extract_price(self, text):
        if text:
            return int(''.join(filter(str.isdigit, text)))
        return None