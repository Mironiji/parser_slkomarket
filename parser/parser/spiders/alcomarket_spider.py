import scrapy
import json
import time


class AlkotekaApiSpider(scrapy.Spider):
    name = 'alkoteka_api'
    allowed_domains = ['alkoteka.com']
    start_urls = [
        'https://alkoteka.com/web-api/v1/product?city_uuid=396df2b5-7b2b-11eb-80cd-00155d039009&page=1&per_page=20&root_category_slug=slaboalkogolnye-napitki-2'
    ]

    def parse(self, response, **kwargs):
        data = json.loads(response.text)
        for product in data.get('results', []):
            title = product.get('name', '')
            filters = product.get('filter_labels')
            for k in filters:
                if k['filter'] == 'cvet':
                    color = k['title']
                if k['filter'] == 'obem':
                    volume = k['title']
            volume, color = '', ''

            if volume and volume not in title:
                title = f"{title}, {volume}"
            elif color and color not in title:
                title = f"{title}, {color}"

            current = product.get('price', 0)
            original = product.get('prev_price')
            if current is None:
                current = 0
            if original is None:
                original = 0
            if original > 0:
                discount = round((original - current) / original * 100)
            else:
                discount = 0
            sale_tag = f"Скидка {discount}%"

            item = {
                "timestamp": int(time.time()),
                "RPC": product.get('uuid'),
                "url": product.get('url'),
                "title": title,
                "marketing_tags": product.get('labels', []),
                "brand": product.get('brand'),
                "section": product.get('category')['name'] + ' ' + product.get('category')['parent']['name'],
                "price_data": {
                    "current": float(current),
                    "original": float(original),
                    "sale_tag": sale_tag
                },
                "stock": {
                    "in_stock": product.get('available', False),
                    "count": product.get('quantity_total', 0)
                },
                "assets": {
                    "main_image": product.get('image_url'),
                },
                "metadata": {
                    "__description": product.get('description', ''),
                    "Объем": volume,
                    "Цвет": color,
                    "Артикул": product.get('sku'),
                    "Страна производитель": product.get('country')
                },
                "variants": 1 if volume or color else 0
            }

            yield item

        # пагинация
        pagination = data.get('meta', {}).get('pagination', {})
        if pagination.get('next'):
            yield scrapy.Request(
                url=pagination['next'],
                callback=self.parse
            )
