"""
客户管家工具模块
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from storage.database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, cast


def _get_beijing_now():
    utc_now = datetime.utcnow()
    return utc_now + timedelta(hours=8)


def _get_beijing_today():
    return _get_beijing_now().date()


def _save_customer_info_impl(name: str, company: Optional[str] = None, position: Optional[str] = None,
    phone: Optional[str] = None, email: Optional[str] = None, wechat: Optional[str] = None,
    birthday: Optional[str] = None, source: Optional[str] = None, notes: Optional[str] = None,
    last_contact_date: Optional[str] = None, next_follow_up_date: Optional[str] = None,
    relationship_strength: Optional[str] = None, ctx=None) -> str:
    try:
        client = get_supabase_client()
        customer_data: Dict[str, Any] = {"name": name, "company": company, "position": position,
            "phone": phone, "email": email, "wechat": wechat, "birthday": birthday, "source": source,
            "notes": notes, "last_contact_date": last_contact_date, "next_follow_up_date": next_follow_up_date,
            "relationship_strength": relationship_strength, "updated_at": datetime.now().isoformat()}
        customer_data = {k: v for k, v in customer_data.items() if v is not None}
        query = client.table("customers").select("id").eq("name", name)
        if phone: query = query.eq("phone", phone)
        existing = query.execute()
        if existing.data:
            client.table("customers").update(customer_data).eq("id", existing.data[0]["id"]).execute()
            return f"✅ 客户信息已更新：{name}"
        customer_data["created_at"] = datetime.now().isoformat()
        result = client.table("customers").insert(customer_data).execute()
        return f"✅ 新客户已保存：{name}"
    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


def _query_customer_info_impl(name: Optional[str] = None, company: Optional[str] = None,
    position: Optional[str] = None, relationship_strength: Optional[str] = None,
    limit: int = 10, ctx=None) -> str:
    try:
        client = get_supabase_client()
        query = client.table("customers").select("*")
        if name: query = query.ilike("name", f"%{name}%")
        if company: query = query.ilike("company", f"%{company}%")
        if position: query = query.ilike("position", f"%{position}%")
        if relationship_strength: query = query.eq("relationship_strength", relationship_strength)
        result = query.limit(limit).order("updated_at", desc=True).execute()
        if not result.data: return "📭 未找到匹配的客户信息"
        output = f"📋 找到 {len(result.data)} 条客户记录：\n\n"
        for i, c in enumerate(result.data, 1):
            output += f"**{i}. {c.get('name', '')}**\n"
            if c.get('company'): output += f"   🏢 {c['company']}\n"
            if c.get('phone'): output += f"   📞 {c['phone']}\n"
            output += "\n"
        return output
    except Exception as e:
        return f"❌ 查询失败：{str(e)}"


def _get_morning_reminders_impl(ctx=None) -> str:
    try:
        client = get_supabase_client()
        today = _get_beijing_today()
        seven_days_ago = today - timedelta(days=7)
        
        print(f"[DEBUG] 北京时间今天: {today}")
        print(f"[DEBUG] 7天前: {seven_days_ago}")
        
        birthday_today = []
        no_contact_list = []
        birthday_keys = set()
        grace_keys = set()
        reminded_keys = set()
        
        # 查询有生日记录的客户
        result = client.table("customers").select("name, birthday, company, position, phone").not_.is_("birthday", "null").execute()
        print(f"[DEBUG] 有生日记录的客户数: {len(result.data)}")
        
        today_md = today.strftime('%m-%d')
        print(f"[DEBUG] 今天月日: {today_md}")
        
        for c in result.data:
            name = str(c.get('name', ''))
            if c.get('birthday'):
                try:
                    bs = str(c['birthday'])
                    if 'T' in bs: bs = bs.split('T')[0]
                    cmd = bs[5:10] if len(bs) >= 5 else ""
                    phone = str(c.get('phone', ''))
                    key = f"{name}_{phone}"
                    
                    # 打印每个人的生日匹配情况
                    print(f"[DEBUG] {name}: birthday={bs}, cmd={cmd}, today={today_md}, match={cmd==today_md}")
                    
                    if cmd == today_md:
                        print(f"[DEBUG] ⭐ 找到今天生日: {name}")
                        if key not in birthday_keys:
                            birthday_keys.add(key)
                            birthday_today.append({"name": name, "company": str(c.get('company', '')), "position": str(c.get('position', '')), "phone": phone})
                    
                    bd = datetime.strptime(bs, "%Y-%m-%d").date()
                    tyb = bd.replace(year=today.year)
                    dsb = (today - tyb).days
                    if 0 <= dsb <= 2:
                        grace_keys.add(key)
                except Exception as ex:
                    print(f"[DEBUG] 生日解析错误: {name} - {ex}")
        
        print(f"[DEBUG] 今天生日人数: {len(birthday_today)}")
        
        # 查询超过7天未联系
        all_result = client.table("customers").select("name, company, phone, last_contact_date").execute()
        for c in all_result.data:
            name = str(c.get('name', ''))
            phone = str(c.get('phone', ''))
            if not name: continue
            key = f"{name}_{phone}"
            if key in reminded_keys or key in birthday_keys or key in grace_keys: continue
            
            lc = c.get('last_contact_date')
            remind = False
            lc_obj = None
            if not lc:
                remind = True
            else:
                try:
                    lcs = str(lc)
                    if 'T' in lcs: lcs = lcs.split('T')[0]
                    lc_obj = datetime.strptime(lcs, "%Y-%m-%d").date()
                    if lc_obj <= seven_days_ago: remind = True
                except: remind = True
            
            if remind:
                reminded_keys.add(key)
                lcd = ""
                if lc:
                    try:
                        lcs = str(lc)
                        if 'T' in lcs: lcs = lcs.split('T')[0]
                        lcd = lcs
                    except: lcd = str(lc)
                no_contact_list.append({"name": name, "company": str(c.get('company', '')), "phone": phone, "lc": lcd, "lc_obj": lc_obj})
        
        # 排序
        no_contact_list.sort(key=lambda x: (1, today) if x.get('lc_obj') is None else (0, x['lc_obj']))
        
        # 输出
        parts = []
        if birthday_today:
            parts.append("🎂 **今天生日**\n")
            for c in birthday_today:
                ps = f" 📞{c['phone']}" if c.get('phone') else ""
                parts.append(f"• {c['name']} - {c['company']} {c['position']}{ps}")
            parts.append("\n")
        
        if no_contact_list:
            parts.append(f"⏰ **满7天及超过7天未联系** (共{len(no_contact_list)}人)\n")
            for c in no_contact_list:
                ps = f" 📞{c['phone']}" if c.get('phone') else ""
                ls = f"（最后联系：{c['lc']}）" if c['lc'] else "（从未联系）"
                parts.append(f"• {c['name']} - {c['company']}{ps} {ls}")
        
        return "\n".join(parts) if parts else "✅ 今日暂无提醒事项"
    except Exception as e:
        return f"❌ 检查提醒失败：{str(e)}"


def _get_afternoon_reminders_impl(ctx=None) -> str:
    try:
        client = get_supabase_client()
        today = _get_beijing_today()
        tomorrow = today + timedelta(days=1)
        
        print(f"[DEBUG] 下午推送 - 今天: {today}, 明天: {tomorrow}")
        
        contacted = []
        bday_tmr = []
        contacted_keys = set()
        bday_tmr_keys = set()
        
        # 今天已联系
        cr = client.table("customers").select("name, company").eq("last_contact_date", today.isoformat()).execute()
        print(f"[DEBUG] 今天已联系客户数: {len(cr.data)}")
        for c in cr.data:
            name = str(c.get('name', ''))
            key = f"{name}_{c.get('phone', '')}"
            if key not in contacted_keys:
                contacted_keys.add(key)
                contacted.append({"name": name, "company": str(c.get('company', ''))})
        
        # 明天生日
        tomorrow_md = tomorrow.strftime('%m-%d')
        print(f"[DEBUG] 明天月日: {tomorrow_md}")
        br = client.table("customers").select("name, birthday, company, position, phone").not_.is_("birthday", "null").execute()
        for c in br.data:
            if c.get('birthday'):
                try:
                    bs = str(c['birthday'])
                    if 'T' in bs: bs = bs.split('T')[0]
                    cmd = bs[5:10] if len(bs) >= 5 else ""
                    if cmd == tomorrow_md:
                        name = str(c.get('name', ''))
                        phone = str(c.get('phone', ''))
                        key = f"{name}_{phone}"
                        if key not in bday_tmr_keys:
                            print(f"[DEBUG] 找到明天生日: {name}")
                            bday_tmr_keys.add(key)
                            bday_tmr.append({"name": name, "company": str(c.get('company', '')), "position": str(c.get('position', '')), "phone": phone})
                except: pass
        
        print(f"[DEBUG] 明天生日人数: {len(bday_tmr)}")
        
        parts = []
        if contacted:
            parts.append("📊 **今日已联系客户**\n")
            for c in contacted: parts.append(f"• {c['name']} - {c['company']}")
            parts.append(f"\n✅ 今天已联系 **{len(contacted)}** 位客户\n")
        
        if bday_tmr:
            parts.append("🎂 **明天生日**\n")
            for c in bday_tmr:
                ps = f" 📞{c['phone']}" if c.get('phone') else ""
                parts.append(f"• {c['name']} - {c['company']} {c['position']}{ps}")
        
        return "\n".join(parts) if parts else "✅ 今日暂无提醒事项"
    except Exception as e:
        return f"❌ 检查失败：{str(e)}"


def _check_reminders_impl(days_ahead: int = 7, ctx=None) -> str:
    return _get_morning_reminders_impl(ctx)


def _mark_contacted_impl(name: str, phone: Optional[str] = None, ctx=None) -> str:
    try:
        client = get_supabase_client()
        query = client.table("customers").select("id, name, company").eq("name", name)
        if phone: query = query.eq("phone", phone)
        result = query.execute()
        if not result.data: return f"❌ 未找到客户：{name}"
        client.table("customers").update({"last_contact_date": _get_beijing_today().isoformat(), "updated_at": _get_beijing_now().isoformat()}).eq("id", result.data[0]["id"]).execute()
        return f"✅ 已标记 {name} 为已联系"
    except Exception as e:
        return f"❌ 标记失败：{str(e)}"


def _delete_customer_impl(name: str, phone: Optional[str] = None, reason: Optional[str] = None, ctx=None) -> str:
    try:
        client = get_supabase_client()
        query = client.table("customers").select("id").eq("name", name)
        if phone: query = query.eq("phone", phone)
        result = query.execute()
        if not result.data: return f"❌ 未找到客户：{name}"
        client.table("customers").delete().eq("id", result.data[0]["id"]).execute()
        return f"✅ 已删除客户：{name}"
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


@tool
def save_customer_info(name: str, company: Optional[str] = None, position: Optional[str] = None,
    phone: Optional[str] = None, email: Optional[str] = None, wechat: Optional[str] = None,
    birthday: Optional[str] = None, source: Optional[str] = None, notes: Optional[str] = None,
    last_contact_date: Optional[str] = None, next_follow_up_date: Optional[str] = None,
    relationship_strength: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """保存或更新客户信息"""
    ctx = runtime.context if runtime else new_context(method="save_customer_info")
    return _save_customer_info_impl(name, company, position, phone, email, wechat, birthday, source, notes, last_contact_date, next_follow_up_date, relationship_strength, ctx)


@tool
def query_customer_info(name: Optional[str] = None, company: Optional[str] = None,
    position: Optional[str] = None, relationship_strength: Optional[str] = None,
    limit: int = 10, runtime: ToolRuntime = None) -> str:
    """查询客户信息"""
    ctx = runtime.context if runtime else new_context(method="query_customer_info")
    return _query_customer_info_impl(name, company, position, relationship_strength, limit, ctx)


@tool
def check_reminders(days_ahead: int = 7, runtime: ToolRuntime = None) -> str:
    """检查需要提醒的事项"""
    ctx = runtime.context if runtime else new_context(method="check_reminders")
    return _check_reminders_impl(days_ahead, ctx)


@tool
def mark_contacted(name: str, phone: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """标记客户为已联系"""
    ctx = runtime.context if runtime else new_context(method="mark_contacted")
    return _mark_contacted_impl(name, phone, ctx)


@tool
def delete_customer(name: str, phone: Optional[str] = None, reason: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """删除客户"""
    ctx = runtime.context if runtime else new_context(method="delete_customer")
    return _delete_customer_impl(name, phone, reason, ctx)
