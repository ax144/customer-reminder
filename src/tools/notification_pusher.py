"""
飞书消息推送工具模块
- push_morning_reminders: 上午推送（满7天及超过7天未联系的客户）
- push_afternoon_reminders: 下午推送（今日已联系客户总结）
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
import os
import requests
from datetime import datetime
from typing import Optional

# ============ 普通函数（包含实际逻辑）============

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
                    },
                    {
                        "tag": "note",
                        "elements": [{"tag": "plain_text", "content": "由客户关怀智能体自动推送"}]
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 提醒已成功推送到飞书！\n\n{reminders_text}"
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
                    },
                    {
                        "tag": "note",
                        "elements": [{"tag": "plain_text", "content": "由客户关怀智能体自动推送"}]
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return f"✅ 总结已成功推送到飞书！\n\n{summary_text}"
            else:
                return f"❌ 飞书推送失败：{result}"
        else:
            return f"❌ 飞书推送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 推送总结失败：{str(e)}"


def _push_reminders_impl(ctx=None) -> str:
    """推送提醒到飞书（兼容旧版本）"""
    return _push_morning_reminders_impl(ctx)


def _send_custom_message_impl(message: str, ctx=None) -> str:
    """发送自定义消息的实际逻辑"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": "📢 智能体消息"},
                    "template": "turquoise"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": message
                        }
                    }
                ]
            }
        }
        
        response = requests.post(webhook_url, json=card_content, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return "✅ 消息已成功发送到飞书！"
            else:
                return f"❌ 飞书发送失败：{result}"
        else:
            return f"❌ 飞书发送失败：HTTP {response.status_code}"
            
    except Exception as e:
        return f"❌ 发送消息失败：{str(e)}"


# ============ Tool函数 ============

@tool
def push_morning_reminders(runtime: ToolRuntime = None) -> str:
    """推送上午提醒（满7天及超过7天未联系的客户）"""
    ctx = runtime.context if runtime else new_context(method="push_morning_reminders")
    return _push_morning_reminders_impl(ctx)


@tool
def push_afternoon_reminders(runtime: ToolRuntime = None) -> str:
    """推送下午总结（今日已联系客户）"""
    ctx = runtime.context if runtime else new_context(method="push_afternoon_reminders")
    return _push_afternoon_reminders_impl(ctx)


@tool
def push_reminders(runtime: ToolRuntime = None) -> str:
    """推送客户提醒到飞书群"""
    ctx = runtime.context if runtime else new_context(method="push_reminders")
    return _push_reminders_impl(ctx)


@tool
def send_custom_message_to_feishu(message: str, runtime: ToolRuntime = None) -> str:
    """发送自定义消息到飞书群"""
    ctx = runtime.context if runtime else new_context(method="send_custom_message_to_feishu")
    return _send_custom_message_impl(message, ctx)
