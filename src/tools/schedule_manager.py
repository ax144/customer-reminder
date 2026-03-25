"""
工作安排与客户数据互通工具
实现工作安排与客户库之间的数据关联和同步
"""

from storage.database.supabase_client import get_supabase_admin_client
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from datetime import datetime, date
from typing import Optional, List


# ========== 内部实现函数 ==========

def _link_schedule_to_customer_impl(
    schedule_id: int,
    customer_id: int = None,
    customer_name: str = None,
) -> str:
    """
    将工作安排关联到客户
    
    Args:
        schedule_id: 工作安排ID
        customer_id: 客户ID（优先使用）
        customer_name: 客户姓名（模糊匹配）
    """
    client = get_supabase_admin_client()
    
    try:
        # 获取工作安排
        schedule = client.table('work_schedules').select('*').eq('id', schedule_id).single().execute()
        if not schedule.data:
            return f"❌ 未找到工作安排ID: {schedule_id}"
        
        # 获取客户
        customer = None
        if customer_id:
            customer = client.table('customers').select('*').eq('id', customer_id).single().execute()
        elif customer_name:
            customer = client.table('customers').select('*').ilike('name', f'%{customer_name}%').limit(1).execute()
        
        if not customer or not customer.data:
            return f"❌ 未找到客户"
        
        customer_data = customer.data if isinstance(customer.data, list) else [customer.data]
        if not customer_data:
            return f"❌ 未找到客户"
        
        target_customer = customer_data[0]
        
        # 更新工作安排的 client_name
        client.table('work_schedules').update({
            'client_name': target_customer['name']
        }).eq('id', schedule_id).execute()
        
        return f"✅ 已将【{schedule.data['task_title']}】关联到客户【{target_customer['name']}】"
        
    except Exception as e:
        return f"❌ 关联失败: {str(e)}"


def _complete_schedule_and_update_customer_impl(
    schedule_id: int = None,
    task_title: str = None,
    update_contact_date: bool = True,
    add_follow_note: str = None,
) -> str:
    """
    完成工作安排并更新客户跟进记录
    
    Args:
        schedule_id: 工作安排ID
        task_title: 任务标题（模糊匹配）
        update_contact_date: 是否更新客户的最后联系时间
        add_follow_note: 追加到客户 others 字段的备注
    """
    client = get_supabase_admin_client()
    
    try:
        # 获取工作安排
        schedule = None
        if schedule_id:
            schedule = client.table('work_schedules').select('*').eq('id', schedule_id).single().execute()
        elif task_title:
            result = client.table('work_schedules').select('*').ilike('task_title', f'%{task_title}%').limit(1).execute()
            if result.data:
                schedule = type('obj', (object,), {'data': result.data[0]})()
        
        if not schedule or not schedule.data:
            return "❌ 未找到工作安排"
        
        schedule_data = schedule.data if isinstance(schedule.data, dict) else schedule.data
        schedule_id = schedule_data['id']
        
        # 更新工作安排状态为已完成
        client.table('work_schedules').update({
            'status': 'completed',
            'updated_at': datetime.now().isoformat()
        }).eq('id', schedule_id).execute()
        
        results = [f"✅ 工作安排【{schedule_data['task_title']}】已完成"]
        
        # 如果关联了客户，更新客户记录
        client_name = schedule_data.get('client_name')
        if client_name and update_contact_date:
            # 查找客户
            customer = client.table('customers').select('*').ilike('name', f'%{client_name}%').limit(1).execute()
            
            if customer.data:
                target_customer = customer.data[0]
                today = date.today().isoformat()
                
                update_data = {
                    'last_contact_date': today,
                    'updated_at': datetime.now().isoformat()
                }
                
                # 如果有跟进备注，追加到 others 字段
                if add_follow_note:
                    existing_others = target_customer.get('others') or ''
                    new_note = f"\n[{today}] {add_follow_note}"
                    update_data['others'] = existing_others + new_note
                
                client.table('customers').update(update_data).eq('id', target_customer['id']).execute()
                results.append(f"📝 已更新客户【{target_customer['name']}】的跟进记录")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ 操作失败: {str(e)}"


