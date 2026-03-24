"""
每日提醒推送脚本
由GitHub Actions定时调用

推送类型：
- morning: 上午客户关怀（满7天未联系的客户）
- afternoon: 下午客户关怀（今日已联系客户总结）
- meeting_visit_morning: 早上约见/外访通知
- meeting_visit_afternoon: 下午约见/外访提醒
"""

import os
import sys
from datetime import datetime, timedelta, date

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
MEETING_PLAN_DATE = '2026-03-24'
MEETING_NOTIFY_DATE = '2026-03-25'
VISIT_REMINDER_DATE = '2026-03-25'
VISIT_NOTIFY_DATE = '2026-03-26'


def get_supabase_client():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_ANON_KEY')
    if not url or not key:
        raise ValueError("缺少环境变量")
    return create_client(url, key)


def check_already_pushed(push_type: str, today: date) -> bool:
    try:
        client = get_supabase_client()
        result = client.table('push_logs').select('id').eq('push_date', today.isoformat()).eq('push_type', push_type).execute()
        return len(result.data) > 0
    except:
        return False


def record_push(push_type: str, today: date):
    try:
        client = get_supabase_client()
        client.table('push_logs').insert({'push_date': today.isoformat(), 'push_type': push_type}).execute()
    except:
        pass


def push_and_record(mode: str, push_func, today: date) -> str:
    push_type = f"daily_{mode}"
    if check_already_pushed(push_type, today):
        print(f"⏭️ 今天已推送过 [{mode}]，跳过")
        return ""
    result = push_func()
    record_push(push_type, today)
    return result


def main():
    print("=" * 60)
    print("📅 开始执行提醒推送任务")
    
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    today = beijing_now.date()
    today_str = today.isoformat()
    print(f"📍 北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    required_env = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "FEISHU_WEBHOOK_URL"]
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        print(f"❌ 缺少环境变量：{', '.join(missing_env)}")
        sys.exit(1)
    
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else os.getenv('PUSH_MODE', 'morning').lower()
    print(f"📌 推送模式：{mode}")
    
    if mode == 'morning':
        result = push_and_record('morning', _push_morning_reminders_impl, today)
        print(result) if result else None
    
    elif mode == 'afternoon':
        result = push_and_record('afternoon', _push_afternoon_reminders_impl, today)
        print(result) if result else None
    
    elif mode == 'meeting_visit_morning':
        if today_str == MEETING_NOTIFY_DATE:
            result = push_and_record('meeting_morning', _push_meeting_notify_impl, today)
            print(result) if result else None
        elif today_str == VISIT_NOTIFY_DATE:
            result = push_and_record('visit_morning', _push_visit_notify_impl, today)
            print(result) if result else None
    
    elif mode == 'meeting_visit_afternoon':
        if today_str == MEETING_PLAN_DATE:
            result = push_and_record('meeting_afternoon', _push_meeting_plan_impl, today)
            print(result) if result else None
        elif today_str == VISIT_REMINDER_DATE:
            result = push_and_record('visit_afternoon', _push_visit_reminder_impl, today)
            print(result) if result else None
    
    print("=" * 60)
    print("✅ 推送任务完成")


if __name__ == "__main__":
    main()
