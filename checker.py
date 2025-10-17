import requests
import os
import re # 重新启用正则表达式
import json
import time

# 导入 Selenium 相关库
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# --- 配置 ---
URL = 'https://www.serv00.com/' # 我们要访问的主页
BARK_KEY = os.getenv('BARK_KEY')
BARK_SERVER_URL = os.getenv('BARK_SERVER_URL', 'https://api.day.app')

# --- 辅助函数 (无需修改) ---
def send_bark_notification(title, body, url_to_open):
    if not BARK_KEY:
        print("警告: Bark Key 未设置，跳过发送通知。")
        return
    api_url = f"{BARK_SERVER_URL}/{BARK_KEY}"
    payload = {"title": title, "body": body, "url": url_to_open, "group": "Serv00 Checker"}
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        if response.json().get("code") == 200:
            print("Bark 推送通知已成功发送！")
        else:
            print(f"发送 Bark 通知失败: {response.text}")
    except Exception as e:
        print(f"发送 Bark 通知时发生错误: {e}")

# --- 核心函数 (全新 Selenium 版本) ---
def check_serv00_status():
    """
    使用 Selenium 驱动一个真实的浏览器来加载页面，
    等待JavaScript执行完毕后，直接从页面读取渲染后的内容。
    """
    print("正在初始化无头浏览器...")
    
    # 设置Chrome浏览器选项
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式，不在屏幕上显示浏览器窗口
    options.add_argument('--no-sandbox') # 在Linux/Docker环境中运行时需要
    options.add_argument('--disable-dev-shm-usage') # 解决一些资源限制问题
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
    
    # 使用 webdriver-manager 自动安装和配置ChromeDriver
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print(f"浏览器启动成功，正在访问: {URL} ...")
        driver.get(URL)
        
        # --- 最关键的一步：等待 ---
        # 等待包含数字的元素加载出来，并变得可见。
        # 我们等待那个 <strong> 标签，因为它直接包含了 "数字 / 数字"
        # 最长等待时间为20秒
        print("页面加载中，等待JavaScript渲染账户数量...")
        wait = WebDriverWait(driver, 20)
        # 使用CSS选择器定位元素，这个定位非常精确
        target_element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.hero-accounts strong"))
        )
        print("目标元素已成功加载！")
        
        # 提取渲染后的文本内容
        rendered_text = target_element.text
        print(f"成功提取到文本: '{rendered_text}'")
        
        # 使用你最初的正则表达式来匹配 "数字 / 数字"
        match = re.search(r'(\d+)\s*/\s*(\d+)', rendered_text)
        
        if not match:
            print("错误: 成功定位元素，但无法从文本中解析出账户数量。")
            send_bark_notification("Serv00脚本错误", f"无法解析文本: {rendered_text}", URL)
            return

        current_accounts = int(match.group(1))
        max_accounts = int(match.group(2))
        
        print(f"状态: 成功解析出账户数量 -> {current_accounts} / {max_accounts}")

        # 核心判断逻辑：如果两个数字不相等，则说明有空位
        if current_accounts < max_accounts:
            print("判断: 注册已开放！(账户未满)")
            notification_title = "🎉 Serv00.com 注册开放!"
            notification_body = f"当前账户: {current_accounts} / {max_accounts}。有名额！"
            send_bark_notification(title=notification_title, body=notification_body, url_to_open=URL)
        else:
            print("判断: 注册已关闭。(账户已满)")
            notification_title = "🎉 Serv00.com 注册未开放!"
            send_bark_notification(title=notification_title)
    except TimeoutException:
        print("错误: 等待元素超时。页面可能未正常加载，或元素结构已改变。")
        send_bark_notification("Serv00脚本错误", "等待页面元素超时，请检查脚本。", URL)
    except Exception as e:
        print(f"发生未知错误: {e}")
        send_bark_notification("Serv00脚本严重错误", f"脚本执行时发生意外: {e}", URL)
    finally:
        if driver:
            print("正在关闭浏览器...")
            driver.quit()

if __name__ == "__main__":
    check_serv00_status()
