import json


class AlkotekaPipeline:
    def open_spider(self, spider):
        self.file = open('cleaned_products.json', 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first_item = True

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()

    def process_item(self, item, spider):
        item['title'] = item['title'].strip() if item['title'] else ''
        item['marketing_tags'] = [tag.strip() for tag in item.get('marketing_tags', []) if tag.strip()]

        if 'price_data' in item:
            for key in ['price', 'original_price']:
                price = item['price_data'].get(key)
                if isinstance(price, str):
                    item['price_data'][key] = int(''.join(filter(str.isdigit, price))) if price else None

        if not self.first_item:
            self.file.write(',\n')
        self.first_item = False

        line = json.dumps(dict(item), ensure_ascii=False, indent=2)
        self.file.write(line)
        return item
