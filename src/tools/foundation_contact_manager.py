"""
基金会人脉管理工具 - 支持添加、更新基金会人脉数据
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from typing import Optional, List
from storage.database.supabase_client import get_supabase_client


@tool
def add_foundation_contact(
    name: str,
    foundation_name: str,
    position: Optional[str] = None,
    background: Optional[str] = None,
    connected_universities: Optional[List[str]] = None,
    connected_companies: Optional[List[str]] = None,
    focus_areas: Optional[List[str]] = None,
    notes: Optional[str] = None,
    contact_info: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    添加基金会人脉
    
    Args:
        name: 姓名（必填）
        foundation_name: 基金会/机构名称（必填）
        position: 职位（可选）
        background: 背景介绍（可选）
        connected_universities: 可对接高校列表（可选）
        connected_companies: 可对接企业列表（可选）
        focus_areas: 关注领域列表（可选）
        notes: 备注（可选）
        contact_info: 其他联系方式（可选）
        email: 邮箱（可选）
        phone: 电话（可选）
    
    Returns:
        添加结果
    """
    ctx = runtime.context if runtime else new_context(method="add_foundation_contact")
    
    try:
        client = get_supabase_client(ctx=ctx)
        
        data = {
            "name": name,
            "foundation_name": foundation_name
        }
        
        if position:
            data["position"] = position
        if background:
            data["background"] = background
        if connected_universities:
            data["connected_universities"] = connected_universities
        if connected_companies:
            data["connected_companies"] = connected_companies
        if focus_areas:
            data["focus_areas"] = focus_areas
        if notes:
            data["notes"] = notes
        if contact_info:
            data["contact_info"] = contact_info
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        
        result = client.table("foundation_contacts").insert(data).execute()
        
        if result.data:
            return f"✅ 成功添加基金会人脉：{name}（{foundation_name}）"
        else:
            return "❌ 添加失败"
            
    except Exception as e:
        return f"❌ 添加失败：{str(e)}"


@tool
def update_foundation_contact(
    name: str,
    foundation_name: Optional[str] = None,
    position: Optional[str] = None,
    background: Optional[str] = None,
    connected_universities: Optional[List[str]] = None,
    connected_companies: Optional[List[str]] = None,
    focus_areas: Optional[List[str]] = None,
    notes: Optional[str] = None,
    contact_info: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    更新基金会人脉
    
    Args:
        name: 姓名（必填，用于查找要更新的记录）
        foundation_name: 基金会/机构名称（可选，更新时用）
        position: 职位（可选）
        background: 背景介绍（可选）
        connected_universities: 可对接高校列表（可选）
        connected_companies: 可对接企业列表（可选）
        focus_areas: 关注领域列表（可选）
        notes: 备注（可选）
        contact_info: 其他联系方式（可选）
        email: 邮箱（可选）
        phone: 电话（可选）
    
    Returns:
        更新结果
    """
    ctx = runtime.context if runtime else new_context(method="update_foundation_contact")
    
    try:
        client = get_supabase_client(ctx=ctx)
        
        data = {}
        
        if foundation_name:
            data["foundation_name"] = foundation_name
        if position:
            data["position"] = position
        if background:
            data["background"] = background
        if connected_universities:
            data["connected_universities"] = connected_universities
        if connected_companies:
            data["connected_companies"] = connected_companies
        if focus_areas:
            data["focus_areas"] = focus_areas
        if notes:
            data["notes"] = notes
        if contact_info:
            data["contact_info"] = contact_info
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        
        if not data:
            return "❌ 没有提供要更新的字段"
        
        result = client.table("foundation_contacts").update(data).eq("name", name).execute()
        
        if result.data:
            return f"✅ 成功更新基金会人脉：{name}"
        else:
            return f"❌ 更新失败，未找到姓名为 {name} 的记录"
            
    except Exception as e:
        return f"❌ 更新失败：{str(e)}"


# 导出
__all__ = [
    'add_foundation_contact',
    'update_foundation_contact',
]
