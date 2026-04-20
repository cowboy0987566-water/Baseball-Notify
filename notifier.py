import os
import json
import requests
import sys
from datetime import datetime, timedelta

def send_line_message(token, to_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": to_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.status_code, response.text

def get_weekly_schedule(schedule_data, team_name, force_date=None):
    if force_date:
        today = datetime.strptime(force_date, "%Y-%m-%d")
    else:
        # 當前時間 (台灣時間 UTC+8)
        today = datetime.now() + timedelta(hours=8)
    
    # 計算本週日
    days_until_sunday = (6 - today.weekday()) % 7
    target_sunday = today + timedelta(days=days_until_sunday)
    target_date_str = target_sunday.strftime("%Y-%m-%d")
    
    print(f"正在檢查週日賽程: {target_date_str}")
    
    # 找出當天的所有賽程
    day_entry = next((item for item in schedule_data if item["date"] == target_date_str), None)
    matches = day_entry["matches"] if day_entry else []
    
    return target_sunday, matches

def main():
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    
    if not token:
        print("錯誤: 缺少 LINE_CHANNEL_ACCESS_TOKEN 環境變數。")
        return

    # 僅測試 RL 群組
    target_id = "C5f2941eab7c85c53c2fe8b916b580990"
    msg = "【系統測試】這是一則來自賽程小幫手的測試訊息，若您看到此訊息代表 ID 配置正確。"

    print(f"\n===== 正在測試 RL 群組 ID: {target_id} =====")
    status, res = send_line_message(token, target_id, msg)
    print(f"發送完成。狀態碼: {status}, 回應: {res}")

if __name__ == "__main__":
    main()
