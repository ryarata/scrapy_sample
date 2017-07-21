# -*- coding: utf-8 -*-

import scrapy


class QiitaSpider(scrapy.Spider):
    name = 'qiita_spider'

    # エンドポイント（クローリングを開始するURLを記載する）
    start_urls = ['http://qiita.com/advent-calendar/2015/categories/programming_languages']

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
    }

    # URLの抽出処理を記載
    def parse(self, response):
        for href in response.css('.adventCalendarList .adventCalendarList_calendarTitle > a::attr(href)'):
            full_url = response.urljoin(href.extract())

            # 抽出したURLを元にRequestを作成し、ダウンロードする
            yield scrapy.Request(full_url, callback=self.parse_item)

    # ダウンロードしたページを元に、内容を抽出し保存するItemを作成
    def parse_item(self, response):

        urls = []
        for href in response.css('.adventCalendarItem_entry > a::attr(href)'):
            full_url = response.urljoin(href.extract())
            urls.append(full_url)

        yield {
            'title': response.css('h1::text').extract(),
            'urls': urls,
        }