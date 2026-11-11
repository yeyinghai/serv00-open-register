import os
import sys
import json

import requests

# --- 配置 ---
URL = 'https://www.serv00.com/'            # 通知里点开的页面
COUNT_API = 'https://count.serv00.com/'    # 官网首页 JS 读取账户数量的接口，返回 {"limit": ..., "accounts": ...}
BARK_KEY = os.getenv('BARK_KEY')
BARK_SERVER_URL = (os.getenv('BARK_SERVER_URL') or 'https://api.day.app').rstrip('/')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Origin': 'https://www.serv00.com',
    'Referer': 'https://www.serv00.com/',
}


def send_bark_notification(title, body, url_to_open):
    if not BARK_KEY:
        print("警告: Bark Key 未设置，跳过发送通知。")
        return False
    api_url = f"{BARK_SERVER_URL}/{BARK_KEY}"
    payload = {"title": title, "body": body, "url": url_to_open, "group": "Serv00 Checker"}
    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'},
                                 data=json.dumps(payload), timeout=15)
        if response.json().get("code") == 200:
            print("Bark 推送通知已成功发送！")
            return True
        print(f"发送 Bark 通知失败: {response.text}")
    except Exception as e:
        print(f"发送 Bark 通知时发生错误: {e}")
    return False


def check_serv00_status():
    """直接读取官网使用的计数接口，不再依赖无头浏览器渲染。返回进程退出码。"""
    print(f"正在请求计数接口: {COUNT_API}")
    try:
        resp = requests.get(COUNT_API, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        current_accounts = int(data['accounts'])
        max_accounts = int(data['limit'])
    except Exception as e:
        print(f"错误: 无法获取或解析账户数量: {e}")
        send_bark_notification("Serv00脚本错误", f"无法获取账户数量: {e}", URL)
        return 1

    print(f"状态: 当前账户 {current_accounts} / {max_accounts}")

    if current_accounts < max_accounts:
        print("判断: 注册已开放！(账户未满)")
        title = "🎉 Serv00.com 注册开放!"
        body = f"当前账户: {current_accounts} / {max_accounts}，剩余 {max_accounts - current_accounts} 个名额！"
    else:
        print("判断: 注册已关闭。(账户已满)")
        title = "Serv00.com 注册未开放"
        body = f"当前账户: {current_accounts} / {max_accounts}。无名额。"

    if not send_bark_notification(title=title, body=body, url_to_open=URL) and BARK_KEY:
        return 1  # 推送失败时让 Actions 标红，避免静默失败
    return 0


if __name__ == "__main__":
    sys.exit(check_serv00_status())
