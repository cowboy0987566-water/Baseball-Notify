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
    to_id = os.getenv("LINE_GROUP_ID")
    team_name = "柏飛"
    
    force_date = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not token or not to_id:
        print("錯誤: 缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_GROUP_ID 環境變數。")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    schedule_path = os.path.join(base_dir, "schedule.json")

    if not os.path.exists(schedule_path):
        print(f"找不到賽程檔案: {schedule_path}")
        return

    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)
    
    date_obj, all_matches = get_weekly_schedule(schedule_data, team_name, force_date)
    
    # 檢查該隊伍當天是否有任何參與
    has_any_involvement = any(team_name in m["teams"] for m in all_matches)
    
    if all_matches and has_any_involvement:
        msg = f"⚾️ 【{team_name}】本週比賽預告 ⚾️\n"
        msg += f"📅 日期：{date_obj.strftime('%Y/%m/%d')} (日)\n"
        msg += f"📍 地點：仁德春風球場\n"
        msg += "----------------------\n"
        
        # 將比賽按三場一組(三角賽)分類
        groups = [
            all_matches[0:3],
            all_matches[3:6],
            all_matches[6:9]
        ]
        
        for group in groups:
            group_involved = any(team_name in m["teams"] for m in group)
            if group_involved:
                for m in group:
                    is_playing = team_name in m["teams"]
                    vs_info = f"{m['teams'][0]} vs {m['teams'][1]}"
                    if is_playing:
                        msg += f"⏰ {m['time']} | {vs_info}\n"
                    else:
                        msg += f"⏰ {m['time']} | {vs_info}(裁判)\n"
        
        msg += "----------------------\n"
        msg += "備註：\n\n"
        msg += "✅ 參加：\n\n\n"
        msg += "❌ 不參加：\n"
    elif all_matches:
        msg = f"📅 {date_obj.strftime('%m/%d')} (日)\n本週【{team_name}】無賽程，大家休息一週！"
    else:
        msg = f"📅 {date_obj.strftime('%m/%d')} (日)\n目前尚無本週賽程資訊。"

    print(f"正在發送訊息至 {to_id}...")
    print("-" * 20)
    print(msg)
    print("-" * 20)
    
    status, res = send_line_message(token, to_id, msg)
    print(f"發送完成。狀態碼: {status}, 回應: {res}")

if __name__ == "__main__":
    main()
