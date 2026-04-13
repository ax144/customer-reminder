"""
人脉资源库Agent - 支持校友查询、路径规划、企业搜索和数据库操作
基于 Supabase + GitHub Actions + 飞书的客户关怀自动推送系统
"""

import os
import json
from typing import Annotated, Sequence
from langchain.agents import create_agent
from langchain_core.messages import AnyMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

# 工具导入
from tools.alumni_manager import (
    search_alumni, get_all_alumni, get_alumni_by_company, 
    get_alumni_by_position, add_alumni, update_alumni
)
from tools.company_searcher import search_company_info
from tools.path_planner import plan_connection_paths
from tools.foundation_contact_manager import (
    add_foundation_contact, update_foundation_contact
)

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40


def _windowed_messages(old: Sequence[BaseMessage], new: Sequence[BaseMessage]):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        top_p=cfg['config'].get('top_p', 0.9),
        max_completion_tokens=cfg['config'].get('max_completion_tokens', 10000),
        timeout=cfg['config'].get('timeout', 600),
        streaming=True,
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=[
            search_alumni,
            get_all_alumni,
            get_alumni_by_company,
            get_alumni_by_position,
            search_company_info,
            plan_connection_paths,
            add_alumni,
            update_alumni,
            add_foundation_contact,
            update_foundation_contact
        ],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
