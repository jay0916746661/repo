"""
Line Notify 通知模組
用法：
  import line_notify
  line_notify.send("你好！")
或直接執行測試：
  python line_notify.py
"""

import os
import json
import requests


def send_line(message: str, token: str) -> bool:
    """發送 Line Notify 訊息，成功回傳 True"""
    if not token or token.startswith("PASTE_YOUR"):
        print("[Line Notify] ⚠️ Token 尚未設定，跳過通知")
        return False

    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, headers=headers, data={"message": message}, timeout=10)
    if resp.status_code == 200:
        print("[Line Notify] ✅ 通知發送成功")
        return True
    else:
        print(f"[Line Notify] ❌ 發送失敗: {resp.status_code} {resp.text}")
        return False


def get_token() -> str:
    """優先從環境變數取 Token，其次從 config.json"""
    token = os.environ.get("LINE_NOTIFY_TOKEN", "")
    if token:
        return token
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("line_notify_token", "")
    except FileNotFoundError:
        return ""


def send(message: str) -> bool:
    """自動讀取 Token 並發送"""
    return send_line(message, get_token())


if __name__ == "__main__":
    # 測試用：直接執行這個檔案
    print("Line Notify 測試發送...")
    ok = send("\n🎸 Jim Finance 2026 - 系統測試通知\n✅ Line Notify 連線正常！")
    if not ok:
        print("請先在 config.json 填入你的 LINE_NOTIFY_TOKEN")
