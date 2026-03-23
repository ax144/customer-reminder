"""
客户管家工具模块
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


def _get_reminders_impl(ctx=None) -> str:
    """获取提醒事项（满7天及超过7天未联系的客户）"""
    try:
        client = get_supabase_client()
        today = _get_beijing_today()
        seven_days_ago = today - timedelta(days=7)
        
        no_contact_list = []
        reminded_keys = set()
        
        all_result = client.table("customers").select(
            "id, name, company, position, direct_project, project_progress_1, last_contact_date"
        ).execute()
        
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
                    "project_progress_1": str(c.get('project_progress_1', '')),
                    "lc": lcd,
                    "lc_obj": lc_obj
                })
        
        no_contact_list.sort(
            key=lambda x: (1, today) if x.get('lc_obj') is None else (0, x['lc_obj'])
        )
        
        parts = []
        
        if no_contact_list:
            parts.append(f"⏰ **满7天及超过7天未联系** (共{len(no_contact_list)}人)\n")
            for c in no_contact_list:
                progress = c.get('project_progress_1', '') if c.get('project_progress_1') else ''
                proj_info = f"【项目推进：{progress}】" if progress else ""
                ls = f"（最后联系：{c['lc']}）" if c['lc'] else "（从未联系）"
                parts.append(f"• **{c['name']}** - {c['company']} {proj_info} {ls}")
        
        return "\n".join(parts) if parts else "✅ 今日暂无提醒事项"
        
    except Exception as e:
        return f"❌ 检查提醒失败：{str(e)}"


def _get_today_contacted_impl(ctx=None) -> str:
    """获取今日已联系的客户"""
    try:
        client = get_supabase_client()
        today = _get_beijing_today()
        
        today_str = today.isoformat()
        tomorrow_str = (today + timedelta(days=1)).isoformat()
        
        result = client.table("customers").select(
            "id, name, company, project_progress_1"
        ).gte("last_contact_date", today_str).lt("last_contact_date", tomorrow_str).execute()
        
        if not result.data:
            return "📊 **今日联系总结**\n\n📭 今天还没有联系客户记录"
        
        parts = []
        parts.append(f"📊 **今日联系总结**\n")
        parts.append(f"✅ 今天已联系 **{len(result.data)}** 位客户\n")
        
        for c in result.data:
            progress = c.get('project_progress_1', '') if c.get('project_progress_1') else ''
            proj_info = f"【项目推进：{progress}】" if progress else ""
            parts.append(f"• **{c.get('name', '')}** - {c.get('company', '')} {proj_info}")
        
        return "\n".join(parts)
        
    except Exception as e:
        return f"❌ 获取今日联系记录失败：{str(e)}"
