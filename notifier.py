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
        today = datetime.now()
    
    # 計算下一個週日 (或是本週日)
    days_until_sunday = (6 - today.weekday()) % 7
    target_sunday = today + timedelta(days=days_until_sunday)
    target_date_str = target_sunday.strftime("%Y-%m-%d")
    
    print(f"Checking schedule for Sunday: {target_date_str}")
    
    for entry in schedule_data:
        if entry["date"] == target_date_str:
            matches = entry["matches"]
            team_matches = [m for m in matches if team_name in m["teams"]]
            return target_sunday, team_matches
            
    return target_sunday, []

def main():
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to_id = os.getenv("LINE_GROUP_ID")
    team_name = "柏飛"
    
    # 支援手動測試測試日期: python3 notifier.py 2026-04-12
    force_date = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not token or not to_id:
        print("Error: Missing LINE_CHANNEL_ACCESS_TOKEN or LINE_GROUP_ID environment variables.")
        return

    # 取得檔案絕對路徑
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schedule_path = os.path.join(base_dir, "schedule.json")

    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)
    
    date_obj, matches = get_weekly_schedule(schedule_data, team_name, force_date)
    
    if matches:
        msg = f"📅 【柏飛】本週比賽預報 ({date_obj.strftime('%m/%d')})\n\n"
        for i, m in enumerate(matches, 1):
            opponent = [t for t in m["teams"] if t != team_name][0]
            msg += f"{i}. 時間：{m['time']}\n"
            msg += f"   對手：{opponent}\n"
        msg += "\n⚾️ 請大家準時到場加油！"
        
        print(f"Sending message to {to_id}...")
        status, res = send_line_message(token, to_id, msg)
        print(f"Message sent. Status: {status}, Response: {res}")
    else:
        print(f"No matches found for {team_name} on {date_obj.strftime('%m/%d')}.")

if __name__ == "__main__":
    main()
