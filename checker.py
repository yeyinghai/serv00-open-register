# checker.py
import requests
import os
import re # 导入正则表达式模块
from bs4 import BeautifulSoup
import json

# --- 配置 (保持不变) ---
URL = 'https://www.serv00.com/'
BARK_KEY = os.getenv('BARK_KEY')
# BARK_SERVER_URL = os.getenv('BARK_SERVER_URL')
BARK_SERVER_URL = "https://nas.yeyhome.com:286"
def send_bark_notification(title, body, url_to_open):
    """通过 Bark 发送推送通知 (此函数无需改动)"""
    if not BARK_KEY:
        print("警告: Bark Key 未设置，跳过发送通知。")
        return
    
    api_url = f"{BARK_SERVER_URL}/{BARK_KEY}"
    payload = {
        "title": title,
        "body": body,
        "url": url_to_open,
        "group": "Serv00 Checker"
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        if response.json().get("code") == 200:
            print("Bark 推送通知已成功发送！")
        else:
            print(f"发送 Bark 通知失败: {response.text}")
    except Exception as e:
        print(f"发送 Bark 通知时发生错误: {e}")

def check_serv00_status():
    """
    检查 Serv00.com 的注册状态 (核心逻辑已更新)。
    """
    print(f"正在检查 URL: {URL} ...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- 全新的判断逻辑 ---

        # 1. 寻找包含账户信息的文本区域
        # 我们假设数字位于 "Accounts created on the server" 这段文字附近。
        # 首先，找到包含这段文字的标签。
        target_element = soup.find('div', class_='hero-content') # Serv00页面通常使用hero-content作为容器
        if not target_element:
            print("错误: 无法找到 class='hero-content' 的区域。网站结构可能已更改。")
            send_bark_notification("Serv00脚本错误", "无法找到hero-content，请检查脚本。", URL)
            return

        search_text = target_element.get_text(strip=True)

        # 2. 使用正则表达式从文本中提取 "数字 / 数字" 格式
        # 正则表达式 r'(\d+)\s*/\s*(\d+)' 会匹配 "123/456" 或 "123 / 456" 这样的格式
        match = re.search(r'(\d+)\s*/\s*(\d+)', search_text)
        
        if not match:
            print("错误: 找到了目标区域但无法提取账户数量。网站结构或文本格式可能已更改。")
            # 打印部分文本用于调试
            print(f"搜索区域文本片段: {search_text[:250]}...")
            send_bark_notification("Serv00脚本错误", "无法解析账户数量，请检查脚本。", URL)
            return

        # 3. 提取数字并进行比较
        current_accounts = int(match.group(1))
        max_accounts = int(match.group(2))
        
        print(f"状态: 已成功提取账户数量 -> {current_accounts} / {max_accounts}")

        # 核心判断：如果两个数字不相等 (通常是 current < max)，则说明有空位
        if current_accounts < max_accounts:
            print("判断: 注册已开放！(账户未满)")
            notification_title = "🎉 Serv00.com 注册开放!"
            notification_body = f"当前账户: {current_accounts} / {max_accounts}。有名额！"
            
            send_bark_notification(
                title=notification_title,
                body=notification_body,
                url_to_open=URL
            )
        else:
            print("判断: 注册已关闭。(账户数量已满或相等)")

    except requests.exceptions.RequestException as e:
        print(f"访问网站时发生网络错误: {e}")
        send_bark_notification("Serv00脚本错误", f"无法访问网站: {e}", URL)
    except Exception as e:
        # 捕获其他可能的错误，例如解析失败
        print(f"处理页面时发生未知错误: {e}")
        send_bark_notification("Serv00脚本严重错误", f"脚本执行时发生意外: {e}", URL)


if __name__ == "__main__":
    check_serv00_status()
