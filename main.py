import requests
import json
from datetime import datetime
import os
import time
# 引入 Twilio 库
from twilio.rest import Client

# --- 配置区域 ---
# 1. 微信推送配置
PUSH_TOKEN = os.environ.get('PUSH_TOKEN') 

# 2. 电话拨打配置 (从环境变量获取)
TWILIO_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM = os.environ.get('TWILIO_FROM_NUMBER')
MY_PHONE = os.environ.get('MY_PHONE_NUMBER')

# 3. 爬虫配置
URL = "https://driverstest.noob.place/api/get_location_details8534567107532739672"

TARGET_LOCATIONS = {
    "421": "Roselands",
    "20":  "Bankstown",
    "382": "Revesby",
    "109": "Rockdale"
}

# 日期范围 (2026年1月4日 - 1月20日)
START_DATE = datetime(2026, 1, 4) 
END_DATE = datetime(2026, 1, 20)

def make_phone_call():
    """拨打语音电话提醒"""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, MY_PHONE]):
        print("⚠️ Twilio 配置缺失，跳过电话通知")
        return

    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        print(f"☎️ 正在拨打电话给 {MY_PHONE} ...")
        
        # TwiML 是 Twilio 的语音指令，这里让它朗读一段话
        call = client.calls.create(
            twiml='<Response><Say loop="3">Attention! Found a driving test slot! Check your WeChat now.</Say></Response>',
            to=MY_PHONE,
            from_=TWILIO_FROM
        )
        print(f"电话已拨出，SID: {call.sid}")
    except Exception as e:
        print(f"❌ 拨打电话失败: {e}")

def send_wechat_notification(content):
    """发送微信通知"""
    if not PUSH_TOKEN:
        return
    
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSH_TOKEN,
        "title": "🎉 紧急：发现考位！",
        "content": content,
        "template": "html"
    }
    try:
        requests.post(url, json=data)
        print("微信通知已发送")
    except Exception as e:
        print(f"微信发送失败: {e}")

def get_slots_for_location(loc_id, loc_name):
    """查询单个考点"""
    print(f"--- 检查: {loc_name} (ID: {loc_id}) ---")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded", 
        "Origin": "https://driverstest.noob.place",
        "Referer": "https://driverstest.noob.place/",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
    }
    
    payload = {
        "location_id": loc_id,
        "client_etag": "" 
    }

    found_slots = []

    try:
        response = requests.post(URL, data=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  ❌ 状态码: {response.status_code}")
            return []

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("  ❌ JSON解析失败")
            return []

        if str(data.get("location")) != loc_id:
            print(f"  ⚠️ Location ID 不匹配，跳过")
            return []

        slots_list = data.get('slots', [])
        print(f"  API 返回 {len(slots_list)} 条数据")

        for slot in slots_list:
            time_str = slot.get('startTime')
            if not time_str: continue

            # 只要 availability 为 True
            if slot.get('availability') is True:
                try:
                    slot_time = datetime.strptime(time_str, "%d/%m/%Y %H:%M")
                except ValueError:
                    continue

                if START_DATE <= slot_time <= END_DATE:
                    print(f"    ✅ 发现目标: {time_str}")
                    found_slots.append(time_str)
        
        return found_slots

    except Exception as e:
        print(f"  ❌ 出错: {e}")
        return []

def main():
    print(f"=== 任务开始: {datetime.now()} ===")
    
    all_messages = []
    
    for loc_id, loc_name in TARGET_LOCATIONS.items():
        slots = get_slots_for_location(loc_id, loc_name)
        
        if slots:
            msg_part = (f"<b>📍 {loc_name}</b> (ID {loc_id}):<br>" + 
                        "<br>".join(slots) + "<br>")
            all_messages.append(msg_part)
        
        time.sleep(1)

    if all_messages:
        # 1. 发现考位，准备通知内容
        count_msg = f"共发现 {len(all_messages)} 个地区有位"
        print(f"\n🎉 {count_msg}")
        
        final_content = (
            f"🎯 <b>在目标日期 ({START_DATE.date()} - {END_DATE.date()}) 发现考位！</b><br><br>" + 
            "<br>------------------<br>".join(all_messages) + 
            "<br>------------------<br>" +
            "👉 立即预约：电话 132213" +
            "<br>booking id: 2965462510" +
            "<br><br><a href='https://driverstest.noob.place/'>点击跳转官网</a>"
        )
        
        # 2. 发送微信
        send_wechat_notification(final_content)
        
        # 3. 拨打电话 (新增功能)
        make_phone_call()
        
    else:
        print("\n🏁 检查完毕，暂无考位。")

if __name__ == "__main__":
    main()
