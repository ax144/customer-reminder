"""
每日提醒推送脚本
由GitHub Actions定时调用
- 推送满7天及超过7天未联系的客户提醒
"""

import os
import sys
from datetime import datetime

# 添加项目根目录和src目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from tools.notification_pusher import _push_reminders_impl


def main():
    """主函数：推送客户提醒"""
    print("=" * 80)
    print("📅 开始执行客户提醒推送任务")
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
    print(f"📌 推送模式：客户未联系提醒")
    
    # 执行推送
    result = _push_reminders_impl()
    print(result)
    
    print("\n" + "=" * 80)
    print("✅ 客户提醒推送任务完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
