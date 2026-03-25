"""
文档库管理工具
用于管理分析报告、需求文档等资料，支持关键词检索

数据库表结构：
- id: 主键
- doc_type: 文档类型（分析报告、客户清单、需求文档等）
- title: 文档标题
- content: 文档内容
- tags: 标签数组
- client_name: 关联客户/项目
- file_url: 文件URL
"""

from storage.database.supabase_client import get_supabase_admin_client
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from datetime import datetime
from typing import Optional, List


# ========== 内部实现函数 ==========

def _save_document_impl(
    title: str,
    doc_type: str,
    content: str = None,
    tags: List[str] = None,
    client_name: str = None,
    file_url: str = None,
) -> str:
    """保存文档到文档库"""
    client = get_supabase_admin_client()
    
    try:
        doc_data = {
            'title': title,
            'doc_type': doc_type,
            'content': content,
            'tags': tags or [],
        }
        
        # 添加可选字段
        if client_name:
            doc_data['client_name'] = client_name
        if file_url:
            doc_data['file_url'] = file_url
        
        response = client.table('documents').insert(doc_data).execute()
        
        if response.data:
            return f"✅ 文档【{title}】已保存到文档库"
        return "❌ 保存失败"
        
    except Exception as e:
        return f"❌ 保存失败: {str(e)}"


def _query_document_impl(
    keyword: str = None,
    doc_type: str = None,
    client_name: str = None,
) -> str:
    """查询文档库"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('documents').select('*')
        
        if doc_type:
            query = query.eq('doc_type', doc_type)
        if client_name:
            query = query.ilike('client_name', f'%{client_name}%')
        
        response = query.order('created_at', desc=True).limit(20).execute()
        
        if not response.data:
            return "未找到匹配的文档"
        
        # 如果有关键词，在结果中筛选
        if keyword:
            keyword_lower = keyword.lower()
            filtered = []
            for doc in response.data:
                # 检查标题、内容、标签数组
                if (keyword_lower in doc.get('title', '').lower() or
                    keyword_lower in (doc.get('content') or '').lower() or
                    any(keyword_lower in str(k).lower() for k in (doc.get('tags') or []))):
                    filtered.append(doc)
            response.data = filtered
        
        if not response.data:
            return f"未找到包含关键词「{keyword}」的文档"
        
        results = []
        for doc in response.data:
            tags_str = ', '.join(doc.get('tags') or [])
            info = f"【{doc['title']}】\n"
            info += f"  类型: {doc.get('doc_type', '未分类')}\n"
            if doc.get('client_name'):
                info += f"  客户/项目: {doc['client_name']}\n"
            if tags_str:
                info += f"  标签: {tags_str}\n"
            if doc.get('content'):
                content_preview = doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content']
                info += f"  摘要: {content_preview}\n"
            info += f"  创建时间: {doc.get('created_at', '')}"
            results.append(info)
        
        return f"找到 {len(response.data)} 份文档:\n\n" + "\n\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _list_documents_impl(doc_type: str = None, limit: int = 20) -> str:
    """列出文档库中的所有文档"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('documents').select('id, title, doc_type, client_name, created_at')
        
        if doc_type:
            query = query.eq('doc_type', doc_type)
        
        response = query.order('created_at', desc=True).limit(limit).execute()
        
        if not response.data:
            return "文档库为空"
        
        results = []
        for doc in response.data:
            info = f"- [{doc['id']}] {doc['title']}"
            if doc.get('doc_type'):
                info += f" ({doc['doc_type']})"
            results.append(info)
        
        return f"文档库列表（共{len(response.data)}份）:\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _delete_document_impl(doc_id: int = None, title: str = None) -> str:
    """删除文档"""
    client = get_supabase_admin_client()
    
    try:
        if doc_id:
            client.table('documents').delete().eq('id', doc_id).execute()
            return f"✅ 已删除文档ID: {doc_id}"
        elif title:
            existing = client.table('documents').select('*').ilike('title', f'%{title}%').execute()
            if not existing.data:
                return f"❌ 未找到文档【{title}】"
            for doc in existing.data:
                client.table('documents').delete().eq('id', doc['id']).execute()
            return f"✅ 已删除 {len(existing.data)} 份匹配的文档"
        else:
            return "❌ 请提供文档ID或标题"
            
    except Exception as e:
        return f"❌ 删除失败: {str(e)}"


# ========== Agent工具 ==========

@tool
def save_document(
    title: str,
    doc_type: str,
    content: str = None,
    tags: str = None,
    client_name: str = None,
    file_url: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    保存文档到文档库。
    
    Args:
        title: 文档标题
        doc_type: 文档类型（如：分析报告、需求文档、客户清单、会议纪要等）
        content: 文档内容摘要
        tags: 标签，用逗号分隔
        client_name: 关联客户或项目名称
        file_url: 文件URL
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="save_document")
    
    # 处理标签
    tag_list = [k.strip() for k in tags.split(',')] if tags else None
    
    return _save_document_impl(
        title=title,
        doc_type=doc_type,
        content=content,
        tags=tag_list,
        client_name=client_name,
        file_url=file_url,
    )


@tool
def query_document(
    keyword: str = None,
    doc_type: str = None,
    client_name: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询文档库。
    
    Args:
        keyword: 搜索关键词（匹配标题、内容、标签）
        doc_type: 文档类型
        client_name: 关联客户或项目名称
    
    Returns:
        匹配的文档列表
    """
    ctx = runtime.context if runtime else new_context(method="query_document")
    return _query_document_impl(keyword, doc_type, client_name)


@tool
def list_documents(
    doc_type: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    列出文档库中的所有文档。
    
    Args:
        doc_type: 按类型筛选（可选）
    
    Returns:
        文档列表
    """
    ctx = runtime.context if runtime else new_context(method="list_documents")
    return _list_documents_impl(doc_type)


@tool
def delete_document(
    doc_id: int = None,
    title: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    删除文档。
    
    Args:
        doc_id: 文档ID
        title: 文档标题（模糊匹配）
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="delete_document")
    return _delete_document_impl(doc_id, title)


__all__ = [
    # 内部实现函数
    '_save_document_impl',
    '_query_document_impl',
    '_list_documents_impl',
    '_delete_document_impl',
    # Agent工具
    'save_document',
    'query_document',
    'list_documents',
    'delete_document',
]