def _get_customer_schedules_impl(
    customer_name: str = None,
    customer_id: int = None,
    status: str = None,
) -> str:
    """
    查询某客户的所有工作安排
    
    Args:
        customer_name: 客户姓名
        customer_id: 客户ID
        status: 筛选状态（pending/in_progress/completed）
    """
    client = get_supabase_admin_client()
    
    try:
        # 获取客户名称
        if customer_id:
            customer = client.table('customers').select('name').eq('id', customer_id).single().execute()
            if customer.data:
                customer_name = customer.data['name']
        
        if not customer_name:
            return "❌ 请提供客户姓名或ID"
        
        # 查询关联的工作安排
        query = client.table('work_schedules').select('*').ilike('client_name', f'%{customer_name}%')
        
        if status:
            query = query.eq('status', status)
        
        response = query.order('created_at', desc=True).limit(20).execute()
        
        if not response.data:
            return f"客户【{customer_name}】暂无关联的工作安排"
        
        results = [f"📋 客户【{customer_name}】的工作安排（共{len(response.data)}条）:\n"]
        
        for s in response.data:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(s.get('priority'), '⚪')
            status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}.get(s.get('status'), '❓')
            
            info = f"{priority_icon} {status_icon} [{s['id']}] {s['task_title']}\n"
            info += f"   类型: {s.get('task_type', '-')} | 负责人: {s.get('assignee', '-')}\n"
            if s.get('scheduled_date'):
                info += f"   计划日期: {s['scheduled_date']}\n"
            if s.get('notes'):
                notes_preview = s['notes'][:50] + '...' if len(s['notes']) > 50 else s['notes']
                info += f"   备注: {notes_preview}\n"
            results.append(info)
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _get_schedule_customers_impl(
    schedule_id: int,
) -> str:
    """
    查询工作安排关联的客户详情
    
    Args:
        schedule_id: 工作安排ID
    """
    client = get_supabase_admin_client()
    
    try:
        # 获取工作安排
        schedule = client.table('work_schedules').select('*').eq('id', schedule_id).single().execute()
        
        if not schedule.data:
            return f"❌ 未找到工作安排ID: {schedule_id}"
        
        client_name = schedule.data.get('client_name')
        if not client_name:
            return f"工作安排【{schedule.data['task_title']}】未关联客户"
        
        # 查询客户详情
        customers = client.table('customers').select('*').ilike('name', f'%{client_name}%').execute()
        
        if not customers.data:
            return f"未找到关联的客户【{client_name}】"
        
        results = [f"👤 工作安排【{schedule.data['task_title']}】关联的客户:\n"]
        
        for c in customers.data:
            info = f"【{c['name']}】\n"
            info += f"  公司: {c.get('company', '-')}\n"
            info += f"  职位: {c.get('position', '-')}\n"
            info += f"  直推项目: {c.get('direct_project', '-')}\n"
            info += f"  项目进度: {c.get('project_progress_1', '-')}\n"
            info += f"  最后联系: {c.get('last_contact_date', '-')}\n"
            if c.get('others'):
                others_preview = c['others'][:100] + '...' if len(c['others']) > 100 else c['others']
                info += f"  备注: {others_preview}\n"
            results.append(info)
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


