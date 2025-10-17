import requests
import os
import re
from bs4 import BeautifulSoup
import json

# --- 配置 ---
URL = 'https://www.serv00.com/'
BARK_KEY = os.getenv('BARK_KEY')
BARK_SERVER_URL = os.getenv('BARK_SERVER_URL', 'https://api.day.app') # 添加默认 Bark 服务器地址
# --- 新增配置 ---
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
    """从文件中读取上一次记录的账户数量"""
    try:
        if os.path.exists(LAST_VALUE_FILE):
            with open(LAST_VALUE_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return int(content)
    except (IOError, ValueError) as e:
        print(f"警告: 无法读取或解析旧的账户值文件 ({LAST_VALUE_FILE}): {e}")
    return None # 如果文件不存在、为空或内容无效，则返回 None

def update_last_known_accounts(value):
    """将新的账户数量写入文件"""
    try:
        with open(LAST_VALUE_FILE, 'w') as f:
            f.write(str(value))
        print(f"已将新值 {value} 更新到状态文件 {LAST_VALUE_FILE}")
    except IOError as e:
        print(f"错误: 无法写入状态文件: {e}")


def check_serv00_status():
    """
    检查 Serv00.com 的账户数量，并在数值变化时发送通知。
    """
    print(f"正在检查 URL: {URL} ...")
    
    # 1. 读取上一次记录的数值
    last_known_accounts = get_last_known_accounts()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 2. 提取当前网页上的数值 (这部分逻辑与你原有的基本一致)
        target_element = soup.find('div', class_='hero-accounts')
        if not target_element:
            print("错误: 无法找到 class='hero-accounts' 的区域。网站结构可能已更改。")
            send_bark_notification("Serv00脚本错误", "无法找到hero-accounts，请检查脚本。", URL)
            return

        search_text = target_element.get_text(strip=True)
        match = re.search(r'(\d+)\s*/\s*(\d+)', search_text)
        
        if not match:
            print("错误: 找到了目标区域但无法提取账户数量。网站结构或文本格式可能已更改。")
            send_bark_notification("Serv00脚本错误", "无法解析账户数量，请检查脚本。", URL)
            return

        current_accounts = int(match.group(1))
        max_accounts = int(match.group(2))
        
        print(f"状态: 成功提取到当前值 -> {current_accounts} / {max_accounts}")
        if last_known_accounts is not None:
             print(f"记录: 上一次记录的值 -> {last_known_accounts}")
        else:
             print(f"记录: 这是第一次运行，无历史记录。")

        # 3. 核心比较逻辑
        if last_known_accounts is None:
            # 首次运行，只记录数值，不发送通知
            print("首次运行，正在记录初始值...")
            update_last_known_accounts(current_accounts)
            # (可选) 如果你希望首次运行时也发送通知，可以取消下面这行注释
            # send_bark_notification("Serv00监控已启动", f"已记录初始账户数量: {current_accounts}", URL)

        elif current_accounts != last_known_accounts:
            # 数值发生了变化！
            print("!!! 数值发生变化 !!!")
            notification_title = "Serv00 账户数量发生变化！"
            notification_body = f"账户数量从 {last_known_accounts} 变为 {current_accounts}。\n总限额: {max_accounts}。"
            
            send_bark_notification(
                title=notification_title,
                body=notification_body,
                url_to_open=URL
            )
            # 更新文件中的值为最新值
            update_last_known_accounts(current_accounts)
            
        else:
            # 数值未变
            print("判断: 数值未发生变化。")

    except requests.exceptions.RequestException as e:
        print(f"访问网站时发生网络错误: {e}")
        send_bark_notification("Serv00脚本错误", f"无法访问网站: {e}", URL)
    except Exception as e:
        print(f"处理页面时发生未知错误: {e}")
        send_bark_notification("Serv00脚本严重错误", f"脚本执行时发生意外: {e}", URL)


if __name__ == "__main__":
    check_serv00_status()
