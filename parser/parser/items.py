import scrapy


class AlcomarketItems(scrapy.Item):
    timestamp = scrapy.Field()  # Время в формате UNIX timestamp
    RPC = scrapy.Field()  # Уникальный идентификатор товара
    url = scrapy.Field()  # Ссылка на товар
    title = scrapy.Field()  # Название с объемом/цветом

    marketing_tags = scrapy.Field()  # Маркетинговые теги
    brand = scrapy.Field()  # Бренд
    section = scrapy.Field()  # Иерархия категорий

    price_data = scrapy.Field()  # Словарь: current, original, sale_tag
    stock = scrapy.Field()  # Словарь: in_stock, count

    assets = scrapy.Field()  # Словарь: main_image, set_images, view360, video

    metadata = scrapy.Field()  # Характеристики + описание
    variants = scrapy.Field()  # Число вариантов (цвет/объем)
