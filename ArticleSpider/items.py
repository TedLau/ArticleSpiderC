# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import re
import scrapy
from itemloaders.processors import MapCompose
from itemloaders.processors import TakeFirst, Identity, Join
from scrapy.loader import ItemLoader


def add_cnblogs(value):
    return value + "-tedlau"


def add_test(value):
    return value + '-test'


# 定义一个remove可以过滤掉我们不需要的tag 并使用mapcompose传递
def remove_tags(value):
    if value == "sometag":
        return ""
    else:
        return value


def time_convert(value):
    match_re = re.match(".*?(\d+.*)", value)
    if match_re:
        return match_re.group(1)
    else:
        return "1970-01-01"  # value 设置默认值


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    create_time = scrapy.Field(
        input_processor=MapCompose(time_convert)
    )
    url = scrapy.Field()
    url_obj_id = scrapy.Field()
    front_image_url = scrapy.Field(
        # input_processor=MapCompose(add_cnblogs, add_test), # 逐一的进行调用
        out_processor=Identity()
    )  # 只有一个field类型
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field()
    comment_nums = scrapy.Field()
    fav_nums = scrapy.Field()
    tags = scrapy.Field(
        output_processor=Join(separator=",")  # 原因是原来的tag有多个tag，可能组成taglist，join需要研究用什么将其join起来  使用separater
    )
    content = scrapy.Field()
    pass


class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
