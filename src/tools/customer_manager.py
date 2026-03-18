"""
客户管家工具模块
- save_customer_info: 保存/更新客户信息
- query_customer_info: 查询客户信息
- check_reminders: 检查提醒事项
- get_morning_reminders: 上午推送（今天生日 + 超过7天未联系）
- get_afternoon_reminders: 下午推送（今天联系总结 + 明天生日）
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from storage.database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, cast

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
        client = get_supabase_client()
        
        customer_data: Dict[str, Any] = {
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
        
        # 过滤掉None值
        customer_data = {k: v for k, v in customer_data.items() if v is not None}
        
        # 检查客户是否已存在（按name + phone组合判断）
        query = client.table("customers").select("id").eq("name", name)
        if phone:
            query = query.eq("phone", phone)
        existing = query.execute()
        existing_data = cast(List[Dict[str, Any]], existing.data)
        
        if existing_data:
            customer_id = existing_data[0]["id"]
            client.table("customers").update(customer_data).eq("id", customer_id).execute()
            return f"✅ 客户信息已更新：{name} (ID: {customer_id})"
        else:
            customer_data["created_at"] = datetime.now().isoformat()
            result = client.table("customers").insert(customer_data).execute()
            result_data = cast(List[Dict[str, Any]], result.data)
            customer_id = result_data[0]["id"]
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
        client = get_supabase_client()
        
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
        result_data = cast(List[Dict[str, Any]], result.data)
        
        if not result_data:
            return "📭 未找到匹配的客户信息"
        
        output = f"📋 找到 {len(result_data)} 条客户记录：\n\n"
        for i, customer in enumerate(result_data, 1):
            output += f"**{i}. {customer.get('name', '')}**\n"
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


def _get_morning_reminders_impl(ctx=None) -> str:
    """
    上午推送：今天生日 + 满7天及超过7天未联系的客户
    逻辑：最后联系日期 <= 今天 - 7天
    去重逻辑：按 name + phone 组合去重（支持同名不同客户）
    
    示例：
    - 今天是2026/3/18，7天前是2026/3/11
    - 最后联系2026/3/11的客户，今天满7天，需要联系
    - 最后联系2026/3/10的客户，已超过7天，也需要联系（避免错过）
    """
    try:
        client = get_supabase_client()
        
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=7)
        
        birthday_today: List[Dict[str, str]] = []
        no_contact_over_7_days: List[Dict[str, str]] = []
        
        # 用于去重的集合（使用 name+phone 组合）
        birthday_keys: set = set()
        reminded_keys: set = set()
        
        # 1. 检查今天生日的客户
        birthday_result = client.table("customers").select("name, birthday, company, position, phone").not_.is_("birthday", "null").execute()
        birthday_data = cast(List[Dict[str, Any]], birthday_result.data)
        
        for customer in birthday_data:
            if customer.get('birthday'):
                try:
                    birthday_date = datetime.strptime(str(customer['birthday']), "%Y-%m-%d").date()
                    this_year_birthday = birthday_date.replace(year=today.year)
                    
                    if this_year_birthday == today:
                        name = str(customer.get('name', ''))
                        phone = str(customer.get('phone', ''))
                        # 使用 name+phone 组合作为唯一标识
                        unique_key = f"{name}_{phone}"
                        
                        if unique_key not in birthday_keys:
                            birthday_keys.add(unique_key)
                            birthday_today.append({
                                "name": name,
                                "company": str(customer.get('company', '')),
                                "position": str(customer.get('position', '')),
                                "phone": phone
                            })
                except:
                    pass
        
        # 2. 检查超过7天未联系的客户（自动计算）
        all_result = client.table("customers").select("name, company, position, phone, last_contact_date, birthday").execute()
        all_data = cast(List[Dict[str, Any]], all_result.data)
        
        for customer in all_data:
            name = str(customer.get('name', ''))
            phone = str(customer.get('phone', ''))
            if not name:
                continue
            
            # 使用 name+phone 组合作为唯一标识
            unique_key = f"{name}_{phone}"
            
            # 去重：避免重复添加
            if unique_key in reminded_keys:
                continue
            
            # 排除今天生日的客户（避免重复）
            if unique_key in birthday_keys:
                continue
            
            last_contact = customer.get('last_contact_date')
            should_remind = False
            
            if not last_contact:
                # 从未联系过，需要跟进
                should_remind = True
            else:
                # 检查是否超过7天（包括第7天）
                try:
                    # 处理不同的日期格式
                    last_contact_str = str(last_contact)
                    # 如果包含时间部分，只取日期部分
                    if 'T' in last_contact_str:
                        last_contact_str = last_contact_str.split('T')[0]
                    
                    last_contact_date_obj = datetime.strptime(last_contact_str, "%Y-%m-%d").date()
                    # 提醒满7天及超过7天的客户（避免错过提醒）
                    if last_contact_date_obj <= seven_days_ago:
                        should_remind = True
                except Exception as e:
                    # 日期格式错误，也提醒
                    should_remind = True
            
            if should_remind:
                reminded_keys.add(unique_key)
                # 格式化最后联系日期
                last_contact_display = ""
                if last_contact:
                    try:
                        last_contact_str = str(last_contact)
                        if 'T' in last_contact_str:
                            last_contact_str = last_contact_str.split('T')[0]
                        last_contact_display = last_contact_str
                    except:
                        last_contact_display = str(last_contact)
                
                no_contact_over_7_days.append({
                    "name": name,
                    "company": str(customer.get('company', '')),
                    "position": str(customer.get('position', '')),
                    "phone": phone,
                    "last_contact_date": last_contact_display
                })
        
        # 构建输出
        output_parts: List[str] = []
        
        # 生日提醒
        if birthday_today:
            output_parts.append("🎂 **今天生日**\n")
            for customer in birthday_today:
                phone_str = f" 📞{customer['phone']}" if customer.get('phone') else ""
                output_parts.append(f"• {customer['name']} - {customer['company']} {customer['position']}{phone_str}")
            output_parts.append("\n")
        
        # 满7天及超过7天未联系
        if no_contact_over_7_days:
            output_parts.append(f"⏰ **满7天及超过7天未联系** (共{len(no_contact_over_7_days)}人)\n")
            for customer in no_contact_over_7_days:
                phone_str = f" 📞{customer['phone']}" if customer.get('phone') else ""
                last_contact_str = f"（最后联系：{customer['last_contact_date']}）" if customer.get('last_contact_date') else "（从未联系）"
                output_parts.append(f"• {customer['name']} - {customer['company']}{phone_str} {last_contact_str}")
            output_parts.append("")
        
        if not output_parts:
            return "✅ 今日暂无提醒事项"
        
        return "\n".join(output_parts)
        
    except Exception as e:
        return f"❌ 检查提醒失败：{str(e)}"


def _get_afternoon_reminders_impl(ctx=None) -> str:
    """下午推送：今天联系总结 + 明天生日"""
    try:
        client = get_supabase_client()
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        contacted_today: List[Dict[str, str]] = []
        birthday_tomorrow: List[Dict[str, str]] = []
        
        # 用于去重的集合
        contacted_keys: set = set()
        birthday_tomorrow_keys: set = set()
        
        # 1. 检查今天已联系的客户（last_contact_date = 今天）
        contacted_result = client.table("customers").select("name, company, position, phone").eq("last_contact_date", today.isoformat()).execute()
        contacted_data = cast(List[Dict[str, Any]], contacted_result.data)
        
        for customer in contacted_data:
            name = str(customer.get('name', ''))
            phone = str(customer.get('phone', ''))
            unique_key = f"{name}_{phone}"
            
            if unique_key not in contacted_keys:
                contacted_keys.add(unique_key)
                contacted_today.append({
                    "name": name,
                    "company": str(customer.get('company', '')),
                    "position": str(customer.get('position', '')),
                    "phone": phone
                })
        
        # 2. 检查明天生日的客户
        birthday_result = client.table("customers").select("name, birthday, company, position, phone").not_.is_("birthday", "null").execute()
        birthday_data = cast(List[Dict[str, Any]], birthday_result.data)
        
        for customer in birthday_data:
            if customer.get('birthday'):
                try:
                    birthday_date = datetime.strptime(str(customer['birthday']), "%Y-%m-%d").date()
                    this_year_birthday = birthday_date.replace(year=today.year)
                    
                    if this_year_birthday == tomorrow:
                        name = str(customer.get('name', ''))
                        phone = str(customer.get('phone', ''))
                        unique_key = f"{name}_{phone}"
                        
                        if unique_key not in birthday_tomorrow_keys:
                            birthday_tomorrow_keys.add(unique_key)
                            birthday_tomorrow.append({
                                "name": name,
                                "company": str(customer.get('company', '')),
                                "position": str(customer.get('position', '')),
                                "phone": phone
                            })
                except:
                    pass
        
        # 构建输出
        output_parts: List[str] = []
        
        # 今天联系列表（不带手机号）
        if contacted_today:
            output_parts.append("📊 **今日已联系客户**\n")
            for customer in contacted_today:
                output_parts.append(f"• {customer['name']} - {customer['company']}")
            output_parts.append("\n")
            output_parts.append(f"✅ 今天已联系 **{len(contacted_today)}** 位客户\n")
        
        # 明天生日提醒（带手机号）
        if birthday_tomorrow:
            output_parts.append("🎂 **明天生日**\n")
            for customer in birthday_tomorrow:
                phone_str = f" 📞{customer['phone']}" if customer.get('phone') else ""
                output_parts.append(f"• {customer['name']} - {customer['company']} {customer['position']}{phone_str}")
            output_parts.append("")
        
        if not output_parts:
            return "✅ 今日暂无提醒事项"
        
        return "\n".join(output_parts)
        
    except Exception as e:
        return f"❌ 检查提醒失败：{str(e)}"


def _check_reminders_impl(days_ahead: int = 7, ctx=None) -> str:
    """检查提醒事项的实际逻辑（兼容旧版本）"""
    return _get_morning_reminders_impl(ctx)


def _mark_contacted_impl(name: str, phone: Optional[str] = None, ctx=None) -> str:
    """
    标记客户为已联系
    更新 last_contact_date 为今天，7天内不再提醒
    """
    try:
        client = get_supabase_client()
        today = datetime.now().date().isoformat()
        
        # 查找客户
        query = client.table("customers").select("id, name, company").eq("name", name)
        if phone:
            query = query.eq("phone", phone)
        result = query.execute()
        result_data = cast(List[Dict[str, Any]], result.data)
        
        if not result_data:
            return f"❌ 未找到客户：{name}"
        
        customer = result_data[0]
        customer_id = customer["id"]
        
        # 更新最后联系日期
        client.table("customers").update({
            "last_contact_date": today,
            "updated_at": datetime.now().isoformat()
        }).eq("id", customer_id).execute()
        
        return f"✅ 已标记 {name}（{customer.get('company', '未知公司')}）为已联系，7天内不再提醒"
        
    except Exception as e:
        return f"❌ 标记失败：{str(e)}"


def _delete_customer_impl(name: str, phone: Optional[str] = None, reason: Optional[str] = None, ctx=None) -> str:
    """
    删除客户（不再合作）
    """
    try:
        client = get_supabase_client()
        
        # 查找客户
        query = client.table("customers").select("id, name, company").eq("name", name)
        if phone:
            query = query.eq("phone", phone)
        result = query.execute()
        result_data = cast(List[Dict[str, Any]], result.data)
        
        if not result_data:
            return f"❌ 未找到客户：{name}"
        
        customer = result_data[0]
        customer_id = customer["id"]
        
        # 删除客户
        client.table("customers").delete().eq("id", customer_id).execute()
        
        reason_str = f"，原因：{reason}" if reason else ""
        return f"✅ 已删除客户：{name}（{customer.get('company', '未知公司')}）{reason_str}"
        
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


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
    """检查需要提醒的事项"""
    ctx = runtime.context if runtime else new_context(method="check_reminders")
    return _check_reminders_impl(days_ahead, ctx)


@tool
def mark_contacted(name: str, phone: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """标记客户为已联系，更新最后联系日期为今天，7天内不再提醒"""
    ctx = runtime.context if runtime else new_context(method="mark_contacted")
    return _mark_contacted_impl(name, phone, ctx)


@tool
def delete_customer(name: str, phone: Optional[str] = None, reason: Optional[str] = None, runtime: ToolRuntime = None) -> str:
    """删除客户（不再合作），从数据库中移除该客户"""
    ctx = runtime.context if runtime else new_context(method="delete_customer")
    return _delete_customer_impl(name, phone, reason, ctx)
