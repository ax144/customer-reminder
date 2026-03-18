"""
飞书消息推送工具模块
- push_reminders_to_feishu: 推送提醒到飞书
- send_custom_message_to_feishu: 发送自定义消息到飞书
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
import os
import requests
from datetime import datetime
from typing import Optional

# ============ 普通函数（包含实际逻辑）============

def _push_reminders_to_feishu_impl(ctx=None) -> str:
    """推送提醒到飞书的实际逻辑"""
    try:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        if not webhook_url:
            return "❌ 未配置飞书Webhook URL"
        
        from src.tools.customer_manager import _check_reminders_impl
        reminders_text = _check_reminders_impl(days_ahead=7, ctx=ctx)
        
        today = datetime.now().strftime("%Y年%m月%d日")
        
        card_content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": f"📅 {today} 客户提醒"},
                    "template": "blue"
                },
                "elements": [
                    {"tag": "markdown", "content": reminders_text},
                    {"tag": "note", "elements": [{"tag": "plain_text", "content": "由全能销售与人脉智能体自动推送"}]}
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
                "elements": [{"tag": "markdown", "content": message}]
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
def push_reminders_to_feishu(runtime: ToolRuntime = None) -> str:
    """推送今日提醒到飞书群"""
    ctx = runtime.context if runtime else new_context(method="push_reminders_to_feishu")
    return _push_reminders_to_feishu_impl(ctx)


@tool
def send_custom_message_to_feishu(message: str, runtime: ToolRuntime = None) -> str:
    """发送自定义消息到飞书群"""
    ctx = runtime.context if runtime else new_context(method="send_custom_message_to_feishu")
    return _send_custom_message_impl(message, ctx)
