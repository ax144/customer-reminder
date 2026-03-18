"""
每日提醒推送脚本
由GitHub Actions定时调用
- 上午8:45：今天生日 + 今天跟进
- 下午16:45：今天联系总结 + 明天生日
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.notification_pusher import _push_morning_reminders_impl, _push_afternoon_reminders_impl


def main():
    """主函数：根据时间推送不同的提醒"""
    print("=" * 50)
    print("📅 开始执行每日提醒推送任务")
    print("=" * 50)
    
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
    
    # 判断是上午还是下午
    current_hour = datetime.now().hour
    
    if current_hour < 12:
        # 上午推送
        print("\n☀️ 上午推送模式")
        result = _push_morning_reminders_impl()
    else:
        # 下午推送
        print("\n🌅 下午推送模式")
        result = _push_afternoon_reminders_impl()
    
    print(result)
    
    print("\n" + "=" * 50)
    print("✅ 每日提醒推送任务完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
