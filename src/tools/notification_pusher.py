"""
飞书消息推送工具模块
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
import os
import requests
from datetime import datetime, timedelta


# ============ 约见/外访推送相关 ============

def _get_meeting_customers(target_date) -> str:
    """获取指定日期有约见的客户列表"""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            return ""
        
        client = create_client(url, key)
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        result = client.table('customers').select('name, company').eq('meeting_date', target_date_str).execute()
        
        if not result.data:
            return ""
        
        lines = []
        for c in result.data:
            name = c.get('name', '未知')
            company = c.get('company', '未知公司')
            lines.append(f"{name} - {company}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return ""


def _get_visit_customers(target_date) -> str:
    """获取指定日期有外访的客户列表"""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            return ""
        
        client = create_client(url, key)
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        result = client.table('customers').select('name, company').eq('visit_date', target_date_str).execute()
        
        if not result.data:
            return ""
        
        lines = []
        for c in result.data:
            name = c.get('name', '未知')
            company = c.get('company', '未知公司')
            lines.append(f"{name} - {company}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return ""


def _push_meeting_plan_impl(ctx=None) -> str:
    """约见计划推送：提醒明天有约见"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        tomorrow = datetime.now() + timedelta(days=1)
        customers_text = _get_meeting_customers(tomorrow)
        
        if not customers_text:
            return "ℹ️ 明天没有约见安排"
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": "📅 约见计划"},
                    "template": "purple"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"## 明天有约见\n\n{customers_text}"
                        }
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 约见计划已推送！\n\n{customers_text}"
            else:
                return f"❌ 飞书推送失败：{result}"
        else:
            return f"❌ 飞书推送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 推送失败：{str(e)}"


def _push_meeting_notify_impl(ctx=None) -> str:
    """约见通知推送：提醒今天有约见"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        today = datetime.now()
        customers_text = _get_meeting_customers(today)
        
        if not customers_text:
            return "ℹ️ 今天没有约见安排"
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": "🔔 约见通知"},
                    "template": "red"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"## 今天有约见\n\n{customers_text}"
                        }
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 约见通知已推送！\n\n{customers_text}"
            else:
                return f"❌ 飞书推送失败：{result}"
        else:
            return f"❌ 飞书推送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 推送失败：{str(e)}"


def _push_visit_reminder_impl(ctx=None) -> str:
    """外访提醒推送：提醒明天有外访"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        tomorrow = datetime.now() + timedelta(days=1)
        customers_text = _get_visit_customers(tomorrow)
        
        if not customers_text:
            return "ℹ️ 明天没有外访安排"
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": "🚗 外访提醒"},
                    "template": "orange"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"## 明天外访\n\n{customers_text}"
                        }
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 外访提醒已推送！\n\n{customers_text}"
            else:
                return f"❌ 飞书推送失败：{result}"
        else:
            return f"❌ 飞书推送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 推送失败：{str(e)}"


def _push_visit_notify_impl(ctx=None) -> str:
    """外访通知推送：提醒今天有外访"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        today = datetime.now()
        customers_text = _get_visit_customers(today)
        
        if not customers_text:
            return "ℹ️ 今天没有外访安排"
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": "🔔 外访通知"},
                    "template": "yellow"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"## 今天需要外访\n\n{customers_text}"
                        }
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 外访通知已推送！\n\n{customers_text}"
            else:
                return f"❌ 飞书推送失败：{result}"
        else:
            return f"❌ 飞书推送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 推送失败：{str(e)}"


# ============ 客户关怀推送 ============

def _push_morning_reminders_impl(ctx=None) -> str:
    """上午推送：满7天及超过7天未联系的客户"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        from tools.customer_manager import _get_reminders_impl
        reminders_text = _get_reminders_impl(ctx=ctx)
        
        today = datetime.now().strftime("%Y年%m月%d日")
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": f"☀️ {today} 上午提醒"},
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": reminders_text
                        }
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 提醒已成功推送到飞书！"
            else:
                return f"❌ 飞书推送失败：{result}"
        else:
            return f"❌ 飞书推送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 推送提醒失败：{str(e)}"


def _push_afternoon_reminders_impl(ctx=None) -> str:
    """下午推送：今日已联系客户总结"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        from tools.customer_manager import _get_today_contacted_impl
        summary_text = _get_today_contacted_impl(ctx=ctx)
        
        today = datetime.now().strftime("%Y年%m月%d日")
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": f"🌙 {today} 下午总结"},
                    "template": "turquoise"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": summary_text
                        }
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 总结已成功推送到飞书！"
            else:
                return f"❌ 飞书推送失败：{result}"
        else:
            return f"❌ 飞书推送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 推送总结失败：{str(e)}"


# 导出
__all__ = [
    '_push_morning_reminders_impl',
    '_push_afternoon_reminders_impl',
    '_push_meeting_plan_impl',
    '_push_meeting_notify_impl',
    '_push_visit_reminder_impl',
    '_push_visit_notify_impl',
]
