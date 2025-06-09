import scrapy
import json
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class AlkotekaApiSpider(scrapy.Spider):
    name = 'alkoteka_api'
    allowed_domains = ['alkoteka.com']
    start_urls = [
        'https://alkoteka.com/web-api/v1/product?city_uuid=396df2b5-7b2b-11eb-80cd-00155d039009&page=1&per_page=20&root_category_slug=slaboalkogolnye-napitki-2',
        'https://alkoteka.com/web-api/v1/product?city_uuid=396df2b5-7b2b-11eb-80cd-00155d039009&options%5Bcategories%5D[]=viski&page=1&per_page=20&root_category_slug=krepkiy-alkogol',
        'https://alkoteka.com/web-api/v1/product?city_uuid=396df2b5-7b2b-11eb-80cd-00155d039009&options%5Bcategories%5D[]=vodka&page=1&per_page=20&root_category_slug=krepkiy-alkogol'
    ]

    def start_requests(self):
        cookies = {
            "alkoteka_locality": "%7B%22uuid%22%3A%224a70f9e0-46ae-11e7-83ff-00155d026416%22%2C%22name%22%3A%22%D0%9A%D1%80%D0%B0%D1%81%D0%BD%D0%BE%D0%B4%D0%B0%D1%80%22%2C%22slug%22%3A%22krasnodar%22%2C%22longitude%22%3A%2238.975996%22%2C%22latitude%22%3A%2245.040216%22%2C%22accented%22%3Atrue%7D"
        }
        for url in self.start_urls:
            yield scrapy.Request(url, cookies=cookies, callback=self.parse, cb_kwargs={'base_url': url})

    def parse(self, response, base_url):
        data = json.loads(response.text)
        results = data.get('results', [])
        if not results:
            return

        for product in results:
            title = product.get('name', '')
            filters = product.get('filter_labels')
            volume, color = '', ''
            for k in filters:
                if k['filter'] == 'cvet':
                    color = k['title']
                if k['filter'] == 'obem':
                    volume = k['title']

            if volume and volume not in title:
                title = f"{title}, {volume}"
            elif color and color not in title:
                title = f"{title}, {color}"

            current = product.get('price', 0) or 0
            original = product.get('prev_price') or 0

            discount = round((original - current) / original * 100) if original > 0 else 0
            sale_tag = f"Скидка {discount}%" if discount else ""

            item = {
                "timestamp": int(time.time()),
                "RPC": product.get('uuid'),
                "url": product.get('product_url'),
                "title": title,
                "section": product.get('category')['name'] + ', ' + product.get('category')['parent']['name'],
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
                    "Объем": volume,
                    "Цвет": color,
                    "Артикул": product.get('vendor_code'),
                },
            }

            yield item

        parsed_url = urlparse(base_url)
        query_params = parse_qs(parsed_url.query)
        current_page = int(query_params.get('page', [1])[0])
        next_page = current_page + 1
        query_params['page'] = [str(next_page)]
        new_query = urlencode(query_params, doseq=True)
        next_url = urlunparse(parsed_url._replace(query=new_query))

        yield scrapy.Request(next_url, cookies=response.request.cookies, callback=self.parse, cb_kwargs={'base_url': next_url})