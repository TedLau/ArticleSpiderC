import json
import re
from urllib import parse

import scrapy
from scrapy import Request
from ArticleSpider.items import ArticlespiderItem
from ArticleSpider.utils import common
from ArticleSpider.items import ArticleItemLoader


class CnblogsSpider(scrapy.Spider):
    name = 'cnblogs'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    def parse(self, response):

        """
        1、获取新闻列表中的新闻url并交给scrapy进行下载后调用对应的解析方法
        2、获取下一页的URL并交给scrapy进行下载，之后继续跟进

        """
        post_nodes = response.css('#news_list .news_block')
        for post_node in post_nodes:
            image_url = post_node.css('.entry_summary a img::attr(src)').extract_first("")
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            post_url = post_node.css('h2 a::attr(href)').extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)

        next_url = response.xpath("//a[contains(text(),'Next >')]/@href").extract_first("")
        yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse_detail)

    # pass

    def parse_detail(self, response):
        match_re = re.match(".*?(\d+)", response.url)
        if match_re:
            post_id = match_re.group(1)
            # article_item = ArticlespiderItem()
            # title = response.css("#news_title a::text").extract_first("")
            # # title = response.xpath("//*[@id='news_title'//a/text()")
            # create_time = response.css("#news_info .time::text").extract_first("")
            # # create_date = response.xpath("//*[@id='news_info'//*[@class='time']/text()")
            # match_re = re.match(".*?(\d+.*)", create_time)
            # if match_re:
            #     create_time = match_re.group(1)
            # content = response.css("#news_content").extract()[0]
            # # content = response.xpath("//*[@id='news_content']").extract()[0]
            # tag_list = response.css(".news_tags a::text").extract()  # 无法存储list
            # # tag_list = response.xpath("//*[@class=news_tags']//a/text()")
            # tags = ",".join(tag_list)

            # post_id = match_re.group(1)
            # html = requests.get(parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)))
            # 尽量不用同步的库
            # 打断点看是否符合要求
            # url路径 / 可以避免加入到子路径
            # j_data = json.loads(html.text)
            # article_item['title'] = title
            # article_item['create_time'] = create_time
            # article_item['content'] = content
            # article_item['tags'] = tags
            #
            # article_item['url'] = response.url
            # if response.meta.get("front_image_ur;", ""):
            #     article_item['front_image_url'] = [response.meta.get('front_image_url', "")]
            # else:
            #     article_item['front_image_url'] = []

            # 使用itemloader的代码，使得程序可以更加易于维护  匹配项
            item_loader = ArticleItemLoader(item=ArticlespiderItem(), response=response)
            item_loader.add_css("title", "#news_title a::text")
            item_loader.add_css("content", "#news_content")
            item_loader.add_css("tags", ".news_tags a::text")
            item_loader.add_css("create_time", "#news_info .time::text")
            item_loader.add_value("url", response.url)
            if response.meta.get('front_image_url', []):
                item_loader.add_value('front_image_url', response.meta.get('front_image_url', []))

            article_item = item_loader.load_item()
            if response.meta.get("front_image_ur;", ""):
                article_item['front_image_url'] = [response.meta.get('front_image_url', "")]
            else:
                article_item['front_image_url'] = []
            yield Request(url=parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
                          meta={"article_item": article_item}, callback=self.parse_nums)
            # praise_nums = j_data['DiggCount']
            # fav_nums = j_data['TotalView']
            # comment_nums = j_data['CommentCount']
            pass

    def parse_nums(self, response):
        j_data = json.loads(response.text)
        if j_data:

            article_item = response.meta.get('article_item', "")
        # 基于回调的代码

            praise_nums = int(j_data["DiggCount"])



            fav_nums = j_data['TotalView']
            comment_nums = j_data['CommentCount']

        # 延迟调用  代码分离

        # item_loader = response.meta.get("article_item", "")
        # item_loader.add_value("praise_nums", j_data["DiggCount"])
            article_item["praise_nums"] = praise_nums
            article_item['fav_nums'] = fav_nums
            article_item['comment_nums'] = comment_nums
            article_item['url_obj_id'] = common.get_md5(article_item['url'])

            yield article_item
        else:
            print("Error here")
