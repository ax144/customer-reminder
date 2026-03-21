"""
每日提醒推送脚本
由GitHub Actions定时调用
- 上午：满7天及超过7天未联系的客户提醒（7:00-9:00 多次触发，只推送一次）
- 下午：今日已联系客户总结（16:00-18:00 多次触发，只推送一次）
"""

import os
import sys
from datetime import datetime, date, timedelta

# 添加项目根目录和src目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from tools.notification_pusher import _push_morning_reminders_impl, _push_afternoon_reminders_impl
from supabase import create_client


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


def main():
    """主函数：根据时间或参数推送不同的提醒"""
    print("=" * 80)
    print("📅 开始执行每日提醒推送任务")
    print("=" * 80)
    
    # 获取北京时间今天
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    today = beijing_now.date()
    print(f"📍 北京时间今天: {today}")
    
    # 检查环境变量
    required_env = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "FEISHU_WEBHOOK_URL"]
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        print(f"❌ 缺少环境变量：{', '.join(missing_env)}")
        sys.exit(1)
    
    print("✅ 环境变量检查通过")
    
    # 判断推送模式
    mode = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['morning', 'm', '上午']:
            mode = 'morning'
        elif arg in ['afternoon', 'a', '下午']:
            mode = 'afternoon'
    elif os.getenv('PUSH_MODE'):
        env_mode = os.getenv('PUSH_MODE').lower()
        if env_mode in ['morning', 'm']:
            mode = 'morning'
        elif env_mode in ['afternoon', 'a']:
            mode = 'afternoon'
    
    if not mode:
        current_hour = beijing_now.hour
        mode = 'morning' if current_hour < 12 else 'afternoon'
    
    print(f"📌 推送模式：{mode}")
    
    # 防重复检查
    push_type = f"daily_{mode}"
    if check_already_pushed(push_type, today):
        print(f"⏭️ 今天 {today} 已经推送过 [{mode}]，跳过本次执行")
        print("=" * 80)
        return
    
    # 执行推送
    if mode == 'morning':
        print("\n☀️ 上午推送模式")
        result = _push_morning_reminders_impl()
        print(result)
    else:
        print("\n🌙 下午推送模式")
        result = _push_afternoon_reminders_impl()
        print(result)
    
    # 记录推送
    if record_push(push_type, today):
        print(f"✅ 已记录推送状态：{today} - {mode}")
    
    print("\n" + "=" * 80)
    print("✅ 每日提醒推送任务完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
