"""客户管家工具模块"""

from storage.database.supabase_client import get_supabase_client
from datetime import datetime, timedelta


def _get_beijing_today():
    return (datetime.utcnow() + timedelta(hours=8)).date()


def _get_reminders_impl(ctx=None) -> str:
    """获取提醒（满7天未联系的客户）"""
    try:
        client = get_supabase_client()
        today = _get_beijing_today()
        seven_days_ago = today - timedelta(days=7)
        
        result = client.table("customers").select("name, company, project_progress_1, last_contact_date").execute()
        
        no_contact_list = []
        for c in result.data:
            name = c.get('name', '')
            if not name:
                continue
            
            lc = c.get('last_contact_date')
            remind = False
            lc_obj = None
            
            if not lc:
                remind = True
            else:
                try:
                    lcs = str(lc).split('T')[0]
                    lc_obj = datetime.strptime(lcs, "%Y-%m-%d").date()
                    if lc_obj <= seven_days_ago:
                        remind = True
                except:
                    remind = True
            
            if remind:
                lcd = str(lc).split('T')[0] if lc else ""
                no_contact_list.append({
                    "name": name,
                    "company": c.get('company', ''),
                    "progress": c.get('project_progress_1', ''),
                    "lc": lcd,
                    "lc_obj": lc_obj
                })
        
        no_contact_list.sort(key=lambda x: (1, today) if x.get('lc_obj') is None else (0, x['lc_obj']))
        
        if no_contact_list:
            parts = [f"⏰ **满7天未联系** (共{len(no_contact_list)}人)\n"]
            for c in no_contact_list:
                progress = f"【项目推进：{c['progress']}】" if c['progress'] else ""
                ls = f"（最后联系：{c['lc']}）" if c['lc'] else "（从未联系）"
                parts.append(f"• **{c['name']}** - {c['company']} {progress} {ls}")
            return "\n".join(parts)
        return "✅ 今日暂无提醒"
    except Exception as e:
        return f"❌ 查询失败：{str(e)}"


def _get_today_contacted_impl(ctx=None) -> str:
    """获取今日已联系的客户"""
    try:
        client = get_supabase_client()
        today = _get_beijing_today()
        
        result = client.table("customers").select("name, company, project_progress_1").gte("last_contact_date", today.isoformat()).lt("last_contact_date", (today + timedelta(days=1)).isoformat()).execute()
        
        if not result.data:
            return "📊 **今日联系总结**\n\n📭 今天还没有联系客户"
        
        parts = [f"📊 **今日联系总结**\n", f"✅ 今天已联系 **{len(result.data)}** 位客户\n"]
        for c in result.data:
            progress = f"【项目推进：{c.get('project_progress_1', '')}】" if c.get('project_progress_1') else ""
            parts.append(f"• **{c.get('name', '')}** - {c.get('company', '')} {progress}")
        return "\n".join(parts)
    except Exception as e:
        return f"❌ 查询失败：{str(e)}"
