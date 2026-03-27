"""
全能销售与人脉智能体 - 主Agent模块
集成客户管家、销售军师、人脉导航三大核心职能
"""

import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers

from storage.memory import get_memory_saver
from tools.customer_manager import (
    save_customer, query_customer, get_reminders, 
    mark_contacted, delete_customer, update_project_progress
)
from tools.notification_pusher import (
    push_reminders, push_morning_reminders, 
    push_afternoon_reminders, send_custom_message_to_feishu
)
from tools.alumni_manager import (
    search_alumni, get_all_alumni, 
    get_alumni_by_company, get_alumni_by_position
)
from tools.web_search_tool import (
    web_search, search_company_info, search_government_alumni
)

# 配置文件路径
LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近20轮对话(40条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近MAX_MESSAGES条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    """构建Agent实例"""
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    # 读取配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # 获取API配置
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    # 构建LLM实例
    llm = ChatOpenAI(
        model=cfg['config'].get("model", "doubao-seed-2-0-pro-260215"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking_type', 'enabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )
    
    # 注册所有工具
    tools = [
        save_customer,
        query_customer,
        get_reminders,
        mark_contacted,
        delete_customer,
        update_project_progress,
        push_reminders,
        push_morning_reminders,
        push_afternoon_reminders,
        send_custom_message_to_feishu,
        search_alumni,
        get_all_alumni,
        get_alumni_by_company,
        get_alumni_by_position,
        web_search,
        search_company_info,
        search_government_alumni
    ]
    
    # 创建并返回Agent
    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp", ""),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
