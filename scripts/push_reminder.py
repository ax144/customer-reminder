"""
每日提醒推送脚本
由GitHub Actions定时调用
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.customer_manager import _check_reminders_impl
from src.tools.notification_pusher import _push_reminders_to_feishu_impl


def main():
    """主函数：检查提醒并推送到飞书"""
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
    
    # 检查提醒
    print("\n📋 正在检查提醒事项...")
    reminders = _check_reminders_impl(days_ahead=7)
    print(reminders)
    
    # 推送到飞书
    print("\n📤 正在推送到飞书...")
    result = _push_reminders_to_feishu_impl()
    print(result)
    
    print("\n" + "=" * 50)
    print("✅ 每日提醒推送任务完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
