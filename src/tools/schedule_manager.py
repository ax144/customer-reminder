"""
工作安排管理工具
用于管理工作安排、任务分配，支持项目关联
"""

from storage.database.supabase_client import get_supabase_admin_client
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from datetime import datetime, date
from typing import Optional, List


# ========== 内部实现函数 ==========

def _save_schedule_impl(
    title: str,
    assignee: str = None,
    project: str = None,
    content: str = None,
    priority: str = 'medium',
    due_date: str = None,
    related_customers: List[str] = None,
    related_documents: List[int] = None,
) -> str:
    """保存工作安排"""
    client = get_supabase_admin_client()
    
    try:
        schedule_data = {
            'title': title,
            'assignee': assignee,
            'project': project,
            'content': content,
            'priority': priority,
            'due_date': due_date,
            'related_customers': related_customers or [],
            'related_documents': related_documents or [],
        }
        
        # 移除None值
        schedule_data = {k: v for k, v in schedule_data.items() if v is not None}
        
        response = client.table('work_schedules').insert(schedule_data).execute()
        
        if response.data:
            return f"✅ 工作安排【{title}】已保存"
        return "❌ 保存失败"
        
    except Exception as e:
        return f"❌ 保存失败: {str(e)}"


def _query_schedule_impl(
    assignee: str = None,
    project: str = None,
    status: str = None,
    priority: str = None,
) -> str:
    """查询工作安排"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('work_schedules').select('*')
        
        if assignee:
            query = query.ilike('assignee', f'%{assignee}%')
        if project:
            query = query.ilike('project', f'%{project}%')
        if status:
            query = query.eq('status', status)
        if priority:
            query = query.eq('priority', priority)
        
        response = query.order('due_date', desc=False).order('created_at', desc=True).limit(30).execute()
        
        if not response.data:
            return "未找到匹配的工作安排"
        
        results = []
        for s in response.data:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(s.get('priority'), '⚪')
            status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}.get(s.get('status'), '❓')
            
            info = f"{priority_icon} {status_icon} 【{s['title']}】\n"
            if s.get('assignee'):
                info += f"  负责人: {s['assignee']}\n"
            if s.get('project'):
                info += f"  项目: {s['project']}\n"
            if s.get('due_date'):
                info += f"  截止日期: {s['due_date']}\n"
            if s.get('content'):
                content_preview = s['content'][:150] + '...' if len(s['content']) > 150 else s['content']
                info += f"  内容: {content_preview}\n"
            if s.get('related_customers'):
                info += f"  关联客户: {', '.join(s['related_customers'])}\n"
            results.append(info)
        
        return f"找到 {len(response.data)} 条工作安排:\n\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _update_schedule_status_impl(
    schedule_id: int = None,
    title: str = None,
    status: str = None,
) -> str:
    """更新工作安排状态"""
    client = get_supabase_admin_client()
    
    try:
        if schedule_id:
            client.table('work_schedules').update({
                'status': status,
                'updated_at': datetime.now().isoformat()
            }).eq('id', schedule_id).execute()
            return f"✅ 已更新工作安排状态为: {status}"
        elif title:
            existing = client.table('work_schedules').select('*').ilike('title', f'%{title}%').execute()
            if not existing.data:
                return f"❌ 未找到工作安排【{title}】"
            for s in existing.data:
                client.table('work_schedules').update({
                    'status': status,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', s['id']).execute()
            return f"✅ 已更新 {len(existing.data)} 条工作安排状态为: {status}"
        else:
            return "❌ 请提供工作安排ID或标题"
            
    except Exception as e:
        return f"❌ 更新失败: {str(e)}"


def _get_today_tasks_impl(assignee: str = None) -> str:
    """获取今日待办任务"""
    client = get_supabase_admin_client()
    
    try:
        today = date.today().isoformat()
        
        query = client.table('work_schedules').select('*').neq('status', 'completed')
        
        if assignee:
            query = query.ilike('assignee', f'%{assignee}%')
        
        response = query.order('priority', desc=False).order('due_date', desc=False).execute()
        
        if not response.data:
            return "✅ 今日暂无待办任务"
        
        # 筛选出今日到期或已逾期的任务
        today_tasks = []
        overdue_tasks = []
        
        for s in response.data:
            due = s.get('due_date')
            if due:
                if due < today:
                    overdue_tasks.append(s)
                elif due == today:
                    today_tasks.append(s)
        
        results = []
        
        if overdue_tasks:
            results.append("🚨 **已逾期任务**:")
            for s in overdue_tasks:
                results.append(f"  🔴 【{s['title']}】- 截止: {s['due_date']}")
        
        if today_tasks:
            results.append("\n📅 **今日到期**:")
            for s in today_tasks:
                results.append(f"  🟡 【{s['title']}】- {s.get('assignee', '未分配')}")
        
        # 显示其他进行中的任务
        other_pending = [s for s in response.data if s not in overdue_tasks and s not in today_tasks][:5]
        if other_pending:
            results.append("\n📋 **进行中任务**:")
            for s in other_pending:
                results.append(f"  ⏳ 【{s['title']}】- 截止: {s.get('due_date', '未设置')}")
        
        return "\n".join(results) if results else "✅ 今日暂无待办任务"
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _list_schedules_impl(project: str = None, status: str = None) -> str:
    """列出工作安排"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('work_schedules').select('id, title, assignee, project, status, priority, due_date')
        
        if project:
            query = query.ilike('project', f'%{project}%')
        if status:
            query = query.eq('status', status)
        
        response = query.order('created_at', desc=True).limit(30).execute()
        
        if not response.data:
            return "暂无工作安排"
        
        results = []
        for s in response.data:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(s.get('priority'), '⚪')
            status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}.get(s.get('status'), '❓')
            info = f"{priority_icon} {status_icon} [{s['id']}] {s['title']}"
            if s.get('assignee'):
                info += f" - {s['assignee']}"
            if s.get('due_date'):
                info += f" (截止: {s['due_date']})"
            results.append(info)
        
        return f"工作安排列表（共{len(response.data)}条）:\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _delete_schedule_impl(schedule_id: int = None, title: str = None) -> str:
    """删除工作安排"""
    client = get_supabase_admin_client()
    
    try:
        if schedule_id:
            client.table('work_schedules').delete().eq('id', schedule_id).execute()
            return f"✅ 已删除工作安排ID: {schedule_id}"
        elif title:
            existing = client.table('work_schedules').select('*').ilike('title', f'%{title}%').execute()
            if not existing.data:
                return f"❌ 未找到工作安排【{title}】"
            for s in existing.data:
                client.table('work_schedules').delete().eq('id', s['id']).execute()
            return f"✅ 已删除 {len(existing.data)} 条匹配的工作安排"
        else:
            return "❌ 请提供工作安排ID或标题"
            
    except Exception as e:
        return f"❌ 删除失败: {str(e)}"


