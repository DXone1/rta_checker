import requests
import json
from datetime import datetime
import os

# --- 配置区域 ---
# 你的 PushPlus Token (建议通过环境变量注入，不要直接写死在代码里)
PUSH_TOKEN = os.environ.get('PUSH_TOKEN') 

# 目标考点 ID (Roselands = 421)
TARGET_LOCATION_ID = "421"

# 目标 URL
URL = "https://sbmkvp.github.io/rta_booking_information/results.json"

# 目标日期范围
START_DATE = datetime(2026, 1, 5) # 1月5日之后
END_DATE = datetime(2026, 1, 15)  # 1月15日及之前

def send_wechat_notification(content):
    """发送微信通知"""
    if not PUSH_TOKEN:
        print("未配置 PushPlus Token，跳过发送")
        return
    
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSH_TOKEN,
        "title": "🎉 RTA Roselands 有考位啦！",
        "content": content,
        "template": "html"
    }
    try:
        requests.post(url, json=data)
        print("微信通知已发送")
    except Exception as e:
        print(f"发送失败: {e}")

def check_slots():
    print(f"开始检查: {datetime.now()}")
    try:
        # 1. 获取数据
        # 添加 User-Agent 防止被简单的反爬虫拦截
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(URL, headers=headers)
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return

        data = response.json()

        # 2. 找到 Roselands (ID 421) 的数据
        roselands_data = None
        for location in data:
            if str(location.get('location')) == TARGET_LOCATION_ID:
                roselands_data = location
                break
        
        if not roselands_data:
            print("未找到 Roselands 数据")
            return

        # 3. 筛选考位
        available_slots = []
        try:
            slots_list = roselands_data['result']['ajaxresult']['slots']['listTimeSlot']
        except KeyError:
            print("数据结构解析错误，可能是考位数据为空")
            return

        for slot in slots_list:
            # 数据格式通常为 "dd/mm/yyyy HH:MM"
            slot_time_str = slot.get('startTime')
            if not slot_time_str:
                continue
                
            try:
                slot_time = datetime.strptime(slot_time_str, "%d/%m/%Y %H:%M")
            except ValueError:
                continue

            # 检查时间是否在 1月5日之后 且 1月15日之前
            # 注意：startTime > START_DATE 会排除1月5日当天，符合你的"之后"要求
            # slot_time <= END_DATE 包含1月15日
            if START_DATE < slot_time <= END_DATE:
                # 再次确认 availability 为 true (虽然有些系统可能把 false 也列出来)
                # 你的json样本里有 "availability": false/true
                # 如果你想即使是 false 也提醒（可能是缓存），可以去掉这个判断
                # 这里假设只提醒 available 的
                if slot.get('availability') is True or slot.get('slotNumber') is not None:
                    available_slots.append(slot_time_str)

        # 4. 如果有考位，发送通知
        if available_slots:
            msg = f"发现 {len(available_slots)} 个可用考位！<br>" + "<br>".join(available_slots)
            print(msg)
            send_wechat_notification(msg)
        else:
            print("当前时段无可用考位")

    except Exception as e:
        print(f"脚本运行出错: {e}")

if __name__ == "__main__":
    check_slots()
