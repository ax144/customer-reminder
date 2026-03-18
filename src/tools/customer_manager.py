"""
客户管家工具模块
- save_customer_info: 保存/更新客户信息
- query_customer_info: 查询客户信息
- check_reminders: 检查提醒事项（简洁版）
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from src.storage.database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
from typing import Optional

# ============ 普通函数（包含实际逻辑）============

def _save_customer_info_impl(
    name: str,
    company: Optional[str] = None,
    position: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    wechat: Optional[str] = None,
    birthday: Optional[str] = None,
    source: Optional[str] = None,
    notes: Optional[str] = None,
    last_contact_date: Optional[str] = None,
    next_follow_up_date: Optional[str] = None,
    relationship_strength: Optional[str] = None,
    ctx=None
) -> str:
    """保存客户信息的实际逻辑"""
    try:
        client = get_supabase_client(ctx)
        
        customer_data = {
            "name": name,
            "company": company,
            "position": position,
            "phone": phone,
            "email": email,
            "wechat": wechat,
            "birthday": birthday,
            "source": source,
            "notes": notes,
            "last_contact_date": last_contact_date,
            "next_follow_up_date": next_follow_up_date,
            "relationship_strength": relationship_strength,
            "updated_at": datetime.now().isoformat()
        }
        
        customer_data = {k: v for k, v in customer_data.items() if v is not None}
        
        existing = client.table("customers").select("id").eq("name", name).execute()
        
        if existing.data:
            customer_id = existing.data[0]["id"]
            client.table("customers").update(customer_data).eq("id", customer_id).execute()
            return f"✅ 客户信息已更新：{name} (ID: {customer_id})"
        else:
            customer_data["created_at"] = datetime.now().isoformat()
            result = client.table("customers").insert(customer_data).execute()
            customer_id = result.data[0]["id"]
            return f"✅ 新客户已保存：{name} (ID: {customer_id})"
            
    except Exception as e:
        return f"❌ 保存客户信息失败：{str(e)}"


def _query_customer_info_impl(
    name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    relationship_strength: Optional[str] = None,
    limit: int = 10,
    ctx=None
) -> str:
    """查询客户信息的实际逻辑"""
    try:
        client = get_supabase_client(ctx)
        
        query = client.table("customers").select("*")
        
        if name:
            query = query.ilike("name", f"%{name}%")
        if company:
            query = query.ilike("company", f"%{company}%")
        if position:
            query = query.ilike("position", f"%{position}%")
        if relationship_strength:
            query = query.eq("relationship_strength", relationship_strength)
        
        result = query.limit(limit).order("updated_at", desc=True).execute()
        
        if not result.data:
            return "📭 未找到匹配的客户信息"
        
        output = f"📋 找到 {len(result.data)} 条客户记录：\n\n"
        for i, customer in enumerate(result.data, 1):
            output += f"**{i}. {customer['name']}**\n"
            if customer.get('company'):
                output += f"   🏢 公司：{customer['company']}\n"
            if customer.get('position'):
                output += f"   💼 职位：{customer['position']}\n"
            if customer.get('phone'):
                output += f"   📞 电话：{customer['phone']}\n"
            if customer.get('wechat'):
                output += f"   💬 微信：{customer['wechat']}\n"
            if customer.get('relationship_strength'):
                output += f"   🔗 关系强度：{customer['relationship_strength']}\n"
            if customer.get('last_contact_date'):
                output += f"   📅 最后联系：{customer['last_contact_date']}\n"
            if customer.get('next_follow_up_date'):
                output += f"   ⏰ 下次跟进：{customer['next_follow_up_date']}\n"
            if customer.get('notes'):
                output += f"   📝 备注：{customer['notes']}\n"
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"❌ 查询客户信息失败：{str(e)}"


def _check_reminders_impl(days_ahead: int = 7, ctx=None) -> str:
    """检查提醒事项的实际逻辑（简洁版：只显示今天和明天）"""
    try:
        client = get_supabase_client(ctx)
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        birthday_today = []
        birthday_tomorrow = []
        follow_up_today = []
        cold_customers = []
        
        # 1. 检查生日提醒（今天和明天）
        birthday_customers = client.table("customers").select("name, birthday, company, position").not_.is_("birthday", "null").execute()
        
        for customer in birthday_customers.data:
            if customer['birthday']:
                birthday_date = datetime.strptime(customer['birthday'], "%Y-%m-%d").date()
                this_year_birthday = birthday_date.replace(year=today.year)
                
                # 检查今天生日
                if this_year_birthday == today:
                    birthday_today.append({
                        "name": customer['name'],
                        "company": customer.get('company', ''),
                        "position": customer.get('position', '')
                    })
                # 检查明天生日
                elif this_year_birthday == tomorrow:
                    birthday_tomorrow.append({
                        "name": customer['name'],
                        "company": customer.get('company', ''),
                        "position": customer.get('position', '')
                    })
        
        # 2. 检查今天需要跟进的客户
        follow_up_customers = client.table("customers").select("*").eq("next_follow_up_date", today.isoformat()).execute()
        
        for customer in follow_up_customers.data:
            follow_up_today.append({
                "name": customer['name'],
                "company": customer.get('company', ''),
                "position": customer.get('position', ''),
                "notes": customer.get('notes', '')
            })
        
        # 3. 检查超过7天未联系的客户
        seven_days_ago = (today - timedelta(days=7)).isoformat()
        cold_customers_data = client.table("customers").select("*").or_(f"last_contact_date.is.null,last_contact_date.lt.{seven_days_ago}").limit(10).execute()
        
        for customer in cold_customers_data.data:
            if customer.get('last_contact_date'):
                last_date = datetime.strptime(customer['last_contact_date'], "%Y-%m-%d").date()
                days_passed = (today - last_date).days
                cold_customers.append({
                    "name": customer['name'],
                    "company": customer.get('company', ''),
                    "days_passed": days_passed
                })
            else:
                cold_customers.append({
                    "name": customer['name'],
                    "company": customer.get('company', ''),
                    "days_passed": 999  # 从未联系
                })
        
        # 构建简洁的输出
        output_parts = []
        
        # 生日提醒
        if birthday_today:
            output_parts.append("🎂 **今天生日**")
            for customer in birthday_today:
                output_parts.append(f"• {customer['name']} - {customer['company']} {customer['position']}")
            output_parts.append("")
        
        if birthday_tomorrow:
            output_parts.append("🎂 **明天生日**")
            for customer in birthday_tomorrow:
                output_parts.append(f"• {customer['name']} - {customer['company']} {customer['position']}")
            output_parts.append("")
        
        # 跟进提醒
        if follow_up_today:
            output_parts.append("⏰ **今天跟进**")
            for customer in follow_up_today:
                output_parts.append(f"• {customer['name']} - {customer['company']}")
            output_parts.append("")
        
        # 久未联系
        if cold_customers:
            output_parts.append("❄️ **超过7天未联系**")
            for customer in cold_customers[:5]:  # 最多显示5个
                if customer['days_passed'] == 999:
                    output_parts.append(f"• {customer['name']} - {customer['company']}（从未联系）")
                else:
                    output_parts.append(f"• {customer['name']} - {customer['company']}（{customer['days_passed']}天）")
            output_parts.append("")
        
        if not output_parts:
            return "✅ 今日暂无提醒事项"
        
        return "\n".join(output_parts)
        
    except Exception as e:
        return f"❌ 检查提醒失败：{str(e)}"


# ============ Tool函数（调用普通函数）============

@tool
def save_customer_info(
    name: str,
    company: Optional[str] = None,
    position: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    wechat: Optional[str] = None,
    birthday: Optional[str] = None,
    source: Optional[str] = None,
    notes: Optional[str] = None,
    last_contact_date: Optional[str] = None,
    next_follow_up_date: Optional[str] = None,
    relationship_strength: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """保存或更新客户信息到数据库"""
    ctx = runtime.context if runtime else new_context(method="save_customer_info")
    return _save_customer_info_impl(
        name, company, position, phone, email, wechat,
        birthday, source, notes, last_contact_date,
        next_follow_up_date, relationship_strength, ctx
    )


@tool
def query_customer_info(
    name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    relationship_strength: Optional[str] = None,
    limit: int = 10,
    runtime: ToolRuntime = None
) -> str:
    """查询客户信息"""
    ctx = runtime.context if runtime else new_context(method="query_customer_info")
    return _query_customer_info_impl(name, company, position, relationship_strength, limit, ctx)


@tool
def check_reminders(days_ahead: int = 7, runtime: ToolRuntime = None) -> str:
    """检查需要提醒的事项（生日、跟进提醒等）"""
    ctx = runtime.context if runtime else new_context(method="check_reminders")
    return _check_reminders_impl(days_ahead, ctx)
