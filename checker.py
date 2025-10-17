import requests
import os
from bs4 import BeautifulSoup
import json

# --- 配置 ---
URL = 'https://www.serv00.com/'
BARK_KEY = os.getenv('BARK_KEY')
BARK_SERVER_URL = os.getenv('BARK_SERVER_URL', 'https://api.day.app')
# 用于存储上一次检测到的账户数量的文件名
LAST_VALUE_FILE = 'last_accounts.txt'

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

def get_last_known_accounts():
    """从文件中读取上一次记录的账户数量 (此函数无需改动)"""
    try:
        if os.path.exists(LAST_VALUE_FILE):
            with open(LAST_VALUE_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return int(content)
    except (IOError, ValueError) as e:
        print(f"警告: 无法读取或解析旧的账户值文件 ({LAST_VALUE_FILE}): {e}")
    return None

def update_last_known_accounts(value):
    """将新的账户数量写入文件 (此函数无需改动)"""
    try:
        with open(LAST_VALUE_FILE, 'w') as f:
            f.write(str(value))
        print(f"已将新值 {value} 更新到状态文件 {LAST_VALUE_FILE}")
    except IOError as e:
        print(f"错误: 无法写入状态文件: {e}")


def check_serv00_status():
    """
    检查 Serv00.com 的账户数量，并在数值变化时发送通知。
    (核心数据提取逻辑已更新)
    """
    print(f"正在检查 URL: {URL} ...")
    
    last_known_accounts = get_last_known_accounts()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- 全新的、更可靠的数据提取逻辑 ---

        # 1. 直接查找包含特定 'data-accounts' 属性的 <span> 标签
        account_span = soup.find('span', attrs={'data-accounts': ''})
        limit_span = soup.find('span', attrs={'data-limit': ''})

        # 2. 检查是否成功找到了这两个标签
        if not account_span or not limit_span:
            print("错误: 无法在页面上找到 'data-accounts' 或 'data-limit' 标签。网站结构可能已更改。")
            send_bark_notification("Serv00脚本错误", "无法找到数据标签，请检查脚本。", URL)
            return

        # 3. 从标签中提取文本并转换为数字
        try:
            current_accounts = int(account_span.get_text(strip=True))
            max_accounts = int(limit_span.get_text(strip=True))
        except (ValueError, TypeError):
            print(f"错误: 成功找到标签，但无法将内容解析为数字。账户内容: '{account_span.get_text()}', 限额内容: '{limit_span.get_text()}'")
            send_bark_notification("Serv00脚本错误", "无法将标签内容解析为数字。", URL)
            return
        
        # --- 比较逻辑 (保持不变) ---
        
        print(f"状态: 成功提取到当前值 -> {current_accounts} / {max_accounts}")
        if last_known_accounts is not None:
             print(f"记录: 上一次记录的值 -> {last_known_accounts}")
        else:
             print(f"记录: 这是第一次运行，无历史记录。")

        if last_known_accounts is None:
            print("首次运行，正在记录初始值...")
            update_last_known_accounts(current_accounts)

        elif current_accounts != last_known_accounts:
            print("!!! 数值发生变化 !!!")
            notification_title = "Serv00 账户数量发生变化！"
            notification_body = f"账户数量从 {last_known_accounts} 变为 {current_accounts}。\n总限额: {max_accounts}。"
            
            send_bark_notification(
                title=notification_title,
                body=notification_body,
                url_to_open=URL
            )
            update_last_known_accounts(current_accounts)
            
        else:
            print("判断: 数值未发生变化。")

    except requests.exceptions.RequestException as e:
        print(f"访问网站时发生网络错误: {e}")
        send_bark_notification("Serv00脚本错误", f"无法访问网站: {e}", URL)
    except Exception as e:
        print(f"处理页面时发生未知错误: {e}")
        send_bark_notification("Serv00脚本严重错误", f"脚本执行时发生意外: {e}", URL)


if __name__ == "__main__":
    check_serv00_status()
