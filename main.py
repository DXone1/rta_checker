import requests
import json
from datetime import datetime
import os

# --- 配置区域 ---
# 你的 PushPlus Token (从环境变量获取)
PUSH_TOKEN = os.environ.get('PUSH_TOKEN') 

# [修正] 必须带上后面这串数字，否则会 404
URL = "https://driverstest.noob.place/api/get_location_details8534567107532739672"

# 目标考点 ID (Roselands = 421)
TARGET_LOCATION_ID = "421"

# 目标日期范围 (2026年1月5日之后 - 2026年1月15日及之前)
START_DATE = datetime(2026, 1, 5) 
END_DATE = datetime(2026, 1, 15)

def send_wechat_notification(content):
    """发送微信通知"""
    if not PUSH_TOKEN:
        print("未配置 PushPlus Token，跳过发送")
        return
    
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSH_TOKEN,
        "title": "🎉 Roselands 发现目标考位！",
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
        # 1. 构造请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded", # 对应 curl 的 header
            "Origin": "https://driverstest.noob.place",
            "Referer": "https://driverstest.noob.place/",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
        }
        
        # 2. 构造 Form Data (对应 curl 的 --data-urlencode)
        payload = {
            "location_id": TARGET_LOCATION_ID,
            "client_etag": "" 
        }

        # 使用 data=payload 发送 application/x-www-form-urlencoded 请求
        response = requests.post(URL, data=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...") # 打印部分错误内容方便调试
            return

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("返回内容不是 JSON，可能是服务器错误")
            return

        # 3. 验证 Location ID (有些API返回的是int，转str比较稳)
        if str(data.get("location")) != TARGET_LOCATION_ID:
            print(f"提示：API返回的 location ({data.get('location')}) 与预期不符，继续检查...")

        # 4. 筛选考位
        available_slots = []
        slots_list = data.get('slots', [])
        
        print(f"API 返回了 {len(slots_list)} 个时间段数据")

        for slot in slots_list:
            time_str = slot.get('startTime')
            if not time_str:
                continue

            # 只要 availability 是 True 就认为是有效考位
            if slot.get('availability') is True:
                print(f"🔎 发现可用考位 (日期未验证): {time_str}")
                
                try:
                    # 解析日期格式: dd/mm/yyyy HH:MM
                    slot_time = datetime.strptime(time_str, "%d/%m/%Y %H:%M")
                except ValueError:
                    print(f"   ❌ 日期格式解析错误: {time_str}")
                    continue

                # 检查日期范围
                # TODO: send wechat first
                # if START_DATE < slot_time <= END_DATE:
                    # print(f"   ✅ 日期符合要求 ({START_DATE.date()} - {END_DATE.date()})! 加入通知列表.")
                available_slots.append(time_str)
                # else:
                    # print(f"   ⚠️ 日期不在目标范围内，忽略.")

        # 5. 发送通知
        if available_slots:
            count = len(available_slots)
            msg = (f"🎯 <b>Roselands 锁定 {count} 个考位！</b><br><br>" + 
                   "<br>".join(available_slots) + 
                   "<br><br>👉 立即预约：https://driverstest.noob.place/")
            print(f"成功筛选出 {count} 个目标考位，正在推送...")
            send_wechat_notification(msg)
        else:
            print(f"检查完成：暂无符合日期要求的可用考位")

    except Exception as e:
        print(f"脚本运行出错: {e}")

if __name__ == "__main__":
    check_slots()
