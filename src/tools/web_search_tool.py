"""
网络搜索工具
使用coze-coding-dev-sdk进行网络搜索
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from typing import Optional, List, Dict, Any

try:
    from coze_coding_dev_sdk import SearchClient
    HAS_SEARCH_SDK = True
except ImportError:
    HAS_SEARCH_SDK = False


def _format_search_results(response: Any) -> str:
    """格式化搜索结果"""
    result_text = "## 🔍 网络搜索结果\n\n"
    
    if hasattr(response, 'summary') and response.summary:
        result_text += "### 📋 AI摘要\n"
        result_text += f"{response.summary}\n\n"
    
    if hasattr(response, 'web_items') and response.web_items:
        result_text += "### 📄 搜索结果\n\n"
        for i, item in enumerate(response.web_items[:10], 1):
            result_text += f"#### {i}. {item.title or '无标题'}\n"
            if item.site_name:
                result_text += f"- **来源**: {item.site_name}\n"
            if item.url:
                result_text += f"- **链接**: {item.url}\n"
            if item.snippet:
                snippet = item.snippet[:200] + "..." if len(item.snippet) > 200 else item.snippet
                result_text += f"- **摘要**: {snippet}\n"
            if item.publish_time:
                result_text += f"- **发布时间**: {item.publish_time}\n"
            result_text += "\n"
        
        if len(response.web_items) > 10:
            result_text += f"---\n还有 {len(response.web_items) - 10} 条结果未显示\n"
    
    return result_text


@tool
def web_search(
    query: str,
    count: Optional[int] = 10,
    need_summary: Optional[bool] = True,
    runtime: ToolRuntime = None
) -> str:
    """
    网络搜索工具 - 搜索互联网获取实时信息
    
    Args:
        query: 搜索关键词
        count: 返回结果数量（默认10条）
        need_summary: 是否需要AI生成的摘要（默认是）
    
    Returns:
        格式化的搜索结果
    """
    ctx = runtime.context if runtime else new_context(method="web_search")
    
    if not HAS_SEARCH_SDK:
        return "❌ 搜索SDK不可用，请先安装coze-coding-dev-sdk"
    
    try:
        client = SearchClient(ctx=ctx)
        
        if need_summary:
            response = client.web_search_with_summary(query=query, count=count)
        else:
            response = client.web_search(query=query, count=count, need_summary=False)
        
        return _format_search_results(response)
        
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"


@tool
def search_company_info(
    company_name: str,
    runtime: ToolRuntime = None
) -> str:
    """
    搜索公司信息 - 获取公司的投资方、合作方、高管信息等
    
    Args:
        company_name: 公司名称
    
    Returns:
        公司相关信息
    """
    ctx = runtime.context if runtime else new_context(method="search_company_info")
    
    if not HAS_SEARCH_SDK:
        return "❌ 搜索SDK不可用，请先安装coze-coding-dev-sdk"
    
    try:
        client = SearchClient(ctx=ctx)
        
        # 搜索公司基本信息
        query1 = f"{company_name} 公司简介 投资方 合作方"
        response1 = client.web_search_with_summary(query=query1, count=5)
        
        # 搜索公司高管信息
        query2 = f"{company_name} 高管 董事长 总经理 联系方式"
        response2 = client.web_search_with_summary(query=query2, count=5)
        
        result_text = f"## 🏢 {company_name} 信息搜索\n\n"
        
        if response1.summary:
            result_text += "### 📋 公司概况\n"
            result_text += f"{response1.summary}\n\n"
        
        if response2.summary:
            result_text += "### 👥 高管信息\n"
            result_text += f"{response2.summary}\n\n"
        
        # 合并搜索结果
        all_items = []
        if response1.web_items:
            all_items.extend(response1.web_items[:5])
        if response2.web_items:
            all_items.extend(response2.web_items[:5])
        
        if all_items:
            result_text += "### 📄 详细来源\n\n"
            seen_urls = set()
            for i, item in enumerate(all_items, 1):
                if item.url and item.url in seen_urls:
                    continue
                if item.url:
                    seen_urls.add(item.url)
                
                result_text += f"#### {i}. {item.title or '无标题'}\n"
                if item.site_name:
                    result_text += f"- **来源**: {item.site_name}\n"
                if item.url:
                    result_text += f"- **链接**: {item.url}\n"
                if item.snippet:
                    snippet = item.snippet[:150] + "..." if len(item.snippet) > 150 else item.snippet
                    result_text += f"- **摘要**: {snippet}\n"
                result_text += "\n"
        
        return result_text
        
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"


@tool
def search_government_alumni(
    government_agency: str,
    city: str = "合肥",
    runtime: ToolRuntime = None
) -> str:
    """
    搜索政府部门中的校友信息 - 查找特定城市特定政府部门的安财校友
    
    Args:
        government_agency: 政府部门名称（如"财政局"、"审计局"、"经信局"）
        city: 城市名称（默认合肥）
    
    Returns:
        相关搜索结果
    """
    ctx = runtime.context if runtime else new_context(method="search_government_alumni")
    
    if not HAS_SEARCH_SDK:
        return "❌ 搜索SDK不可用，请先安装coze-coding-dev-sdk"
    
    try:
        client = SearchClient(ctx=ctx)
        
        query = f"{city}{government_agency} 安徽财经大学 校友"
        response = client.web_search_with_summary(query=query, count=10)
        
        result_text = f"## 🔍 {city}{government_agency} 校友搜索\n\n"
        
        if response.summary:
            result_text += "### 📋 AI摘要\n"
            result_text += f"{response.summary}\n\n"
        
        if response.web_items:
            result_text += "### 📄 搜索结果\n\n"
            for i, item in enumerate(response.web_items, 1):
                result_text += f"#### {i}. {item.title or '无标题'}\n"
                if item.site_name:
                    result_text += f"- **来源**: {item.site_name}\n"
                if item.url:
                    result_text += f"- **链接**: {item.url}\n"
                if item.snippet:
                    snippet = item.snippet[:200] + "..." if len(item.snippet) > 200 else item.snippet
                    result_text += f"- **摘要**: {snippet}\n"
                result_text += "\n"
        
        return result_text
        
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"


# 导出
__all__ = [
    'web_search',
    'search_company_info',
    'search_government_alumni',
]
