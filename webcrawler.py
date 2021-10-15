# Writed by Munseok, since 2021-09-27
import json
import logging
import re
import sys
from datetime import datetime

import pymysql
import selenium
from selenium import webdriver

import err

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler('debug.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# data 불러오기
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")

chrome_driver = webdriver.Chrome(executable_path='./chromedriver', chrome_options=chrome_options)


# SQL Connection
try:
    conn = pymysql.connect(host='localhost', user='root', password='1234', db='news', charset='utf8')
    cursor = conn.cursor()
except pymysql.err.OperationalError:
    logging.warning("Cannot connect to SQL Server!")

    f.close()
    chrome_driver.quit()
    sys.exit()

sql = "INSERT INTO junnam_news (unique_num, title, agency, writed_date, collected_date, hyperlink) VALUES (%s, %s, %s, %s, %s, %s)"

site_category = data["site_category"]

def main():
    sites = data["site_name"]

    for site in sites.values():
        crawler(site)

    f.close()
    chrome_driver.quit()

# Data file을 변수에 할당
class setting:
    AGENCY = ''
    NEXT = ''
    NEWS_LIST = ''
    NUM = ''
    WRITED_DATE = ''
    GO_TO_MAIN_TEXT = ''
    TITLE = ''
    PAGE_CNT = 0
    PAGE_TEXT = ''
    UNRELATED_ANNOUNCEMENT = ''

    def __init__(self, agency) -> None:
        self.AGENCY = agency
        self.NEXT = data[agency]['NEXT']
        self.NEWS_LIST = data[agency]['NEWS_LIST']
        self.NUM = data[agency]['NUM']
        self.WRITED_DATE = data[agency]['WRITED_DATE']
        self.GO_TO_MAIN_TEXT = data[agency]['GO_TO_MAIN_TEXT']
        self.TITLE = data[agency]['TITLE']
        self.PAGE_CNT = data[agency]['PAGE_CNT']
        self.PAGE_TEXT = data[agency]['PAGE_TEXT']
        self.UNRELATED_ANNOUNCEMENT = data[agency]['UNRELATED_ANNOUNCEMENT']

# 크롤러 함수
def crawler(link):
    agency = switch(link)
    chrome_driver.get(link)
    
    chrome_driver.implicitly_wait(5)

    page_info = setting(agency)

    cnt = 1
    try:
        while chrome_driver.find_element_by_css_selector(page_info.NEXT):
            for _ in range(page_info.PAGE_CNT - 1):
                for i in range(len(chrome_driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT))):
                    crawling_info = get_values_to_page(page_info, i)
                    if crawling_info:
                        crawling_info['agency'] = agency

                        current_date = checking_current_date(crawling_info['writed_date'])
                        if current_date:
                            crawling_info['writed_date'] = current_date
                        else:
                            return

                        insert_sql(crawling_info)

                cnt += 1
                chrome_driver.implicitly_wait(5)
                try:
                    logging.info("Go to {0} page at {1} site...".format(cnt, agency))
                    chrome_driver.find_element_by_css_selector(page_info.PAGE_TEXT.format(cnt)).click()
                except selenium.common.exceptions.NoSuchElementException:
                    logging.debug("There is no page to click.")
                    return
            chrome_driver.find_element_by_css_selector(page_info.NEXT).click()
            cnt += 1

    except selenium.common.exceptions.WebDriverException:
        logging.warning("Cannot read Chrome Page")
        f.close()
        chrome_driver.quit()
        sys.exit()

    f.close()
    chrome_driver.quit()

# 어떤 기관의 링크인지 구별해주는 함수
def switch(link):
    for key in site_category.keys():
        if key in link:
            return site_category[key] + " 공고"

# 페이지에서 필요한 정보 크롤링
def get_values_to_page(page_info, i):
    if i < 0:
        logging.info("There is no item for iteration.")
        return False

    try:
        chrome_driver.implicitly_wait(5)
        news_list = chrome_driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT)
        unique_num = page_info.AGENCY + "_" + re.sub("\,|\"", "", news_list[i].find_element_by_css_selector(page_info.NUM).text)
        writed_date = news_list[i].find_element_by_css_selector(page_info.WRITED_DATE).text
        collected_date = datetime.today().date()

        chrome_driver.implicitly_wait(5)
        news_list[i].find_element_by_css_selector(page_info.GO_TO_MAIN_TEXT).click()
        title = chrome_driver.find_element_by_css_selector(page_info.TITLE).text
        hyperlink = chrome_driver.current_url
        chrome_driver.implicitly_wait(5)
        chrome_driver.back()

        chrome_driver.implicitly_wait(5)
    except IndexError:
        logging.warning("Cannot access homepage now")
        f.close()
        # chrome_driver.quit()
        sys.exit()

    return {
        'unique_num' : unique_num,
        'title': title,
        'writed_date' : writed_date,
        'collected_date' : collected_date,
        'hyperlink' : hyperlink
    }

# 데이터를 SQL DB에 insert
def insert_sql(crawling_info):
    try:
        print(crawling_info['title'])
        cursor.execute(sql, (crawling_info['unique_num'], crawling_info['title'], crawling_info['agency'], crawling_info['writed_date'], crawling_info['collected_date'], crawling_info['hyperlink']))
    except pymysql.err.IntegrityError:
        logging.debug("Already same primary key is exist!")
        pass
    except Exception:
        logging.warning("Cannot execute SQL Query!")
    finally:
        conn.commit()

# 현재 날짜로부터 특정 기간까지의 정보만을 수집
def checking_current_date(date):
    # 오늘 중에 등록된 글을 파싱하여 오늘의 날짜 값을 부여
    if ':' not in date:
        current_date = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        current_date = datetime.today().date()

    # 특정 날짜 이전의 소식들은 받지 않음.
    if current_date.year == 2021 and current_date.month < 9:
        return False
    return current_date



 