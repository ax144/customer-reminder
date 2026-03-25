"""
文档库管理工具
用于管理分析报告、需求文档等资料，支持关键词检索
"""

from storage.database.supabase_client import get_supabase_admin_client
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from datetime import datetime
from typing import Optional, List


# ========== 内部实现函数 ==========

def _save_document_impl(
    title: str,
    category: str,
    content: str = None,
    keywords: List[str] = None,
    file_path: str = None,
    file_url: str = None,
    project: str = None,
) -> str:
    """保存文档到文档库"""
    client = get_supabase_admin_client()
    
    try:
        doc_data = {
            'title': title,
            'category': category,
            'content': content,
            'keywords': keywords or [],
            'file_path': file_path,
            'file_url': file_url,
            'project': project,
        }
        
        # 移除None值
        doc_data = {k: v for k, v in doc_data.items() if v is not None}
        
        response = client.table('documents').insert(doc_data).execute()
        
        if response.data:
            return f"✅ 文档【{title}】已保存到文档库"
        return "❌ 保存失败"
        
    except Exception as e:
        return f"❌ 保存失败: {str(e)}"


def _query_document_impl(
    keyword: str = None,
    category: str = None,
    project: str = None,
) -> str:
    """查询文档库"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('documents').select('*')
        
        if category:
            query = query.eq('category', category)
        if project:
            query = query.ilike('project', f'%{project}%')
        
        response = query.order('created_at', desc=True).limit(20).execute()
        
        if not response.data:
            return "未找到匹配的文档"
        
        # 如果有关键词，在结果中筛选
        if keyword:
            keyword_lower = keyword.lower()
            filtered = []
            for doc in response.data:
                # 检查标题、内容、关键词数组
                if (keyword_lower in doc.get('title', '').lower() or
                    keyword_lower in (doc.get('content') or '').lower() or
                    any(keyword_lower in str(k).lower() for k in (doc.get('keywords') or []))):
                    filtered.append(doc)
            response.data = filtered
        
        if not response.data:
            return f"未找到包含关键词「{keyword}」的文档"
        
        results = []
        for doc in response.data:
            keywords_str = ', '.join(doc.get('keywords') or [])
            info = f"【{doc['title']}】\n"
            info += f"  分类: {doc.get('category', '未分类')}\n"
            if doc.get('project'):
                info += f"  项目: {doc['project']}\n"
            if keywords_str:
                info += f"  关键词: {keywords_str}\n"
            if doc.get('content'):
                content_preview = doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content']
                info += f"  摘要: {content_preview}\n"
            info += f"  创建时间: {doc.get('created_at', '')}"
            results.append(info)
        
        return f"找到 {len(response.data)} 份文档:\n\n" + "\n\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _list_documents_impl(category: str = None, limit: int = 20) -> str:
    """列出文档库中的所有文档"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('documents').select('id, title, category, project, created_at')
        
        if category:
            query = query.eq('category', category)
        
        response = query.order('created_at', desc=True).limit(limit).execute()
        
        if not response.data:
            return "文档库为空"
        
        results = []
        for doc in response.data:
            info = f"- [{doc['id']}] {doc['title']}"
            if doc.get('category'):
                info += f" ({doc['category']})"
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
    category: str,
    content: str = None,
    keywords: str = None,
    file_path: str = None,
    file_url: str = None,
    project: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    保存文档到文档库。
    
    Args:
        title: 文档标题
        category: 文档分类（如：分析报告、需求文档、方案文档、会议纪要等）
        content: 文档内容摘要
        keywords: 关键词，用逗号分隔
        file_path: 原始文件路径
        file_url: 文件URL
        project: 关联项目
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="save_document")
    
    # 处理关键词
    keyword_list = [k.strip() for k in keywords.split(',')] if keywords else None
    
    return _save_document_impl(
        title=title,
        category=category,
        content=content,
        keywords=keyword_list,
        file_path=file_path,
        file_url=file_url,
        project=project,
    )


@tool
def query_document(
    keyword: str = None,
    category: str = None,
    project: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询文档库。
    
    Args:
        keyword: 搜索关键词（匹配标题、内容、关键词）
        category: 文档分类
        project: 关联项目
    
    Returns:
        匹配的文档列表
    """
    ctx = runtime.context if runtime else new_context(method="query_document")
    return _query_document_impl(keyword, category, project)


@tool
def list_documents(
    category: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    列出文档库中的所有文档。
    
    Args:
        category: 按分类筛选（可选）
    
    Returns:
        文档列表
    """
    ctx = runtime.context if runtime else new_context(method="list_documents")
    return _list_documents_impl(category)


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
