from datetime import datetime
import json

class AlcomarketPipeline:
    def open_spider(self, spider):
        self.file = open("alkoteka_output.json", "w", encoding="utf-8")
        self.file.write("[\n")
        self.first_item = True

    def close_spider(self, spider):
        self.file.write("\n]")
        self.file.close()

    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(",\n")
        json.dump(dict(item), self.file, ensure_ascii=False, indent=2)
        self.first_item = False
        return item

