"""
客户管家工具模块
适配新的客户资源表结构
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from storage.database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


def _get_beijing_now():
    utc_now = datetime.utcnow()
    return utc_now + timedelta(hours=8)


def _get_beijing_today():
    return _get_beijing_now().date()


# ============ 普通函数（包含实际逻辑）============

def _save_customer_impl(
    name: str,
    company: Optional[str] = None,
    position: Optional[str] = None,
    referrer: Optional[str] = None,
    direct_project: Optional[str] = None,
    project_progress_1: Optional[str] = None,
    extended_project: Optional[str] = None,
    project_progress_2: Optional[str] = None,
    others: Optional[str] = None,
    last_contact_date: Optional[str] = None,
    ctx=None
) -> str:
    """保存或更新客户信息"""
    try:
        client = get_supabase_client()
        
        customer_data: Dict[str, Any] = {
            "name": name,
            "company": company,
            "position": position,
            "referrer": referrer,
            "direct_project": direct_project,
            "project_progress_1": project_progress_1,
            "extended_project": extended_project,
            "project_progress_2": project_progress_2,
            "others": others,
            "last_contact_date": last_contact_date,
            "updated_at": datetime.now().isoformat()
        }
        
        # 移除 None 值
        customer_data = {k: v for k, v in customer_data.items() if v is not None}
        
        # 检查是否已存在（按姓名+公司去重）
        query = client.table("customers").select("id").eq("name", name)
        if company:
            query = query.eq("company", company)
        
        existing = query.execute()
        
        if existing.data:
            # 更新
            client.table("customers").update(customer_data).eq("id", existing.data[0]["id"]).execute()
            return f"✅ 客户信息已更新：{name}"
        else:
            # 新增
            customer_data["created_at"] = datetime.now().isoformat()
            result = client.table("customers").insert(customer_data).execute()
            return f"✅ 新客户已保存：{name}"
            
    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


def _query_customer_impl(
    name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 10,
    ctx=None
) -> str:
    """查询客户信息"""
    try:
        client = get_supabase_client()
        
        query = client.table("customers").select("*")
        
        if name:
            query = query.ilike("name", f"%{name}%")
        if company:
            query = query.ilike("company", f"%{company}%")
        if position:
            query = query.ilike("position", f"%{position}%")
        
        result = query.limit(limit).order("updated_at", desc=True).execute()
        
        if not result.data:
            return "📭 未找到匹配的客户信息"
        
        output = f"📋 找到 {len(result.data)} 条客户记录：\n\n"
        
        for i, c in enumerate(result.data, 1):
            output += f"**{i}. {c.get('name', '')}**\n"
            if c.get('company'):
                output += f"   🏢 {c['company']}\n"
            if c.get('position'):
                output += f"   💼 {c['position']}\n"
            if c.get('direct_project'):
                output += f"   📌 直推项目: {c['direct_project']}\n"
            if c.get('last_contact_date'):
                output += f"   📅 最后联系: {c['last_contact_date']}\n"
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"❌ 查询失败：{str(e)}"


def _get_reminders_impl(ctx=None) -> str:
    """获取提醒事项（满7天及超过7天未联系的客户）"""
    try:
        client = get_supabase_client()
        today = _get_beijing_today()
        seven_days_ago = today - timedelta(days=7)
        
        print(f"[DEBUG] 北京时间今天: {today}")
        print(f"[DEBUG] 7天前: {seven_days_ago}")
        
        no_contact_list = []
        reminded_keys = set()
        
        # 查询所有客户（新表结构）
        all_result = client.table("customers").select(
            "id, name, company, position, direct_project, project_progress_1, last_contact_date"
        ).execute()
        
        print(f"[DEBUG] 总客户数: {len(all_result.data)}")
        
        for c in all_result.data:
            name = str(c.get('name', ''))
            if not name:
                continue
            
            key = f"{name}_{c.get('company', '')}"
            if key in reminded_keys:
                continue
            
            lc = c.get('last_contact_date')
            remind = False
            lc_obj = None
            
            if not lc:
                remind = True
            else:
                try:
                    lcs = str(lc)
                    if 'T' in lcs:
                        lcs = lcs.split('T')[0]
                    lc_obj = datetime.strptime(lcs, "%Y-%m-%d").date()
                    if lc_obj <= seven_days_ago:
                        remind = True
                except:
                    remind = True
            
            if remind:
                reminded_keys.add(key)
                lcd = ""
                if lc:
                    try:
                        lcs = str(lc)
                        if 'T' in lcs:
                            lcs = lcs.split('T')[0]
                        lcd = lcs
                    except:
                        lcd = str(lc)
                
                no_contact_list.append({
                    "name": name,
                    "company": str(c.get('company', '')),
                    "position": str(c.get('position', '')),
                    "direct_project": str(c.get('direct_project', '')),
                    "project_progress_1": str(c.get('project_progress_1', '')),
                    "lc": lcd,
                    "lc_obj": lc_obj
                })
        
        # 排序：按最后联系时间升序（最久未联系的排前面）
        no_contact_list.sort(
            key=lambda x: (1, today) if x.get('lc_obj') is None else (0, x['lc_obj'])
        )
        
        # 输出
        parts = []
        
        if no_contact_list:
            parts.append(f"⏰ **满7天及超过7天未联系** (共{len(no_contact_list)}人)\n")
            for c in no_contact_list:
                # 项目推进（显示项目进展）
                progress = c.get('project_progress_1', '') if c.get('project_progress_1') else ''
                proj_info = f"【项目推进：{progress}】" if progress else ""
                ls = f"（最后联系：{c['lc']}）" if c['lc'] else "（从未联系）"
                parts.append(f"• **{c['name']}** - {c['company']} {proj_info} {ls}")
        
        return "\n".join(parts) if parts else "✅ 今日暂无提醒事项"
        
    except Exception as e:
        return f"❌ 检查提醒失败：{str(e)}"


def _mark_contacted_impl(name: str, company: Optional[str] = None, ctx=None) -> str:
    """标记客户为已联系"""
    try:
        client = get_supabase_client()
        
        query = client.table("customers").select("id, name, company").eq("name", name)
        if company:
            query = query.eq("company", company)
        
        result = query.execute()
        
        if not result.data:
            return f"❌ 未找到客户：{name}"
        
        client.table("customers").update({
            "last_contact_date": _get_beijing_today().isoformat(),
            "updated_at": _get_beijing_now().isoformat()
        }).eq("id", result.data[0]["id"]).execute()
        
        return f"✅ 已标记 {name} 为已联系"
        
    except Exception as e:
        return f"❌ 标记失败：{str(e)}"


def _delete_customer_impl(name: str, company: Optional[str] = None, ctx=None) -> str:
    """删除客户"""
    try:
        client = get_supabase_client()
        
        query = client.table("customers").select("id").eq("name", name)
        if company:
            query = query.eq("company", company)
        
        result = query.execute()
        
        if not result.data:
            return f"❌ 未找到客户：{name}"
        
        client.table("customers").delete().eq("id", result.data[0]["id"]).execute()
        
        return f"✅ 已删除客户：{name}"
        
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


def _update_project_progress_impl(
    name: str,
    project_progress_1: Optional[str] = None,
    project_progress_2: Optional[str] = None,
    company: Optional[str] = None,
    ctx=None
) -> str:
    """更新项目进展"""
    try:
        client = get_supabase_client()
        
        query = client.table("customers").select("id, name").eq("name", name)
        if company:
            query = query.eq("company", company)
        
        result = query.execute()
        
        if not result.data:
            return f"❌ 未找到客户：{name}"
        
        update_data = {"updated_at": datetime.now().isoformat()}
        if project_progress_1:
            update_data["project_progress_1"] = project_progress_1
        if project_progress_2:
            update_data["project_progress_2"] = project_progress_2
        
        client.table("customers").update(update_data).eq("id", result.data[0]["id"]).execute()
        
        return f"✅ 已更新 {name} 的项目进展"
        
    except Exception as e:
        return f"❌ 更新失败：{str(e)}"


# ============ Tool函数 ============

@tool
def save_customer(
    name: str,
    company: Optional[str] = None,
    position: Optional[str] = None,
    referrer: Optional[str] = None,
    direct_project: Optional[str] = None,
    project_progress_1: Optional[str] = None,
    extended_project: Optional[str] = None,
    project_progress_2: Optional[str] = None,
    others: Optional[str] = None,
    last_contact_date: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """保存或更新客户信息"""
    ctx = runtime.context if runtime else new_context(method="save_customer")
    return _save_customer_impl(
        name, company, position, referrer, direct_project,
        project_progress_1, extended_project, project_progress_2,
        others, last_contact_date, ctx
    )


@tool
def query_customer(
    name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 10,
    runtime: ToolRuntime = None
) -> str:
    """查询客户信息"""
    ctx = runtime.context if runtime else new_context(method="query_customer")
    return _query_customer_impl(name, company, position, limit, ctx)


@tool
def get_reminders(runtime: ToolRuntime = None) -> str:
    """获取未联系客户提醒（满7天及超过7天未联系）"""
    ctx = runtime.context if runtime else new_context(method="get_reminders")
    return _get_reminders_impl(ctx)


@tool
def mark_contacted(name: str, company: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """标记客户为已联系"""
    ctx = runtime.context if runtime else new_context(method="mark_contacted")
    return _mark_contacted_impl(name, company, ctx)


@tool
def delete_customer(name: str, company: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """删除客户"""
    ctx = runtime.context if runtime else new_context(method="delete_customer")
    return _delete_customer_impl(name, company, ctx)


@tool
def update_project_progress(
    name: str,
    project_progress_1: Optional[str] = None,
    project_progress_2: Optional[str] = None,
    company: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """更新客户项目进展"""
    ctx = runtime.context if runtime else new_context(method="update_project_progress")
    return _update_project_progress_impl(name, project_progress_1, project_progress_2, company, ctx)
