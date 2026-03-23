"""
每日提醒推送脚本
由GitHub Actions定时调用

推送类型：
- morning: 上午客户关怀（满7天未联系的客户）
- afternoon: 下午客户关怀（今日已联系客户总结）
- meeting_visit_morning: 早上约见/外访通知
- meeting_visit_afternoon: 下午约见/外访提醒

约见/外访推送日期配置：
- 24号下午：约见计划（明天有约见）
- 25号早上：约见通知（今天有约见）
- 25号下午：外访提醒（明天外访）
- 26号早上：外访通知（今天需要外访）
"""

import os
import sys
from datetime import datetime, timedelta, date

# 添加项目根目录和src目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from tools.notification_pusher import (
    _push_morning_reminders_impl,
    _push_afternoon_reminders_impl,
    _push_meeting_plan_impl,
    _push_meeting_notify_impl,
    _push_visit_reminder_impl,
    _push_visit_notify_impl,
)
from supabase import create_client


# ============ 约见/外访推送日期配置 ============
# 格式：'YYYY-MM-DD'

# 约见计划：24号下午推送
MEETING_PLAN_DATE = '2024-03-24'

# 约见通知：25号早上推送
MEETING_NOTIFY_DATE = '2024-03-25'

# 外访提醒：25号下午推送
VISIT_REMINDER_DATE = '2024-03-25'

# 外访通知：26号早上推送
VISIT_NOTIFY_DATE = '2024-03-26'


def get_supabase_client():
    """获取 Supabase 客户端"""
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_ANON_KEY')
    if not url or not key:
        raise ValueError("缺少 SUPABASE_URL 或 SUPABASE_ANON_KEY 环境变量")
    return create_client(url, key)


def check_already_pushed(push_type: str, today: date) -> bool:
    """检查今天是否已经推送过"""
    try:
        client = get_supabase_client()
        today_str = today.isoformat()
        
        result = client.table('push_logs').select('id').eq('push_date', today_str).eq('push_type', push_type).execute()
        
        return len(result.data) > 0
    except Exception as e:
        print(f"⚠️ 检查推送状态失败：{e}")
        return False


def record_push(push_type: str, today: date) -> bool:
    """记录本次推送"""
    try:
        client = get_supabase_client()
        today_str = today.isoformat()
        
        client.table('push_logs').insert({
            'push_date': today_str,
            'push_type': push_type
        }).execute()
        
        return True
    except Exception as e:
        print(f"⚠️ 记录推送失败：{e}")
        return False


def push_and_record(mode: str, push_func, today: date) -> str:
    """执行推送并记录"""
    push_type = f"daily_{mode}"
    
    if check_already_pushed(push_type, today):
        print(f"⏭️ 今天 {today} 已经推送过 [{mode}]，跳过")
        return ""
    
    result = push_func()
    record_push(push_type, today)
    
    return result


def main():
    """主函数：根据模式推送不同的提醒"""
    print("=" * 80)
    print("📅 开始执行提醒推送任务")
    print("=" * 80)
    
    # 获取北京时间今天
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    today = beijing_now.date()
    today_str = today.isoformat()
    print(f"📍 北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境变量
    required_env = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "FEISHU_WEBHOOK_URL"
    ]
    
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        print(f"❌ 缺少环境变量：{', '.join(missing_env)}")
        sys.exit(1)
    
    print("✅ 环境变量检查通过")
    
    # 判断推送模式
    mode = None
    
    # 1. 命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    # 2. 环境变量
    elif os.getenv('PUSH_MODE'):
        mode = os.getenv('PUSH_MODE').lower()
    # 3. 根据时间自动判断
    else:
        current_hour = beijing_now.hour
        mode = 'morning' if current_hour < 12 else 'afternoon'
    
    print(f"📌 推送模式：{mode}")
    
    # ========== 执行推送 ==========
    
    if mode == 'morning':
        print("\n☀️ 上午客户关怀推送")
        result = push_and_record('morning', _push_morning_reminders_impl, today)
        print(result) if result else None
    
    elif mode == 'afternoon':
        print("\n🌙 下午客户关怀推送")
        result = push_and_record('afternoon', _push_afternoon_reminders_impl, today)
        print(result) if result else None
    
    elif mode == 'meeting_visit_morning':
        # 早上6点：根据日期判断推送约见通知还是外访通知
        print("\n🔔 早上约见/外访通知")
        
        # 25号早上：约见通知
        if today_str == MEETING_NOTIFY_DATE:
            print("📅 今天是约见通知日")
            result = push_and_record('meeting_morning', _push_meeting_notify_impl, today)
            print(result) if result else None
        # 26号早上：外访通知
        elif today_str == VISIT_NOTIFY_DATE:
            print("🚗 今天是外访通知日")
            result = push_and_record('visit_morning', _push_visit_notify_impl, today)
            print(result) if result else None
        else:
            print("⏭️ 今天没有约见/外访通知，跳过")
    
    elif mode == 'meeting_visit_afternoon':
        # 下午17:30：根据日期判断推送约见计划还是外访提醒
        print("\n📅 下午约见/外访提醒")
        
        # 24号下午：约见计划
        if today_str == MEETING_PLAN_DATE:
            print("📅 今天是约见计划日")
            result = push_and_record('meeting_afternoon', _push_meeting_plan_impl, today)
            print(result) if result else None
        # 25号下午：外访提醒
        elif today_str == VISIT_REMINDER_DATE:
            print("🚗 今天是外访提醒日")
            result = push_and_record('visit_afternoon', _push_visit_reminder_impl, today)
            print(result) if result else None
        else:
            print("⏭️ 今天没有约见/外访提醒，跳过")
    
    else:
        print(f"❌ 未知的推送模式：{mode}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ 推送任务完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
