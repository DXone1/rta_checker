import requests
import json
from datetime import datetime
import os
import time

# --- 配置区域 ---
# 你的 PushPlus Token (从环境变量获取)
PUSH_TOKEN = os.environ.get('PUSH_TOKEN') 

# 目标 API 地址
URL = "https://driverstest.noob.place/api/get_location_details8534567107532739672"

# 目标考点配置 (ID: 名称)
TARGET_LOCATIONS = {
    "421": "Roselands",
    "20":  "Bankstown",
    "382": "Revesby",
    "109": "Rockdale"  # 备注: 109 通常是 Rockdale
}

# 目标日期范围 (2026年1月5日及之后 - 2026年1月20日及之前)
START_DATE = datetime(2026, 1, 5) 
END_DATE = datetime(2026, 1, 20)

def send_wechat_notification(content):
    """发送微信通知"""
    if not PUSH_TOKEN:
        print("未配置 PushPlus Token，跳过发送")
        return
    
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSH_TOKEN,
        "title": "🎉 发现目标考位！(多地区)",
        "content": content,
        "template": "html"
    }
    try:
        requests.post(url, json=data)
        print("微信通知已发送")
    except Exception as e:
        print(f"发送失败: {e}")

def get_slots_for_location(loc_id, loc_name):
    """查询单个考点的考位，返回可用时间列表"""
    print(f"--- 正在检查: {loc_name} (ID: {loc_id}) ---")
    
    # 1. 构造请求头 (保留了你添加的 Origin 和 Referer)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded", 
        "Origin": "https://driverstest.noob.place",
        "Referer": "https://driverstest.noob.place/",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
    }
    
    # 2. 构造 Form Data
    payload = {
        "location_id": loc_id,
        "client_etag": "" 
    }

    found_slots = []

    try:
        response = requests.post(URL, data=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  ❌ 请求失败，状态码: {response.status_code}")
            return []

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("  ❌ 返回内容不是 JSON，可能是服务器错误")
            return []

        # 3. 验证 Location ID
        if str(data.get("location")) != loc_id:
            print(f"  ⚠️ API返回的 location ({data.get('location')}) 与预期不符，继续检查...")

        # 4. 筛选考位
        slots_list = data.get('slots', [])
        print(f"  API 返回了 {len(slots_list)} 个时间段数据")

        for slot in slots_list:
            time_str = slot.get('startTime')
            if not time_str:
                continue

            # 逻辑：先看 availability 是否为 True
            if slot.get('availability') is True:
                print(f"  🔎 发现可用考位 (日期未验证): {time_str}")
                
                try:
                    # 解析日期格式: dd/mm/yyyy HH:MM
                    slot_time = datetime.strptime(time_str, "%d/%m/%Y %H:%M")
                except ValueError:
                    print(f"    ❌ 日期格式解析错误: {time_str}")
                    continue

                # 检查日期范围 (START_DATE <= slot_time <= END_DATE)
                if START_DATE <= slot_time <= END_DATE:
                    print(f"    ✅ 日期符合要求 ({START_DATE.date()} - {END_DATE.date()})! 加入列表.")
                    found_slots.append(time_str)
                else:
                    print(f"    ⚠️ 日期不在目标范围内，忽略.")
        
        if not found_slots:
            print(f"  🏁 {loc_name} 本次无符合条件的考位")

        return found_slots

    except Exception as e:
        print(f"  ❌ 脚本运行出错: {e}")
        return []

def main():
    print(f"=== 开始全考点扫描: {datetime.now()} ===")
    
    all_messages = []
    
    # 遍历你在配置区定义的四个考点
    for loc_id, loc_name in TARGET_LOCATIONS.items():
        slots = get_slots_for_location(loc_id, loc_name)
        
        if slots:
            # 格式化单个考点的信息
            msg_part = (f"<b>📍 {loc_name}</b> (ID {loc_id}):<br>" + 
                        "<br>".join(slots) + "<br>")
            all_messages.append(msg_part)
        
        # 稍微等待一下，防止请求过快
        time.sleep(1)

    # 如果汇总列表里有内容，发送合并通知
    if all_messages:
        count_msg = f"共发现 {len(all_messages)} 个地区有位"
        print(f"\n🎉 {count_msg}，准备发送微信通知...")
        
        # 拼接最终消息，包含你要求的自定义信息
        final_content = (
            f"🎯 <b>在目标日期 ({START_DATE.date()} - {END_DATE.date()}) 发现考位！</b><br><br>" + 
            "<br>------------------<br>".join(all_messages) + 
            "<br>------------------<br>" +
            "👉 立即预约：电话 132213" +
            "<br>booking id: 2965462510" +
            "<br><br><a href='https://driverstest.noob.place/'>点击跳转官网</a>"
        )
        send_wechat_notification(final_content)
    else:
        print("\n🏁 所有考点检查完毕，暂无符合条件的考位。")

if __name__ == "__main__":
    main()
