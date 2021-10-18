import webcrawler
import schedule
import time

def start():
    webcrawler.main()

schedule.every().day.at("11:45").do(start)
while True:
    schedule.run_pending()
    time.sleep(60)

