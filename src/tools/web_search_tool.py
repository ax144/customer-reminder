"""
联网搜索工具模块
用于人脉路径规划时搜索目标人物和公司的公开信息
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
import os

@tool
def web_search(query: str, runtime: ToolRuntime = None) -> str:
    """
    联网搜索公开信息
    
    用途：
    - 搜索目标人物和公司的基本信息
    - 搜索公司的投资方、合作方、行业关系
    - 搜索行业协会、政府关系、媒体报道
    
    Args:
        query: 搜索关键词，例如：
            - "科大讯飞 投资方 合作方"
            - "蔚来汽车 行业协会 合肥"
            - "某某公司 政府关系 招商"
    
    Returns:
        搜索结果信息
    """
    ctx = runtime.context if runtime else new_context(method="web_search")
    
    try:
        # 使用coze-coding-dev-sdk的搜索能力
        from coze_coding_dev_sdk import CozeClient
        
        # 获取API配置
        api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL", "https://api.coze.cn")
        
        if not api_key:
            return "❌ 未配置API Key，无法执行搜索"
        
        # 创建客户端
        client = CozeClient(api_key=api_key, base_url=base_url)
        
        # 执行搜索
        result = client.web_search(query=query, ctx=ctx)
        
        if not result or not result.get("results"):
            return f"📭 未找到关于「{query}」的相关信息"
        
        # 格式化输出
        output = f"🔍 搜索「{query}」的结果：\n\n"
        
        for i, item in enumerate(result.get("results", [])[:5], 1):
            title = item.get("title", "无标题")
            url = item.get("url", "")
            snippet = item.get("snippet", "") or item.get("content", "")
            
            output += f"**{i}. {title}**\n"
            if snippet:
                # 限制摘要长度
                snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet
                output += f"   {snippet}\n"
            if url:
                output += f"   🔗 {url}\n"
            output += "\n"
        
        return output
        
    except ImportError:
        # 如果SDK不可用，使用简单的requests搜索
        try:
            import requests
            
            # 使用DuckDuckGo的即时答案API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            output = f"🔍 搜索「{query}」的结果：\n\n"
            
            # 提取摘要
            if data.get("Abstract"):
                output += f"📖 摘要：\n{data['Abstract']}\n\n"
            
            # 提取相关主题
            related_topics = data.get("RelatedTopics", [])[:5]
            for i, topic in enumerate(related_topics, 1):
                if isinstance(topic, dict) and topic.get("Text"):
                    output += f"**{i}.** {topic['Text'][:200]}\n\n"
            
            if not data.get("Abstract") and not related_topics:
                return f"📭 未找到关于「{query}」的相关信息"
            
            return output
            
        except Exception as e:
            return f"❌ 搜索失败：{str(e)}"
            
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"
