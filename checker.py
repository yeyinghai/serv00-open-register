import requests
import os
import json

# --- 配置 ---
API_URL = 'https://panel.serv00.com/api/stats' 
# API所在的面板主域，我们必须先访问它来获取正确的Cookie
PANEL_URL = 'https://panel.serv00.com/' 
# 主页URL仍用于伪造Referer头
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

# --- 核心函数 (最终版：解决跨域Cookie问题) ---
def check_serv00_status():
    """
    终极解决方案：
    1. 访问 API 所在的域 (panel.serv00.com) 以获取其专属的会话Cookie。
    2. 带着这个正确的Cookie，并伪造Referer头，去访问API。
    """
    print("正在初始化会话...")
    
    last_known_accounts = get_last_known_accounts()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }
    
    with requests.Session() as s:
        s.headers.update(headers)
        
        try:
            # --- 步骤 1: 访问面板主域，获取 panel.serv00.com 的专属Cookie ---
            print(f"正在访问面板域 {PANEL_URL} 以获取正确的会话Cookie...")
            s.get(PANEL_URL, timeout=10).raise_for_status()
            print("面板域访问成功，专属Cookie已自动存储。")

            # --- 步骤 2: 带着正确的Cookie访问API ---
            print(f"正在请求 API: {API_URL} ...")
            # 伪造一个看起来合法的Referer头，让服务器以为我们是从主页过来的
            api_headers = {'Referer': HOME_URL} 
            response = s.get(API_URL, headers=api_headers, timeout=10)
            
            response.raise_for_status()
            data = response.json()

            # 数据提取和比较逻辑 (无需修改)
            if 'accounts' not in data or 'total' not in data['accounts'] or 'limit' not in data['accounts']:
                print(f"错误: API返回的数据格式不正确。收到的数据: {data}")
                send_bark_notification("Serv00脚本错误", "API数据格式有误。", HOME_URL)
                return

            current_accounts = int(data['accounts']['total'])
            max_accounts = int(data['accounts']['limit'])

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
                send_bark_notification(title=notification_title, body=notification_body, url_to_open=HOME_URL)
                update_last_known_accounts(current_accounts)
                
            else:
                print("判断: 数值未发生变化。")

        except requests.exceptions.RequestException as e:
            print(f"访问时发生网络错误: {e}")
            send_bark_notification("Serv00脚本错误", f"无法访问网站或API: {e}", HOME_URL)
        except json.JSONDecodeError:
            print(f"错误: 无法解析API返回的JSON数据。服务器响应: {response.text}")
            send_bark_notification("Serv00脚本错误", "API未返回有效的JSON数据。", HOME_URL)
        except Exception as e:
            print(f"处理数据时发生未知错误: {e}")
            send_bark_notification("Serv00脚本严重错误", f"脚本执行时发生意外: {e}", HOME_URL)

if __name__ == "__main__":
    check_serv00_status()
