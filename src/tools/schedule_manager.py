"""
工作安排管理工具
用于管理工作安排、任务分配，支持项目关联

数据库表结构：
- id: 主键
- assignee: 负责人
- task_type: 任务类型（必填）
- task_title: 任务标题
- task_description: 任务描述
- client_name: 关联客户
- scheduled_date: 计划日期
- scheduled_time: 计划时间
- priority: 优先级
- status: 状态
- reminder_enabled: 是否提醒
- notes: 备注
"""

from storage.database.supabase_client import get_supabase_admin_client
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from datetime import datetime, date
from typing import Optional, List


# ========== 内部实现函数 ==========

def _save_schedule_impl(
    task_title: str,
    task_type: str,
    assignee: str = None,
    task_description: str = None,
    client_name: str = None,
    scheduled_date: str = None,
    scheduled_time: str = None,
    priority: str = 'medium',
    notes: str = None,
    reminder_enabled: bool = False,
) -> str:
    """保存工作安排"""
    client = get_supabase_admin_client()
    
    try:
        schedule_data = {
            'task_title': task_title,
            'task_type': task_type,
            'priority': priority,
            'reminder_enabled': reminder_enabled,
        }
        
        # 添加可选字段
        if assignee:
            schedule_data['assignee'] = assignee
        if task_description:
            schedule_data['task_description'] = task_description
        if client_name:
            schedule_data['client_name'] = client_name
        if scheduled_date:
            schedule_data['scheduled_date'] = scheduled_date
        if scheduled_time:
            schedule_data['scheduled_time'] = scheduled_time
        if notes:
            schedule_data['notes'] = notes
        
        response = client.table('work_schedules').insert(schedule_data).execute()
        
        if response.data:
            return f"✅ 工作安排【{task_title}】已保存"
        return "❌ 保存失败"
        
    except Exception as e:
        return f"❌ 保存失败: {str(e)}"


