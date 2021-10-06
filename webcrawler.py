from datetime import datetime
import json
import re
import logging
import pymysql

import selenium
from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common.keys import Keys

# data 불러오기
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chrome_driver = webdriver.Chrome(executable_path='chromedriver.exe')

# SQL Connection
conn = pymysql.connect(host='localhost', user='root', password='1234', db='news', charset='utf8') 
cursor = conn.cursor() 
sql = "INSERT INTO junnam_news (title, num, agency, writed_date, collected_date, hyperlink) VALUES (%s, %s, %s, %s, %s, %s)" 

site_category = { 'jcia' : "JCIA 공고", 'naju' : "나주 공고", 'jeonnam' : "전남 공고", 'mokpo' : "목포 공고", 'yeosu' : "여수 공고", 'suncheon' : "순천 공고", 'gwangyang' : "광양 공고" }

def main():
    sites = {
        "광양" : "https://www.gwangyang.go.kr/board/list.gwangyang?boardId=BBS_0000004&menuCd=DOM_000000103001000000&contentsSid=227&cpath=", 
        "순천" : "https://www.suncheon.go.kr/kr/news/0001/0004/", 
        "여수" : "https://www.yeosu.go.kr/www/govt/news/notice", 
        "목포" : "https://www.mokpo.go.kr/www/open_administration/city_news/notice", 
        "JUIA" : "http://jcia.or.kr/cf/information/news.do", 
        "나주" : "https://www.naju.go.kr/www/administration/notice/financial", 
        "전남" : "https://www.jeonnam.go.kr/M7124/boardList.do?menuId=jeonnam0201000000"
    }

    for site in sites.values():
        crawler(site)


# Data file을 변수에 할당
class setting:
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

    while chrome_driver.find_element_by_css_selector(page_info.NEXT):
        for _ in range(page_info.PAGE_CNT - 1):
            for i in range(len(chrome_driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT))):
                crawling_info = get_values_to_page(page_info, i)
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
                logging.info("Go to {0} page...".format(cnt))
                chrome_driver.find_element_by_css_selector(page_info.PAGE_TEXT.format(cnt)).click()
            except selenium.common.exceptions.NoSuchElementException:
                logging.debug("There is no page to click.")
                return
            
        chrome_driver.find_element_by_css_selector(page_info.NEXT).click()
        cnt += 1
    
    f.close()
    chrome_driver.quit()

# 어떤 기관의 링크인지 구별해주는 함수
def switch(link):
    for key in site_category.keys():
        if key in link:
            return site_category[key]

# 페이지에서 필요한 정보 크롤링
def get_values_to_page(page_info, i):
    if str(type(page_info)) != "<class '__main__.setting'>" or str(type(i)) != "<class 'int'>": 
        raise TypeError('parameter type is different origin type')

    news_list = chrome_driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT)
    num = int(re.sub("\,|\"", "", news_list[i].find_element_by_css_selector(page_info.NUM).text))
    writed_date = news_list[i].find_element_by_css_selector(page_info.WRITED_DATE).text
    collected_date = datetime.date.today()

    chrome_driver.implicitly_wait(5)
    news_list[i].find_element_by_css_selector(page_info.GO_TO_MAIN_TEXT).click()
    title = chrome_driver.find_element_by_css_selector(page_info.TITLE).text
    hyperlink = chrome_driver.current_url
    chrome_driver.implicitly_wait(5)
    chrome_driver.back()
        
    chrome_driver.implicitly_wait(5)

    return {
        'title': title,
        'num' : num,
        'writed_date' : writed_date,
        'collected_date' : collected_date,
        'hyperlink' : hyperlink
    }

# 데이터를 SQL DB에 insert
def insert_sql(crawling_info):
    try:
        logging.info("Executing SQL Query....")
        cursor.execute(sql, (crawling_info['title'], crawling_info['num'], crawling_info['agency'], crawling_info['writed_date'], crawling_info['collected_date'], crawling_info['hyperlink']))
    except pymysql.err.IntegrityError:
        logging.debug("Already duplicate title is exist!")
        pass
    except:
        logging.warning("Cannot execute SQL Query! Check about data or SQL Connection.")
        
    conn.commit()

# 현재 날짜로부터 특정 기간까지의 정보만을 수집
def checking_current_date(date):
    current_date = datetime.strptime(date, "%Y-%m-%d")
    if current_date.year != 2021 and current_date.month != 9:
        if ':' in date:
            return datetime.date.today()
        return False

if __name__ == '__main__':
    main()


 