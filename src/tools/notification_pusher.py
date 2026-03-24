"""
飞书消息推送工具模块
"""

import os
import requests
from datetime import datetime, timedelta


def _has_meeting(target_date) -> bool:
    """检查指定日期是否有约见"""
    try:
        from supabase import create_client
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
        result = client.table('customers').select('id').eq('meeting_date', target_date.strftime("%Y-%m-%d")).limit(1).execute()
        return len(result.data) > 0
    except:
        return False


def _has_visit(target_date) -> bool:
    """检查指定日期是否有外访"""
    try:
        from supabase import create_client
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
        result = client.table('customers').select('id').eq('visit_date', target_date.strftime("%Y-%m-%d")).limit(1).execute()
        return len(result.data) > 0
    except:
        return False


def _push_meeting_plan_impl(ctx=None) -> str:
    """约见计划：明天有约见"""
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return "❌ 未配置"
    
    tomorrow = datetime.now() + timedelta(days=1)
    if not _has_meeting(tomorrow):
        return "ℹ️ 明天没有约见"
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "📅 约见计划"}, "template": "purple"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "## 明天有约见"}}]
        }
    }
    
    response = requests.post(webhook_url, json=card, timeout=10)
    return "✅ 约见计划已推送！" if response.status_code == 200 else "❌ 推送失败"


def _push_meeting_notify_impl(ctx=None) -> str:
    """约见通知：今天有约见"""
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return "❌ 未配置"
    
    today = datetime.now()
    if not _has_meeting(today):
        return "ℹ️ 今天没有约见"
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "🔔 约见通知"}, "template": "red"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "## 今天有约见"}}]
        }
    }
    
    response = requests.post(webhook_url, json=card, timeout=10)
    return "✅ 约见通知已推送！" if response.status_code == 200 else "❌ 推送失败"


def _push_visit_reminder_impl(ctx=None) -> str:
    """外访提醒：明天有外访"""
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return "❌ 未配置"
    
    tomorrow = datetime.now() + timedelta(days=1)
    if not _has_visit(tomorrow):
        return "ℹ️ 明天没有外访"
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "🚗 外访提醒"}, "template": "orange"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "## 明天有外访"}}]
        }
    }
    
    response = requests.post(webhook_url, json=card, timeout=10)
    return "✅ 外访提醒已推送！" if response.status_code == 200 else "❌ 推送失败"


def _push_visit_notify_impl(ctx=None) -> str:
    """外访通知：今天有外访"""
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return "❌ 未配置"
    
    today = datetime.now()
    if not _has_visit(today):
        return "ℹ️ 今天没有外访"
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "🔔 外访通知"}, "template": "yellow"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "## 今天有外访"}}]
        }
    }
    
    response = requests.post(webhook_url, json=card, timeout=10)
    return "✅ 外访通知已推送！" if response.status_code == 200 else "❌ 推送失败"


def _push_morning_reminders_impl(ctx=None) -> str:
    """上午推送"""
    from tools.customer_manager import _get_reminders_impl
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return "❌ 未配置"
    
    reminders_text = _get_reminders_impl(ctx=ctx)
    today = datetime.now().strftime("%Y年%m月%d日")
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": f"☀️ {today} 上午提醒"}, "template": "blue"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": reminders_text}}]
        }
    }
    
    response = requests.post(webhook_url, json=card, timeout=10)
    return "✅ 提醒已推送！" if response.status_code == 200 else "❌ 推送失败"


def _push_afternoon_reminders_impl(ctx=None) -> str:
    """下午推送"""
    from tools.customer_manager import _get_today_contacted_impl
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return "❌ 未配置"
    
    summary_text = _get_today_contacted_impl(ctx=ctx)
    today = datetime.now().strftime("%Y年%m月%d日")
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": f"🌙 {today} 下午总结"}, "template": "turquoise"},
            "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": summary_text}}]
        }
    }
    
    response = requests.post(webhook_url, json=card, timeout=10)
    return "✅ 总结已推送！" if response.status_code == 200 else "❌ 推送失败"


__all__ = [
    '_push_morning_reminders_impl',
    '_push_afternoon_reminders_impl',
    '_push_meeting_plan_impl',
    '_push_meeting_notify_impl',
    '_push_visit_reminder_impl',
    '_push_visit_notify_impl',
]
