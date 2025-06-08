import scrapy
from datetime import datetime
from ..items import AlcomarketItems

class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka'
    allowed_domains = ['alkoteka.com']
    cookies = {
        'alkoteka_locality': '%7B%22uuid%22%3A%224a70f9e0-46ae-11e7-83ff-00155d026416%22%2C%22name%22%3A%22%D0%9A%D1%80%D0%B0%D1%81%D0%BD%D0%BE%D0%B4%D0%B0%D1%80%22%2C%22slug%22%3A%22krasnodar%22%2C%22longitude%22%3A%2238.975996%22%2C%22latitude%22%3A%2245.040216%22%2C%22accented%22%3Atrue%7D'
    }
    start_urls = ['https://alkoteka.com/catalog/slaboalkogolnye-napitki-2']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, cookies=self.cookies, callback=self.parse)

    def parse(self, response):
        product_links = response.xpath('//div[contains(@class,"product-item")]/a[@class="product-item-image-link"]/@href').getall()
        for link in product_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, cookies=self.cookies, callback=self.parse_product)

        next_page = response.xpath('//a[@class="next page-numbers"]/@href').get()
        if next_page:
            yield response.follow(next_page, cookies=self.cookies, callback=self.parse)

    def parse_product(self, response):
        item = AlcomarketItems()

        # URL
        item['url'] = response.url

        # Поиск артикула
        article = None
        char_blocks = response.xpath('//ul[@class="props"]/li')
        for li in char_blocks:
            label = li.xpath('strong/text()').get(default='').strip().lower()
            if 'артикул' in label:
                article = li.xpath('text()').get(default='').strip()
                break
        item['RPC'] = article

        # Название
        title = response.xpath('//h1/text()').get(default='').strip()

        # Характеристики
        characteristics = response.xpath('//ul[@class="props"]/li')
        extra_info_parts = []
        for char in characteristics:
            label = char.xpath('strong/text()').get(default='').strip().lower()
            value = char.xpath('text()').get(default='').strip()

            if label in ['цвет', 'объем', 'объём']:
                extra_info_parts.append(value)

        # Добавим к title
        if extra_info_parts:
            for part in extra_info_parts:
                if part.lower() not in title.lower():
                    title += f", {part}"
        item['title'] = title.strip()

        # Бренд
        item['brand'] = response.xpath('//div[@class="brand"]/text()').get()

        # Раздел
        item['section'] = 'Слабоалкогольные напитки'

        # Маркетинговые теги
        item['marketing_tags'] = response.xpath('//div[contains(@class,"product-item-label")]/text()').getall()

        # Цена
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

        # Наличие
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

        # Получаем все изображения
        images = response.xpath('//div[contains(@class,"product-gallery")]//img/@src').getall()
        images = [response.urljoin(img) for img in images if img]

        # Основное изображение
        main_image = images[0] if images else None

        # Видео и 360
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

        # Метаданные и вариации
        item['metadata'] = {'source': 'alkoteka.com'}
        item['variants'] = []

        # Время
        item['timestamp'] = datetime.utcnow().isoformat()

        # Описание
        description = response.xpath('//div[contains(@class, "description")]/descendant::text()').getall()
        description = ' '.join([d.strip() for d in description if d.strip()])

        # Характеристики
        metadata = {'__description': description}
        char_blocks = response.xpath('//ul[contains(@class,"props")]/li')
        for li in char_blocks:
            key = li.xpath('strong/text()').get()
            value = li.xpath('text()').get()
            if key and value:
                metadata[key.strip()] = value.strip()

        item['metadata'] = metadata

        # Поиск возможных вариантов (цвет, объем, масса)
        variant_texts = response.xpath(
            '//div[contains(@class,"offer-item") or contains(@class,"product-options")]//text()').getall()
        variant_texts = [v.lower().strip() for v in variant_texts if v.strip()]

        keywords = ['мл', 'л', 'литр', 'объем', 'цвет', 'масса', 'г', 'кг']
        variant_count = sum(1 for v in variant_texts if any(k in v for k in keywords))

        item['variants'] = variant_count

        yield item

    def extract_price(self, text):
        if text:
            return int(''.join(filter(str.isdigit, text)))
        return None