# ========== Agent工具 ==========

@tool
def save_schedule(
    title: str,
    assignee: str = None,
    project: str = None,
    content: str = None,
    priority: str = 'medium',
    due_date: str = None,
    related_customers: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    保存工作安排。
    
    Args:
        title: 安排标题
        assignee: 负责人
        project: 关联项目
        content: 安排内容详情
        priority: 优先级
        due_date: 截止日期（格式：YYYY-MM-DD）
        related_customers: 关联客户姓名，用逗号分隔
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="save_schedule")
    
    # 处理关联客户
    customer_list = [c.strip() for c in related_customers.split(',')] if related_customers else None
    
    return _save_schedule_impl(
        title=title,
        assignee=assignee,
        project=project,
        content=content,
        priority=priority,
        due_date=due_date,
        related_customers=customer_list,
    )


@tool
def query_schedule(
    assignee: str = None,
    project: str = None,
    status: str = None,
    priority: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询工作安排。
    
    Args:
        assignee: 负责人
        project: 关联项目
        status: 状态
        priority: 优先级
    
    Returns:
        匹配的工作安排列表
    """
    ctx = runtime.context if runtime else new_context(method="query_schedule")
    return _query_schedule_impl(assignee, project, status, priority)


@tool
def update_schedule_status(
    status: str,
    schedule_id: int = None,
    title: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    更新工作安排状态。
    
    Args:
        status: 新状态
        schedule_id: 工作安排ID
        title: 工作安排标题（模糊匹配）
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="update_schedule_status")
    return _update_schedule_status_impl(schedule_id, title, status)


@tool
def get_today_tasks(
    assignee: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    获取今日待办任务。
    
    Args:
        assignee: 负责人（可选，不填则显示所有）
    
    Returns:
        今日待办任务列表
    """
    ctx = runtime.context if runtime else new_context(method="get_today_tasks")
    return _get_today_tasks_impl(assignee)


@tool
def list_schedules(
    project: str = None,
    status: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    列出工作安排。
    
    Args:
        project: 按项目筛选
        status: 按状态筛选
    
    Returns:
        工作安排列表
    """
    ctx = runtime.context if runtime else new_context(method="list_schedules")
    return _list_schedules_impl(project, status)


@tool
def delete_schedule(
    schedule_id: int = None,
    title: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    删除工作安排。
    
    Args:
        schedule_id: 工作安排ID
        title: 工作安排标题（模糊匹配）
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="delete_schedule")
    return _delete_schedule_impl(schedule_id, title)


__all__ = [
    # 内部实现函数
    '_save_schedule_impl',
    '_query_schedule_impl',
    '_update_schedule_status_impl',
    '_get_today_tasks_impl',
    '_list_schedules_impl',
    '_delete_schedule_impl',
    # Agent工具
    'save_schedule',
    'query_schedule',
    'update_schedule_status',
    'get_today_tasks',
    'list_schedules',
    'delete_schedule',
]
