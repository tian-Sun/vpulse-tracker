from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime
import os

class VPulseCrawler:
    def __init__(self):
        # 设置 Chrome 选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 启用无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速
        chrome_options.add_argument('--disable-images')  # 禁用图片加载
        chrome_options.add_argument('--disable-javascript')  # 禁用JavaScript
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 初始化浏览器
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"初始化 Chrome 失败: {str(e)}")
            print("尝试使用系统 Chrome...")
            chrome_options.binary_location = "/usr/bin/google-chrome-stable"
            self.driver = webdriver.Chrome(options=chrome_options)
            
        self.wait = WebDriverWait(self.driver, 10)  # 减少等待时间
        
    def scroll_to_load(self):
        """滚动页面以加载更多内容"""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # 减少等待时间
        except Exception as e:
            print(f"滚动页面时出错: {str(e)}")
        
    def get_top10_data(self):
        """获取 Top10 数据"""
        try:
            # 访问网站
            print("正在访问网站...")
            self.driver.get("https://site.v-pulse.com/zh_cn")
            time.sleep(3)  # 减少等待时间
            
            # 等待页面加载完成
            print("等待页面加载...")
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rank_wrap")))
            except Exception as e:
                print(f"等待rank_wrap加载失败: {str(e)}")
                return None
                
            print("开始滚动页面...")
            self.scroll_to_load()  # 简化滚动逻辑
            
            # 获取明星和电视剧数据
            print("查找排行榜区域...")
            sections = self.driver.find_elements(By.CLASS_NAME, "rank_wrap")
            
            if len(sections) < 2:
                print("错误：未找到足够的排行榜区域")
                return None
                
            data = {
                "artists": self._extract_section_data(sections[0], "明星"),
                "dramas": self._extract_section_data(sections[1], "连续剧"),
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return data
            
        except Exception as e:
            print(f"获取数据时出错: {str(e)}")
            return None
            
    def _extract_section_data(self, section, section_type):
        """提取每个部分的数据"""
        items = []
        try:
            print(f"\n开始提取{section_type}数据...")
            # 使用更精确的选择器
            cards = section.find_elements(By.CLASS_NAME, "item-pc")
            print(f"找到 {len(cards)} 个{section_type}卡片")
            
            for index, card in enumerate(cards[:10]):  # 只获取前10个
                try:
                    print(f"正在处理第 {index + 1} 个{section_type}...")
                    # 获取排名标签
                    rank_tag = card.find_element(By.CLASS_NAME, "item_rank").text
                    print(f"排名标签: {rank_tag}")
                    
                    # 获取名字 - 电视剧使用 text-two-lines，明星使用 text-single-line
                    class_name = "text-two-lines" if section_type == "连续剧" else "text-single-line"
                    try:
                        name_element = card.find_element(By.CLASS_NAME, class_name)
                        name = name_element.text.strip()
                        print(f"名称: {name}")
                    except Exception as e:
                        print(f"获取名称失败 ({class_name}): {str(e)}")
                        # 尝试另一个类名
                        alt_class = "text-single-line" if section_type == "连续剧" else "text-two-lines"
                        try:
                            name_element = card.find_element(By.CLASS_NAME, alt_class)
                            name = name_element.text.strip()
                            print(f"使用备选类名获取名称成功: {name}")
                        except Exception as e2:
                            print(f"备选类名也失败: {str(e2)}")
                            continue
                    
                    # 获取全球和中国排名
                    vs_items = card.find_elements(By.CLASS_NAME, "vs_item")
                    if len(vs_items) < 2:
                        print(f"警告：未找到足够的排名信息 (找到 {len(vs_items)} 个)")
                        continue
                        
                    global_rank = vs_items[0].find_element(By.CLASS_NAME, "vs_item_bottom").text
                    china_rank = vs_items[1].find_element(By.CLASS_NAME, "vs_item_bottom").text.strip()
                    print(f"全球排名: {global_rank}, 中国排名: {china_rank}")
                    
                    items.append({
                        "rank": rank_tag,
                        "name": name,
                        "global_rank": global_rank,
                        "china_rank": china_rank
                    })
                    
                except Exception as e:
                    print(f"处理{section_type}卡片时出错: {str(e)}")
                    print("详细错误信息:")
                    print(traceback.format_exc())
                    continue
                    
        except Exception as e:
            print(f"提取{section_type}数据时出错: {str(e)}")
            print("详细错误信息:")
            print(traceback.format_exc())
            
        if not items:
            print(f"警告：没有获取到任何{section_type}数据")
            # 保存页面源码以供调试
            with open(f"debug_{section_type}_page.html", "w", encoding="utf-8") as f:
                f.write(section.get_attribute('outerHTML'))
            print(f"已保存{section_type}页面源码到 debug_{section_type}_page.html")
            
        return items
        
    def save_data(self, data):
        """保存数据到文件"""
        if not data:
            return
            
        # 创建数据目录
        if not os.path.exists("data"):
            os.makedirs("data")
            
        today = datetime.now().strftime('%Y%m%d')
        
        # 读取历史数据
        history_file = "data/v_pulse_history.json"
        history_data = {}
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        
        # 更新历史数据
        history_data[today] = {
            "artists": [{
                "name": item["name"],
                "rank": item["rank"]
            } for item in data["artists"]],
            "dramas": [{
                "name": item["name"],
                "rank": item["rank"]
            } for item in data["dramas"]],
            "crawl_time": data["crawl_time"]
        }
        
        # 保存历史数据
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
            
        # 生成HTML页面
        self._generate_html_report(history_data)
            
    def _generate_html_report(self, history_data):
        """生成HTML报告"""
        html_template = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>V-Pulse 排行榜历史记录</title>
            <style>
                body {{
                    font-family: 'Microsoft YaHei', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                    position: relative;
                }}
                .header-container {{
                    position: relative;
                    margin-bottom: 40px;
                }}
                .last-update {{
                    position: absolute;
                    top: 0;
                    right: 0;
                    color: #666;
                    font-size: 14px;
                    background-color: #fff;
                    padding: 8px 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin: 0;
                    padding: 20px 0;
                    font-size: 32px;
                    font-weight: 600;
                }}
                .section {{
                    background-color: white;
                    border-radius: 15px;
                    padding: 25px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                    overflow-x: auto;
                }}
                h2 {{
                    color: #34495e;
                    margin-bottom: 25px;
                    padding-bottom: 15px;
                    border-bottom: 2px solid #eee;
                    font-size: 24px;
                    font-weight: 500;
                }}
                table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    margin-bottom: 20px;
                }}
                th, td {{
                    padding: 15px;
                    text-align: center;
                    border: 1px solid #eee;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: 600;
                    color: #2c3e50;
                    border-bottom: 2px solid #ddd;
                }}
                tr:hover {{
                    background-color: #f8f9fa;
                }}
                td {{
                    color: #34495e;
                }}
                .rank-up {{
                    color: #2ecc71;
                    font-weight: bold;
                }}
                .rank-down {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .rank-same {{
                    color: #95a5a6;
                }}
                .trend {{
                    font-size: 14px;
                    margin-left: 5px;
                }}
                .date-header {{
                    font-size: 16px;
                    color: #2c3e50;
                    font-weight: 500;
                }}
                .name-cell {{
                    text-align: left;
                    font-weight: 500;
                    color: #2c3e50;
                    padding-left: 20px;
                }}
                .rank-cell {{
                    font-weight: 600;
                    width: 100px;
                    background-color: #ffffff;
                }}
                tr:nth-child(even) {{
                    background-color: #f9fafb;
                }}
                .section:hover {{
                    box-shadow: 0 6px 12px rgba(0,0,0,0.08);
                    transition: box-shadow 0.3s ease;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header-container">
                    <h1>V-Pulse 排行榜历史记录</h1>
                    <div class="last-update">最近更新时间：{last_update}</div>
                </div>
                <div class="section">
                    <h2>明星排行榜</h2>
                    {artists_table}
                </div>
                <div class="section">
                    <h2>电视剧排行榜</h2>
                    {dramas_table}
                </div>
            </div>
        </body>
        </html>
        """
        
        def generate_rank_table(data_type):
            # 获取最近7天的数据
            sorted_dates = sorted(history_data.keys(), reverse=True)[:7]
            if not sorted_dates:
                return "<p>暂无数据</p>"
            
            # 反转日期顺序，使最近的日期在最右边
            sorted_dates = sorted_dates[::-1]
            
            # 获取所有出现过的名字
            all_names = set()
            for date in sorted_dates:
                all_names.update(item["name"] for item in history_data[date][data_type])
            
            # 生成表头
            content = "<table>"
            content += "<tr><th>名称</th>"
            for date in sorted_dates:
                # 只显示月份和日期
                formatted_date = f"{date[4:6]}-{date[6:]}"
                content += f"<th><div class='date-header'>{formatted_date}</div></th>"
            content += "</tr>"
            
            # 为每个名字生成一行数据
            for name in sorted(all_names):
                content += f"<tr><td class='name-cell'>{name}</td>"
                
                prev_rank = None
                for date in sorted_dates:
                    # 查找当天该名字的排名
                    rank_data = next((item for item in history_data[date][data_type] if item["name"] == name), None)
                    
                    if rank_data:
                        current_rank = int(rank_data["rank"].replace("TOP ", ""))
                        trend = ""
                        if prev_rank is not None:
                            if current_rank > prev_rank:
                                trend = "<span class='trend rank-down'>↓</span>"  # 数字变大，排名下降
                            elif current_rank < prev_rank:
                                trend = "<span class='trend rank-up'>↑</span>"    # 数字变小，排名上升
                            else:
                                trend = "<span class='trend rank-same'>-</span>"
                        prev_rank = current_rank
                        content += f"<td class='rank-cell'>TOP {current_rank}{trend}</td>"
                    else:
                        content += "<td>-</td>"
                        prev_rank = None
                
                content += "</tr>"
            
            content += "</table>"
            return content
        
        # 获取最近的运行时间
        latest_date = max(history_data.keys())
        latest_time = history_data[latest_date]["crawl_time"]

        # 生成 HTML 内容
        html_content = html_template.format(
            last_update=latest_time,
            artists_table=generate_rank_table("artists"),
            dramas_table=generate_rank_table("dramas")
        )
        
        # 保存HTML文件
        html_filename = "data/v_pulse_report.html"
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML报告已生成：{html_filename}")
        print(f"最近更新时间：{latest_time}")
            
    def close(self):
        """关闭浏览器"""
        self.driver.quit()

def main():
    crawler = VPulseCrawler()
    try:
        data = crawler.get_top10_data()
        if data:
            crawler.save_data(data)
            print("数据爬取成功！")
        else:
            print("数据爬取失败！")
    finally:
        crawler.close()

if __name__ == "__main__":
    main() 