import requests
import os
import json

# --- 配置 ---
API_URL = 'https://panel.serv00.com/api/stats' 
HOME_URL = 'https://www.serv00.com/' 

BARK_KEY = os.getenv('BARK_KEY')
BARK_SERVER_URL = os.getenv('BARK_SERVER_URL', 'https://api.day.app')
LAST_VALUE_FILE = 'last_accounts.txt'

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

# --- 核心函数 (已更新请求头) ---
def check_serv00_status():
    """
    请求正确的 Serv00 数据 API，并使用完整的浏览器请求头来绕过服务器检测。
    """
    print(f"正在请求 API: {API_URL} ...")
    
    last_known_accounts = get_last_known_accounts()
    
    # --- 全新的、更完整的请求头，伪装成从Chrome浏览器发出的请求 ---
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://www.serv00.com',
        'Referer': 'https://www.serv00.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(API_URL, headers=headers, timeout=10)
        # 检查响应状态码，如果是500，就打印更详细的信息
        if response.status_code == 500:
            print(f"错误: 服务器返回 500 Internal Server Error。这通常是请求头不被接受导致的。")
            print(f"服务器响应内容: {response.text[:500]}...") # 打印部分响应内容帮助调试
            send_bark_notification("Serv00脚本错误", "服务器返回500错误，可能需要更新请求头。", HOME_URL)
            return
            
        response.raise_for_status() # 如果不是2xx成功状态码，则抛出异常
        
        data = response.json()

        # 数据提取逻辑 (与上一版相同)
        if 'accounts' not in data or 'total' not in data['accounts'] or 'limit' not in data['accounts']:
            print(f"错误: API返回的数据格式不正确。收到的数据: {data}")
            send_bark_notification("Serv00脚本错误", "API数据格式有误，请检查脚本。", HOME_URL)
            return

        current_accounts = int(data['accounts']['total'])
        max_accounts = int(data['accounts']['limit'])

        # 比较逻辑 (与上一版相同)
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
                url_to_open=HOME_URL
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
