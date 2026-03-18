"""
每日提醒推送脚本
由GitHub Actions定时调用
- 上午8:45：今天生日 + 今天跟进
- 下午16:45：今天联系总结 + 明天生日

支持多种方式指定模式：
  python scripts/push_reminder.py           # 自动根据时间判断
  python scripts/push_reminder.py morning   # 强制上午模式
  python scripts/push_reminder.py afternoon # 强制下午模式
  python scripts/push_reminder.py both      # 同时推送上午和下午
  
  环境变量方式：
  PUSH_MODE=morning python scripts/push_reminder.py
"""

import os
import sys
from datetime import datetime

# 添加项目根目录和src目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from tools.notification_pusher import _push_morning_reminders_impl, _push_afternoon_reminders_impl


def main():
    """主函数：根据时间或参数推送不同的提醒"""
    print("=" * 80)
    print("📅 开始执行每日提醒推送任务")
    print("=" * 80)
    
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
    
    # 判断推送模式（优先级：命令行参数 > 环境变量 > 自动判断）
    mode = None
    
    # 1. 检查命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['morning', 'm', '上午']:
            mode = 'morning'
        elif arg in ['afternoon', 'a', '下午']:
            mode = 'afternoon'
        elif arg in ['both', 'all', '全部']:
            mode = 'both'
        else:
            print(f"⚠️  未知的参数：{arg}")
            print("用法：python scripts/push_reminder.py [morning|afternoon|both]")
            sys.exit(1)
    # 2. 检查环境变量（GitHub Actions手动触发时使用）
    elif os.getenv('PUSH_MODE'):
        env_mode = os.getenv('PUSH_MODE').lower()
        if env_mode in ['morning', 'm']:
            mode = 'morning'
        elif env_mode in ['afternoon', 'a']:
            mode = 'afternoon'
        elif env_mode in ['both', 'all']:
            mode = 'both'
        else:
            print(f"⚠️  未知的PUSH_MODE：{env_mode}，自动判断模式")
    
    # 3. 根据当前时间自动判断
    if not mode:
        current_hour = datetime.now().hour
        mode = 'morning' if current_hour < 12 else 'afternoon'
    
    print(f"📌 推送模式：{mode}")
    
    # 执行推送
    if mode == 'morning':
        print("\n☀️ 上午推送模式")
        result = _push_morning_reminders_impl()
        print(result)
    elif mode == 'afternoon':
        print("\n🌙 下午推送模式")
        result = _push_afternoon_reminders_impl()
        print(result)
    elif mode == 'both':
        print("\n☀️ 上午推送")
        print("-" * 80)
        result1 = _push_morning_reminders_impl()
        print(result1)
        
        print("\n🌙 下午推送")
        print("-" * 80)
        result2 = _push_afternoon_reminders_impl()
        print(result2)
    
    print("\n" + "=" * 80)
    print("✅ 每日提醒推送任务完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
