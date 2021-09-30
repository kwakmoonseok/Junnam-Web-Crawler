from os import close
import re
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pymysql
import datetime 
import json

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
    if 'jcia' in link:
        agency = "JCIA 공고"
    elif 'naju' in link:
        agency = "나주 공고"
    elif 'jeonnam' in link:
        agency = "전남 공고"
    elif 'mokpo' in link:
        agency = "목포 공고"
    
    driver.get(link)
    
    driver.implicitly_wait(5)

    page_info = setting(agency)

    cnt = 1
    while driver.find_element_by_css_selector(page_info.NEXT):
        for _ in range(page_info.PAGE_CNT - 1):
            for i in range(len(driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT))):
                title, num, writed_date, collected_date, hyperlink = get_values_to_page(page_info, i)
                
                print(writed_date)
                if writed_date[:7] != '2021-09':
                    if ':' in writed_date:
                        writed_date = datetime.date.today()
                    else:
                        return

                try:
                    cursor.execute(sql, (title, num, agency, writed_date, collected_date, hyperlink))
                except pymysql.err.IntegrityError:
                    pass
                conn.commit()

                print(title) #debug
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

def get_values_to_page(page_info, i):
    if str(type(page_info)) != "<class '__main__.setting'>" or str(type(i)) != "<class 'int'>": 
        raise TypeError('parameter type is different origin type')

    news_list = driver.find_elements_by_css_selector(page_info.NEWS_LIST + page_info.UNRELATED_ANNOUNCEMENT)
    num = int(re.sub("\,", "", news_list[i].find_element_by_css_selector(page_info.NUM).text))
    writed_date = news_list[i].find_element_by_css_selector(page_info.WRITED_DATE).text
    collected_date = datetime.date.today()

    
    driver.implicitly_wait(5)
    news_list[i].find_element_by_css_selector(page_info.GO_TO_MAIN_TEXT).click()
    title = driver.find_element_by_css_selector(page_info.TITLE).text
    hyperlink = driver.current_url
    driver.implicitly_wait(5)
    driver.back()
        
    driver.implicitly_wait(5)

    return title, num, writed_date, collected_date, hyperlink
            
links = [ "https://www.mokpo.go.kr/www/open_administration/city_news/notice", "http://jcia.or.kr/cf/information/news.do", "https://www.naju.go.kr/www/administration/notice/financial", "https://www.jeonnam.go.kr/M7124/boardList.do?menuId=jeonnam0201000000"]
for link in links:
    crawler(link)
