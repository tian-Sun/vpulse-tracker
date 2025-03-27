import time
from v_pulse_crawler import main as crawler_main

def run():
    print(f"开始执行爬虫任务 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    crawler_main()
    print(f"爬虫任务完成 - {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run() 