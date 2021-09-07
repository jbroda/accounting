import re
import requests
import logging
import scrapy
from twisted.internet import reactor
from scrapy.http import FormRequest, HtmlResponse
from django.http import HttpResponse, HttpResponseRedirect
from scrapy.crawler import CrawlerRunner
from multiprocessing import Process, Queue

###############################################################################
logger = logging.getLogger(__name__)

##############################################################################
# Cook County URL.
CC_URL = "https://www.cookcountypropertyinfo.com/"

# URL of the main page.
DEFAULT_URL = CC_URL + "default.aspx"

# URL of the property info form.
POST_URL = CC_URL + "pinresults.aspx"

HEADERS = {
    'User-Agent':' Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
}

##############################################################################
class PropertyInfoSpider(scrapy.Spider):
    name = "properties"
    PIN = None

    def __init__(self, pin):
        self.PIN = pin

    def start_requests(self):
        urls = [ CC_URL ]

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.data = {}

        # Hidden inputs
        hidden_inputs = response.xpath('//div[@class="aspNetHidden"]/input')
        for inp in hidden_inputs:
            name = inp.xpath('@name').extract()[0]
            try:
                value = inp.xpath('@value').extract()[0]
            except IndexError:
                value = ""
            self.data[name] = value

        # Split PIN
        pin = self.PIN
        pin = pin.split('-')

        # PIN inputs.
        pin_inputs = response.xpath('//div[@id="pinsearch"]/input')
        for (idx, inp) in enumerate(pin_inputs):
            name = inp.xpath('@name').extract()[0]
            try:
                value = inp.xpath('@value').extract()[0]
            except IndexError:
                value = ""
            self.data[name] = pin[idx]

        # Search button
        submit_button = response.xpath('//div[@id="pinsearchcontainer1"]/input[@value="SEARCH"]')
        name = submit_button.xpath('@name').extract()[0]
        value = submit_button.xpath('@value').extract()[0]
        self.data[name] = value

        # __EVENTARGUMENT
        self.data["__EVENTARGUMENT"] = "btnPIN"

        return FormRequest(url=POST_URL,
                           method='POST',
                           callback=self.parse_page,
                           formdata=self.data,
                           dont_filter=True,
                           headers=HEADERS)

    def parse_page(self, response):
        # Replace href's and src's with relative urls with absolute CC_URL.
        body = response.body

        try:
            body = re.sub(r'href="(?!http)(?!//)', 'href="{0}'.format(CC_URL), body)
            body = re.sub(r'src="(?!http)(?!//)', 'src="{0}'.format(CC_URL), body)
        except Exception as e:
            logger.exception(e)

        global RESPONSE
        RESPONSE = body

##############################################################################
def run_crawler(q,pin,isTest):
    if not isTest:
        # Initialize Django for this process.
        import django
        django.setup()

    logger.info("pin: {0}".format(pin))

    try:
        runner = CrawlerRunner({ 'USER_AGENT' : HEADERS['User-Agent'] })
        d = runner.crawl(PropertyInfoSpider, pin)
        d.addBoth(lambda _: reactor.stop())
        reactor.run() # the script will block here until the crawling is finished
        r = RESPONSE

        # Create the response
        if not isTest:
            r = HttpResponse(content=RESPONSE, content_type='text/html; charset=utf-8')

    except Exception as e:
        logger.exception(e)
        if not isTest:
            r = HttpResponseRedirect(POST_URL)

    q.put(r)

##############################################################################
def get_cook_county_info_resp(pin,isTest=False):
    logger.info("pin: {0}".format(pin))

    # Spawn a subprocess for the crawler.
    try:
        q = Queue()
        p = Process(target=run_crawler, args=(q,pin,isTest))
        p.start()
        r = q.get(timeout=30)
        p.join()
    except Exception as e:
        logger.exception(e)
        r = None

    return r

##############################################################################
# Test
if __name__ == '__main__':
    PIN = "02-34-102-064-1195"
    r = get_cook_county_info_resp(PIN, isTest=True)
    print r
