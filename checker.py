import requests
import os
import json # json库是处理这种数据的标准库

# --- 配置 ---
# 我们将直接请求API，而不是主页
API_URL = 'https://www.serv00.com/freeweb/accounts' 
# 主页URL仍用于通知中的跳转链接
HOME_URL = 'https://www.serv00.com/' 

BARK_KEY = os.getenv('BARK_KEY')
BARK_SERVER_URL = os.getenv('BARK_SERVER_URL', 'https://api.day.app')
LAST_VALUE_FILE = 'last_accounts.txt'

# send_bark_notification, get_last_known_accounts, update_last_known_accounts
# 这三个辅助函数保持不变，无需修改
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

def get_last_known_accounts():
    try:
        if os.path.exists(LAST_VALUE_FILE):
            with open(LAST_VALUE_FILE, 'r') as f:
                content = f.read().strip()
                if content: return int(content)
    except (IOError, ValueError) as e:
        print(f"警告: 无法读取或解析旧的账户值文件 ({LAST_VALUE_FILE}): {e}")
    return None

def update_last_known_accounts(value):
    try:
        with open(LAST_VALUE_FILE, 'w') as f:
            f.write(str(value))
        print(f"已将新值 {value} 更新到状态文件 {LAST_VALUE_FILE}")
    except IOError as e:
        print(f"错误: 无法写入状态文件: {e}")

# --- 核心函数已重写 ---
def check_serv00_status():
    """
    直接请求 Serv00 的数据 API，检查账户数量变化。
    这种方法更稳定、更高效。
    """
    print(f"正在请求 API: {API_URL} ...")
    
    last_known_accounts = get_last_known_accounts()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': HOME_URL # 加上Referer头，模拟是主页发起的请求，更保险
    }
    
    try:
        # 1. 请求API并获取JSON数据
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json() # 直接将返回的JSON字符串解析为Python字典

        # 2. 从字典中提取数值
        # 确保API返回的数据包含我们需要的键
        if 'accounts' not in data or 'limit' not in data:
            print(f"错误: API返回的数据格式不正确。收到的数据: {data}")
            send_bark_notification("Serv00脚本错误", "API数据格式有误，请检查脚本。", HOME_URL)
            return

        current_accounts = int(data['accounts'])
        max_accounts = int(data['limit'])

        # --- 比较逻辑 (保持不变) ---
        print(f"状态: 成功从API获取到当前值 -> {current_accounts} / {max_accounts}")
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
                url_to_open=HOME_URL # 跳转链接使用主页URL
            )
            update_last_known_accounts(current_accounts)
            
        else:
            print("判断: 数值未发生变化。")

    except requests.exceptions.RequestException as e:
        print(f"访问API时发生网络错误: {e}")
        send_bark_notification("Serv00脚本错误", f"无法访问API: {e}", HOME_URL)
    except json.JSONDecodeError:
        print(f"错误: 无法解析API返回的JSON数据。服务器响应: {response.text}")
        send_bark_notification("Serv00脚本错误", "API未返回有效的JSON数据。", HOME_URL)
    except Exception as e:
        print(f"处理数据时发生未知错误: {e}")
        send_bark_notification("Serv00脚本严重错误", f"脚本执行时发生意外: {e}", HOME_URL)

if __name__ == "__main__":
    check_serv00_status()