def _sync_schedules_to_customers_impl(
    days: int = 30,
) -> str:
    """
    批量同步已完成的工作安排到客户记录
    
    Args:
        days: 同步最近N天内完成的任务
    """
    client = get_supabase_admin_client()
    
    try:
        # 查询最近完成的任务
        response = client.table('work_schedules').select('*').eq('status', 'completed').not_.is_('client_name', 'null').order('updated_at', desc=True).limit(50).execute()
        
        if not response.data:
            return "没有已完成且关联客户的工作安排"
        
        updated_count = 0
        
        for schedule in response.data:
            client_name = schedule.get('client_name')
            if not client_name:
                continue
            
            # 查找客户
            customer = client.table('customers').select('*').ilike('name', f'%{client_name}%').limit(1).execute()
            
            if customer.data:
                target_customer = customer.data[0]
                task_date = schedule.get('updated_at', '')[:10]  # 取完成日期
                
                # 更新客户的最后联系时间
                client.table('customers').update({
                    'last_contact_date': task_date,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', target_customer['id']).execute()
                
                updated_count += 1
        
        return f"✅ 已同步 {updated_count} 条任务记录到客户库"
        
    except Exception as e:
        return f"❌ 同步失败: {str(e)}"


# ========== Agent工具 ==========

@tool
def link_schedule_to_customer(
    schedule_id: int,
    customer_id: int = None,
    customer_name: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    将工作安排关联到客户。
    
    Args:
        schedule_id: 工作安排ID
        customer_id: 客户ID（优先使用）
        customer_name: 客户姓名（模糊匹配）
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="link_schedule_to_customer")
    return _link_schedule_to_customer_impl(schedule_id, customer_id, customer_name)


@tool
def complete_schedule_and_update_customer(
    schedule_id: int = None,
    task_title: str = None,
    update_contact_date: bool = True,
    add_follow_note: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    完成工作安排并更新客户跟进记录。
    
    任务完成后会自动：
    1. 更新任务状态为已完成
    2. 更新关联客户的最后联系时间
    3. 可选：追加跟进备注到客户记录
    
    Args:
        schedule_id: 工作安排ID
        task_title: 任务标题（模糊匹配）
        update_contact_date: 是否更新客户的最后联系时间（默认True）
        add_follow_note: 追加到客户备注的跟进内容
    
    Returns:
        操作结果
    """
    ctx = runtime.context if runtime else new_context(method="complete_schedule_and_update_customer")
    return _complete_schedule_and_update_customer_impl(schedule_id, task_title, update_contact_date, add_follow_note)


@tool
def get_customer_schedules(
    customer_name: str = None,
    customer_id: int = None,
    status: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询某客户的所有工作安排。
    
    Args:
        customer_name: 客户姓名
        customer_id: 客户ID
        status: 筛选状态
    
    Returns:
        工作安排列表
    """
    ctx = runtime.context if runtime else new_context(method="get_customer_schedules")
    return _get_customer_schedules_impl(customer_name, customer_id, status)


@tool
def get_schedule_customers(
    schedule_id: int,
    runtime: ToolRuntime = None
) -> str:
    """
    查询工作安排关联的客户详情。
    
    Args:
        schedule_id: 工作安排ID
    
    Returns:
        客户详情
    """
    ctx = runtime.context if runtime else new_context(method="get_schedule_customers")
    return _get_schedule_customers_impl(schedule_id)


@tool
def sync_schedules_to_customers(
    days: int = 30,
    runtime: ToolRuntime = None
) -> str:
    """
    批量同步已完成的工作安排到客户记录。
    
    将已完成任务的完成时间同步到关联客户的最后联系时间。
    
    Args:
        days: 同步最近N天内完成的任务（默认30天）
    
    Returns:
        同步结果
    """
    ctx = runtime.context if runtime else new_context(method="sync_schedules_to_customers")
    return _sync_schedules_to_customers_impl(days)


__all__ = [
    # 内部实现函数
    '_link_schedule_to_customer_impl',
    '_complete_schedule_and_update_customer_impl',
    '_get_customer_schedules_impl',
    '_get_schedule_customers_impl',
    '_sync_schedules_to_customers_impl',
    # Agent工具
    'link_schedule_to_customer',
    'complete_schedule_and_update_customer',
    'get_customer_schedules',
    'get_schedule_customers',
    'sync_schedules_to_customers',
]