def _query_schedule_impl(
    assignee: str = None,
    task_type: str = None,
    status: str = None,
    priority: str = None,
    client_name: str = None,
) -> str:
    """查询工作安排"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('work_schedules').select('*')
        
        if assignee:
            query = query.ilike('assignee', f'%{assignee}%')
        if task_type:
            query = query.eq('task_type', task_type)
        if status:
            query = query.eq('status', status)
        if priority:
            query = query.eq('priority', priority)
        if client_name:
            query = query.ilike('client_name', f'%{client_name}%')
        
        response = query.order('scheduled_date', desc=False).order('created_at', desc=True).limit(30).execute()
        
        if not response.data:
            return "未找到匹配的工作安排"
        
        results = []
        for s in response.data:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(s.get('priority'), '⚪')
            status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}.get(s.get('status'), '❓')
            
            info = f"{priority_icon} {status_icon} 【{s['task_title']}】\n"
            info += f"  类型: {s.get('task_type', '-')}\n"
            if s.get('assignee'):
                info += f"  负责人: {s['assignee']}\n"
            if s.get('client_name'):
                info += f"  关联客户: {s['client_name']}\n"
            if s.get('scheduled_date'):
                time_str = f" {s['scheduled_time']}" if s.get('scheduled_time') else ""
                info += f"  计划时间: {s['scheduled_date']}{time_str}\n"
            if s.get('notes'):
                notes_preview = s['notes'][:100] + '...' if len(s['notes']) > 100 else s['notes']
                info += f"  备注: {notes_preview}\n"
            results.append(info)
        
        return f"找到 {len(response.data)} 条工作安排:\n\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _update_schedule_status_impl(
    schedule_id: int = None,
    task_title: str = None,
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
        elif task_title:
            existing = client.table('work_schedules').select('*').ilike('task_title', f'%{task_title}%').execute()
            if not existing.data:
                return f"❌ 未找到工作安排【{task_title}】"
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
        
        response = query.order('priority', desc=False).order('scheduled_date', desc=False).execute()
        
        if not response.data:
            return "✅ 今日暂无待办任务"
        
        # 筛选出今日到期或已逾期的任务
        today_tasks = []
        overdue_tasks = []
        
        for s in response.data:
            due = s.get('scheduled_date')
            if due:
                if due < today:
                    overdue_tasks.append(s)
                elif due == today:
                    today_tasks.append(s)
        
        results = []
        
        if overdue_tasks:
            results.append("🚨 **已逾期任务**:")
            for s in overdue_tasks:
                results.append(f"  🔴 【{s['task_title']}】- 截止: {s['scheduled_date']}")
        
        if today_tasks:
            results.append("\n📅 **今日到期**:")
            for s in today_tasks:
                results.append(f"  🟡 【{s['task_title']}】- {s.get('assignee', '未分配')}")
        
        # 显示其他进行中的任务
        other_pending = [s for s in response.data if s not in overdue_tasks and s not in today_tasks][:5]
        if other_pending:
            results.append("\n📋 **进行中任务**:")
            for s in other_pending:
                results.append(f"  ⏳ 【{s['task_title']}】- 截止: {s.get('scheduled_date', '未设置')}")
        
        return "\n".join(results) if results else "✅ 今日暂无待办任务"
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _list_schedules_impl(assignee: str = None, status: str = None, task_type: str = None) -> str:
    """列出工作安排"""
    client = get_supabase_admin_client()
    
    try:
        query = client.table('work_schedules').select('id, task_title, task_type, assignee, status, priority, scheduled_date')
        
        if assignee:
            query = query.ilike('assignee', f'%{assignee}%')
        if status:
            query = query.eq('status', status)
        if task_type:
            query = query.eq('task_type', task_type)
        
        response = query.order('created_at', desc=True).limit(30).execute()
        
        if not response.data:
            return "暂无工作安排"
        
        results = []
        for s in response.data:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(s.get('priority'), '⚪')
            status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}.get(s.get('status'), '❓')
            info = f"{priority_icon} {status_icon} [{s['id']}] {s['task_title']}"
            if s.get('assignee'):
                info += f" - {s['assignee']}"
            if s.get('scheduled_date'):
                info += f" (截止: {s['scheduled_date']})"
            results.append(info)
        
        return f"工作安排列表（共{len(response.data)}条）:\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _delete_schedule_impl(schedule_id: int = None, task_title: str = None) -> str:
    """删除工作安排"""
    client = get_supabase_admin_client()
    
    try:
        if schedule_id:
            client.table('work_schedules').delete().eq('id', schedule_id).execute()
            return f"✅ 已删除工作安排ID: {schedule_id}"
        elif task_title:
            existing = client.table('work_schedules').select('*').ilike('task_title', f'%{task_title}%').execute()
            if not existing.data:
                return f"❌ 未找到工作安排【{task_title}】"
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
    task_title: str,
    task_type: str,
    assignee: str = None,
    task_description: str = None,
    client_name: str = None,
    scheduled_date: str = None,
    scheduled_time: str = None,
    priority: str = 'medium',
    notes: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    保存工作安排。
    
    Args:
        task_title: 任务标题
        task_type: 任务类型（如：项目跟进、客户拜访、需求调研、会议等）
        assignee: 负责人
        task_description: 任务描述详情
        client_name: 关联客户名称
        scheduled_date: 计划日期（格式：YYYY-MM-DD）
        scheduled_time: 计划时间（格式：HH:MM）
        priority: 优先级
        notes: 备注信息
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="save_schedule")
    
    return _save_schedule_impl(
        task_title=task_title,
        task_type=task_type,
        assignee=assignee,
        task_description=task_description,
        client_name=client_name,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        priority=priority,
        notes=notes,
    )


@tool
def query_schedule(
    assignee: str = None,
    task_type: str = None,
    status: str = None,
    priority: str = None,
    client_name: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询工作安排。
    
    Args:
        assignee: 负责人
        task_type: 任务类型
        status: 状态
        priority: 优先级
        client_name: 关联客户名称
    
    Returns:
        匹配的工作安排列表
    """
    ctx = runtime.context if runtime else new_context(method="query_schedule")
    return _query_schedule_impl(assignee, task_type, status, priority, client_name)


@tool
def update_schedule_status(
    status: str,
    schedule_id: int = None,
    task_title: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    更新工作安排状态。
    
    Args:
        status: 新状态
        schedule_id: 工作安排ID
        task_title: 任务标题（模糊匹配）
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="update_schedule_status")
    return _update_schedule_status_impl(schedule_id, task_title, status)


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
    assignee: str = None,
    status: str = None,
    task_type: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    列出工作安排。
    
    Args:
        assignee: 按负责人筛选
        status: 按状态筛选
        task_type: 按任务类型筛选
    
    Returns:
        工作安排列表
    """
    ctx = runtime.context if runtime else new_context(method="list_schedules")
    return _list_schedules_impl(assignee, status, task_type)


@tool
def delete_schedule(
    schedule_id: int = None,
    task_title: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    删除工作安排。
    
    Args:
        schedule_id: 工作安排ID
        task_title: 任务标题（模糊匹配）
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="delete_schedule")
    return _delete_schedule_impl(schedule_id, task_title)


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
