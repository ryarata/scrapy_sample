# -*- coding: utf-8 -*-

import scrapy

import sys
from datetime import datetime
import re
#import pymongo
import MySQLdb
import urllib.request
import urllib.error

##connection
#client = pymongo.MongoClient()
#db = client.test
#collection = db.my_first_collection

IMAGES_STORE = '../images/'

conn = MySQLdb.connect(
        user='root',
        passwd='assamdarje2013',
        host='localhost',
        db='pinchae_1707'
    )
c = conn.cursor()

class WalkerFireWorks(scrapy.Spider):
    name = 'walker_fire_works'

    # エンドポイント（クローリングを開始するURLを記載する）
    start_urls = ['https://hanabi.walkerplus.com/list/ar0313/']

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
    }

    # URLの抽出処理を記載
    def parse(self, response):
        #スクレイピング対象のデータはここから
        for href in response.css('li.clearfix > a::attr(href)'):
            full_url = response.urljoin(href.extract())

            # 抽出したURLを元にRequestを作成し、ダウンロードする
            yield scrapy.Request(full_url, callback=self.parse_item)

        #pagingがある場合はこちらで再帰的に行う
        for href in response.css('div.paging > ul > li > a::attr(href)'):
            full_url = response.urljoin(href.extract())

            # 抽出したURLを元にRequestを作成し、ダウンロードする
            yield scrapy.Request(full_url)

    # ダウンロードしたページを元に、内容を抽出し保存するItemを作成
    def parse_item(self, response):
        name = response.css('h1.contentsttl::text').extract_first()
        detail = response.css('div.maintxt > p::text').extract_first()
        time_text = response.css('p.detail_h_date::text').extract_first()
        date_pattern = re.compile('(\d{4})年(\d{1,2})月(\d{1,2})日')
        date_result = date_pattern.search(time_text)
        year = date_result[1]
        month = date_result[2]
        day = date_result[3]
        time_pattern = re.compile('(\d{1,2}):(\d{1,2})')
        time_result = time_pattern.findall(time_text)
        if len(time_result) > 1:
            start_hour = time_result[0][0]
            start_minute = time_result[0][1]
            end_hour = time_result[1][0]
            end_minute = time_result[1][1]
        elif len(time_result) == 0:
            start_hour = "0"
            start_minute = "0"
            end_hour = "0"
            end_minute = "0"
        else:
            start_hour = time_result[0][0]
            start_minute = time_result[0][1]
            end_hour = str(int(start_hour) + 2)
            end_minute = "0"
        
        start_date = datetime.strptime(year+'/'+month+'/'+day+' '+start_hour+':'+start_minute+':00', '%Y/%m/%d %H:%M:%S')
        end_date = datetime.strptime(year+'/'+month+'/'+day+' '+end_hour+':'+end_minute+':00', '%Y/%m/%d %H:%M:%S')
        
        sql = 'insert into events(category_id,name,detail,start_time,end_time,end_flag,special_flag,created_at,updated_at) values (5, %s,%s, %s,%s, 0,0,now(),now())'
        c.execute(sql, (name,detail,start_date,end_date))

        conn.commit()

        event_id = c.lastrowid
        img_url = response.css('div.mainph > img::attr(src)').extract_first()
        filename = img_url.split('/')[-1]
        if filename == "noimage_l.jpg":
             img_url = "https://hanabi.walkerplus.com/images/noimage_l.jpg"
        i = urllib.request.urlopen(img_url)
        

        saveData = open(IMAGES_STORE + str(event_id) + ".jpg", 'wb');
        saveData.write(i.read());
        saveData.close()
        
        i.close()

        request = scrapy.Request(response.url+"/map.html", callback=self.parse_address)
        request.meta["event_id"] = event_id
        yield request

    def parse_address(self,response):
        prefecture_city = response.css('p.detail_h_place::text').extract_first()
        latlang = response.css('div.section > iframe::attr(src)').extract_first().split("?")[1].split("&")[0][5:]
        lat = latlang.split(",")[0][:9]
        lng = latlang.split(",")[1][:9]
        sql = 'insert into addresses(prefecture_id,addressable_id,addressable_type,latitude,longitude,created_at,updated_at) values (13, %s,"Event", %s,%s, now(),now())'
        c.execute(sql, (response.meta["event_id"], float(lat),float(lng)))
        conn.commit()
        return 

