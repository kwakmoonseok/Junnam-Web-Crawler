import datetime
import json
import re
from os import close

import pymysql

import selenium
from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common.keys import Keys

with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

driver = webdriver.Chrome(executable_path='chromedriver.exe')

conn = pymysql.connect(host='localhost', user='root', password='1234', db='news', charset='utf8') 
cursor = conn.cursor() 
sql = "INSERT INTO junnam_news (title, num, agency, writed_date, collected_date, hyperlink) VALUES (%s, %s, %s, %s, %s, %s)" 

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

def crawler(link):
    agency = switch(link)
    driver.get(link)
    
    driver.implicitly_wait(5)

    page_info = setting(agency)

    cnt = 1

    while driver.find_element_by_css_selector(page_info.NEXT):
        for _ in range(page_info.PAGE_CNT - 1):
            for i in range(len(driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT))):
                crawling_info = get_values_to_page(page_info, i)
                crawling_info['agency'] = agency
                
                current_date = checking_current_date(crawling_info['writed_date'])
                if current_date:
                    crawling_info['writed_date'] = current_date
                else:
                    return
                
                insert_sql(crawling_info)
                
            cnt += 1
            driver.implicitly_wait(5)
            try:
                driver.find_element_by_css_selector(page_info.PAGE_TEXT.format(cnt)).click()
            except selenium.common.exceptions.NoSuchElementException:
                return
            
        driver.find_element_by_css_selector(page_info.NEXT).click()
        cnt += 1
    
    f.close()
    driver.quit()

def switch(link):
    site_category = { 'jcia' : "JCIA 공고", 'naju' : "나주 공고", 'jeonnam' : "전남 공고", 'mokpo' : "목포 공고", 'yeosu' : "여수 공고", 'suncheon' : "순천 공고", 'gwangyang' : "광양 공고" }
    for key in site_category.keys():
        if key in link:
            return site_category[key]

def get_values_to_page(page_info, i):
    if str(type(page_info)) != "<class '__main__.setting'>" or str(type(i)) != "<class 'int'>": 
        raise TypeError('parameter type is different origin type')

    news_list = driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT)
    num = int(re.sub("\,|\"", "", news_list[i].find_element_by_css_selector(page_info.NUM).text))
    writed_date = news_list[i].find_element_by_css_selector(page_info.WRITED_DATE).text
    collected_date = datetime.date.today()

    driver.implicitly_wait(5)
    news_list[i].find_element_by_css_selector(page_info.GO_TO_MAIN_TEXT).click()
    title = driver.find_element_by_css_selector(page_info.TITLE).text
    hyperlink = driver.current_url
    driver.implicitly_wait(5)
    driver.back()
        
    driver.implicitly_wait(5)

    return {
        'title': title,
        'num' : num,
        'writed_date' : writed_date,
        'collected_date' : collected_date,
        'hyperlink' : hyperlink
    }

def insert_sql(crawling_info):
    try:
        cursor.execute(sql, (crawling_info['title'], crawling_info['num'], crawling_info['agency'], crawling_info['writed_date'], crawling_info['collected_date'], crawling_info['hyperlink']))
    except pymysql.err.IntegrityError:
        pass
    conn.commit()

def checking_current_date(date):
    if date[:7] != '2021-09':
        if ':' in date:
            return datetime.date.today()
        return False
sites = [ "https://www.gwangyang.go.kr/board/list.gwangyang?boardId=BBS_0000004&menuCd=DOM_000000103001000000&contentsSid=227&cpath=", "https://www.suncheon.go.kr/kr/news/0001/0004/", "https://www.yeosu.go.kr/www/govt/news/notice", "https://www.mokpo.go.kr/www/open_administration/city_news/notice", "http://jcia.or.kr/cf/information/news.do", "https://www.naju.go.kr/www/administration/notice/financial", "https://www.jeonnam.go.kr/M7124/boardList.do?menuId=jeonnam0201000000"]
for site in sites:
    crawler(site)
driver.close()
