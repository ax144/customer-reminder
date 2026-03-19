"""
每日提醒推送脚本
由GitHub Actions定时调用
- 上午8:45：满7天及超过7天未联系的客户提醒
- 下午16:45：今日已联系客户总结
"""

import os
import sys
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from tools.notification_pusher import _push_morning_reminders_impl, _push_afternoon_reminders_impl


def main():
    print("=" * 80)
    print("📅 开始执行每日提醒推送任务")
    print("=" * 80)
    
    required_env = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "FEISHU_WEBHOOK_URL"]
    missing_env = [env for env in required_env if not os.getenv(env)]
    if missing_env:
        print(f"❌ 缺少环境变量：{', '.join(missing_env)}")
        sys.exit(1)
    
    print("✅ 环境变量检查通过")
    
    mode = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['morning', 'm']:
            mode = 'morning'
        elif arg in ['afternoon', 'a']:
            mode = 'afternoon'
    elif os.getenv('PUSH_MODE'):
        mode = os.getenv('PUSH_MODE').lower()
    
    if not mode:
        mode = 'morning' if datetime.now().hour < 12 else 'afternoon'
    
    print(f"📌 推送模式：{mode}")
    
    if mode == 'morning':
        print("\n☀️ 上午推送模式")
        result = _push_morning_reminders_impl()
        print(result)
    elif mode == 'afternoon':
        print("\n🌙 下午推送模式")
        result = _push_afternoon_reminders_impl()
        print(result)
    
    print("\n" + "=" * 80)
    print("✅ 每日提醒推送任务完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
