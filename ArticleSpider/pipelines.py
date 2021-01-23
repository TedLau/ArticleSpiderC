# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import codecs
import json

import MySQLdb
from scrapy.exporters import JsonItemExporter
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi


class ArticlespiderPipeline:
    def process_item(self, item, spider):
        return item


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            image_file_path = ""
            for ok, value in results:
                image_file_path = value['path']
            item['front_image_path'] = image_file_path

        return item


class MysqlPipeline(object):  # setting 设置
    def __init__(self):
        self.conn = MySQLdb.connect("127.0.0.1", 'root', 'root', 'article_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into cnblogs(title, url, url_obj_id, front_image_path, front_image_url, praise_nums, comment_nums, fav_nums, tags, comments, create_time)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        params = list()  # 不是所有的都有，使用get方法可以比较稳妥
        params.append(item.get('title', ""))
        params.append(item.get('url', ""))
        params.append(item.get('url_obj_id', ""))
        front_image = ",".join(item.get("front_image_url", ""))
        params.append(item.get(front_image))
        params.append(item.get('front_image_path', ""))

        params.append(item.get('praise_nums', 0))
        params.append(item.get('comment_nums', 0))
        params.append(item.get('fav_nums', 0))
        params.append(item.get('tags', ""))
        params.append(item.get('comments', ""))
        params.append(item.get('create_time', "1970-07-01"))

        self.cursor.execute(insert_sql, tuple(params))
        self.conn.commit()
        return item


class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        from MySQLdb.cursors import DictCursor
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            db=settings['MYSQL_DBNAME'],
            user=settings["MYSQL_USER"],
            passwd=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True,
        )
        # 使用twisted 不能直接使用db 使用adbapi

        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)  # 方法扔到池中执行
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        print(failure)  # 输出错误，以便排除

    def do_insert(self, cursor, item):
        insert_sql = """
                    insert into cnblogs(title, url, url_obj_id, front_image_path, front_image_url, praise_nums, comment_nums, fav_nums, tags, comments, create_time)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE praise_nums=values(praise_nums)
                    """
        params = list()  # 不是所有的都有，使用get方法可以比较稳妥
        params.append(item.get('title', ""))
        params.append(item.get('url', ""))
        params.append(item.get('url_obj_id', ""))
        front_image = ",".join(item.get("front_image_url", ""))
        params.append(item.get(front_image))
        params.append(item.get('front_image_path', ""))

        params.append(item.get('praise_nums', 0))
        params.append(item.get('comment_nums', 0))
        params.append(item.get('fav_nums', 0))
        params.append(item.get('tags', ""))
        params.append(item.get('comments', ""))
        params.append(item.get('create_time', "1970-07-01"))

        cursor.execute(insert_sql, tuple(params))  # list 转 tuple 通用性强


class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出
    def __init__(self):
        self.file = codecs.open("article.json", "w", encoding="utf8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    def __init__(self):
        self.file = codecs.open("articleexport.json", "wb")
        self.exporter = JsonItemExporter(self.file, encoding="utf8", ensure_ascii=False)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
