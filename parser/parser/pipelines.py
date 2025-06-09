from datetime import datetime
import json

class AlcomarketPipeline:
    def open_spider(self, spider):
        self.file = open('result.json', 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first = True

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False, indent=2)
        if not self.first:
            self.file.write(',\n')
        self.file.write(line)
        self.first = False
        return item
