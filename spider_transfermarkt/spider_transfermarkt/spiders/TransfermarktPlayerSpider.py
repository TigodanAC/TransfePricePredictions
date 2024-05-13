import scrapy
from urllib.parse import urlencode
# from spider_transfermarkt.items import SpiderTransfermarktItem

API = 'bce0d650851a70264d134c1acf710817'


def get_url(url):
    payload = {'api_key': API, 'url': url}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url


query = 'kylian'


class TransfermarktplayerspiderSpider(scrapy.Spider):
    name = "TransfermarktPlayerSpider"

    def start_requests(self):
        url = 'https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?' + urlencode({'query': query})
        print(url)
        yield scrapy.Request(url=get_url(url), callback=self.parse_player)

    # def parse_player(self, response):
        # item = SpiderTransfermarktItem()
        # print("hello")
        # item.url = response.xpath('//*[@id="yw0"]/table/tbody/tr[1]/td[1]/table/tbody/tr[1]/td[2]/a/@href').extract()[0]
