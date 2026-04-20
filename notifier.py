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
    default_group_id = os.getenv("LINE_GROUP_ID")
    
    force_date = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not token:
        print("錯誤: 缺少 LINE_CHANNEL_ACCESS_TOKEN 環境變數。")
        return
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schedule_path = os.path.join(base_dir, "schedule.json")

    if not os.path.exists(schedule_path):
        print(f"找不到賽程檔案: {schedule_path}")
        return

    with open(schedule_path, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)

    # 直接定義群組清單，確保在 GitHub Actions 環境中 100% 執行
    groups = [
       # {"team_name": "柏飛", "group_id": default_group_id},
        {"team_name": "耀田", "group_id": "Ca40d1500f2b01b61aaa2bd712be6afda"},
        {"team_name": "RL", "group_id": "Cc9a503f2950fd15f7477d82c6c29c92c"}
    ]

    for group in groups:
        team_name = group["team_name"]
        to_id = group["group_id"]
        
        if not to_id or to_id == "DEFAULT": # 兼容舊設定
            to_id = default_group_id

        print(f"\n===== 正在處理隊伍: {team_name} =====")
        date_obj, all_matches = get_weekly_schedule(schedule_data, team_name, force_date)
        
        # 檢查該隊伍當天是否有任何參與
        has_any_involvement = any(team_name in m["teams"] for m in all_matches)
        
        if all_matches:
            if has_any_involvement:
                msg = f"⚾️ 【{team_name}】本週比賽預告 ⚾️\n"
                msg += f"📅 日期：{date_obj.strftime('%Y/%m/%d')} (日)\n"
                msg += f"📍 地點：仁德春風球場\n"
                msg += "----------------------\n"
                
                # 將比賽按三場一組(三角賽)分類
                temp_groups = [all_matches[i:i+3] for i in range(0, len(all_matches), 3)]
                
                for g in temp_groups:
                    group_involved = any(team_name in m["teams"] for m in g)
                    if group_involved:
                        for m in g:
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
            else:
                msg = f"⚾️ 本週所有賽程 ⚾️\n"
                msg += f"📅 日期：{date_obj.strftime('%Y/%m/%d')} (日)\n"
                msg += f"📍 地點：仁德春風球場\n"
                msg += "----------------------\n"
                for m in all_matches:
                    vs_info = f"{m['teams'][0]} vs {m['teams'][1]}"
                    msg += f"⏰ {m['time']} | {vs_info}\n"
                msg += "----------------------\n"
                msg += f"🎉 本週【{team_name}】無賽程，大家休息一週！\n"
        else:
            msg = f"📅 {date_obj.strftime('%m/%d')} (日)\n目前尚無本週賽程資訊。"

        print(f"正在發送訊息至 {to_id}...")
        status, res = send_line_message(token, to_id, msg)
        print(f"發送完成。狀態碼: {status}, 回應: {res}")

if __name__ == "__main__":
    main()

