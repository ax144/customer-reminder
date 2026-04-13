"""
安徽财经大学校友信息管理工具
从 Supabase 数据库读取数据，支持添加、更新校友
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
import os
import re
from typing import Optional, List, Dict, Any
from storage.database.supabase_client import get_supabase_client


def _get_alumni_data(ctx=None) -> List[Dict[str, Any]]:
    """从 Supabase 数据库加载校友数据"""
    try:
        client = get_supabase_client(ctx=ctx)
        result = client.table("alumni").select("*").order("name").execute()
        return result.data if result.data else []
    except Exception as e:
        # 如果表找不到，尝试其他方式或者给出更友好的错误
        error_msg = str(e)
        if "PGRST205" in error_msg or "Could not find the table" in error_msg:
            raise Exception(f"未找到校友数据表，请确保Supabase中已创建'alumni'表。错误：{error_msg}")
        raise Exception(f"从 Supabase 加载校友数据失败: {error_msg}")


def _search_alumni_impl(
    name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    ctx=None
) -> List[Dict[str, Any]]:
    """查询校友信息"""
    try:
        client = get_supabase_client(ctx=ctx)
        
        query = client.table("alumni").select("*")
        
        if name:
            query = query.ilike("name", f"%{name}%")
        
        if company:
            query = query.ilike("company", f"%{company}%")
        
        if position:
            query = query.ilike("position", f"%{position}%")
        
        result = query.order("name").execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        raise Exception(f"查询校友信息失败: {str(e)}")


def _format_alumni_result(alumni_list: List[Dict[str, Any]]) -> str:
    """格式化校友查询结果"""
    if not alumni_list:
        return "未找到符合条件的校友信息"
    
    result_text = "## 🔍 校友查询结果\n\n"
    
    for i, alumni in enumerate(alumni_list, 1):
        result_text += f"### {i}. {alumni.get('name', '未知')}\n"
        result_text += f"- **公司**: {alumni.get('company', '未知')}\n"
        result_text += f"- **职位**: {alumni.get('position', '未知')}\n"
        if alumni.get('background') and alumni.get('background') != 'nan':
            result_text += f"- **背景**: {alumni.get('background')}\n"
        if alumni.get('stock_code'):
            result_text += f"- **股票代码**: {alumni.get('stock_code')}\n"
        result_text += "\n"
    
    result_text += f"---\n共找到 {len(alumni_list)} 条记录"
    
    return result_text


def _get_all_alumni_impl(ctx=None) -> List[Dict[str, Any]]:
    """获取所有校友信息"""
    try:
        return _get_alumni_data(ctx=ctx)
    except Exception as e:
        raise Exception(f"获取校友信息失败: {str(e)}")


def _get_alumni_by_company_impl(company_keyword: str, ctx=None) -> List[Dict[str, Any]]:
    """根据公司关键词查询校友"""
    try:
        return _search_alumni_impl(company=company_keyword, ctx=ctx)
    except Exception as e:
        raise Exception(f"查询校友信息失败: {str(e)}")


def _get_alumni_by_position_impl(position_keyword: str, ctx=None) -> List[Dict[str, Any]]:
    """根据职位关键词查询校友"""
    try:
        return _search_alumni_impl(position=position_keyword, ctx=ctx)
    except Exception as e:
        raise Exception(f"查询校友信息失败: {str(e)}")


# ============ 查询工具 ============

@tool
def search_alumni(
    name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    查询安徽财经大学校友信息
    
    Args:
        name: 校友姓名（可选，支持模糊搜索）
        company: 公司名称（可选，支持模糊搜索）
        position: 职位（可选，支持模糊搜索）
    
    Returns:
        格式化的校友信息列表
    """
    ctx = runtime.context if runtime else new_context(method="search_alumni")
    
    try:
        alumni_list = _search_alumni_impl(name=name, company=company, position=position, ctx=ctx)
        return _format_alumni_result(alumni_list)
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


@tool
def get_all_alumni(runtime: ToolRuntime = None) -> str:
    """
    获取所有安徽财经大学校友信息
    
    Returns:
        格式化的全部校友信息列表
    """
    ctx = runtime.context if runtime else new_context(method="get_all_alumni")
    
    try:
        alumni_list = _get_all_alumni_impl(ctx=ctx)
        return _format_alumni_result(alumni_list)
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


@tool
def get_alumni_by_company(company_keyword: str, runtime: ToolRuntime = None) -> str:
    """
    根据公司关键词查询安徽财经大学校友
    
    Args:
        company_keyword: 公司名称关键词（如"汽车"、"证券"、"水泥"等）
    
    Returns:
        格式化的校友信息列表
    """
    ctx = runtime.context if runtime else new_context(method="get_alumni_by_company")
    
    try:
        alumni_list = _get_alumni_by_company_impl(company_keyword, ctx=ctx)
        return _format_alumni_result(alumni_list)
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


@tool
def get_alumni_by_position(position_keyword: str, runtime: ToolRuntime = None) -> str:
    """
    根据职位关键词查询安徽财经大学校友
    
    Args:
        position_keyword: 职位关键词（如"董事长"、"财务总监"、"独立董事"等）
    
    Returns:
        格式化的校友信息列表
    """
    ctx = runtime.context if runtime else new_context(method="get_alumni_by_position")
    
    try:
        alumni_list = _get_alumni_by_position_impl(position_keyword, ctx=ctx)
        return _format_alumni_result(alumni_list)
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


# ============ 添加/更新工具 ============

@tool
def add_alumni(
    name: str,
    company: Optional[str] = None,
    position: Optional[str] = None,
    industry: Optional[str] = None,
    region: Optional[str] = None,
    graduation_year: Optional[int] = None,
    background: Optional[str] = None,
    contact_info: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    notes: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    添加校友
    
    Args:
        name: 姓名（必填）
        company: 公司（可选）
        position: 职位（可选）
        industry: 行业（可选）
        region: 地区（可选）
        graduation_year: 毕业年份（可选）
        background: 背景介绍（可选）
        contact_info: 其他联系方式（可选）
        email: 邮箱（可选）
        phone: 电话（可选）
        notes: 备注（可选）
    
    Returns:
        添加结果
    """
    ctx = runtime.context if runtime else new_context(method="add_alumni")
    
    try:
        client = get_supabase_client(ctx=ctx)
        
        data = {
            "name": name
        }
        
        if company:
            data["company"] = company
        if position:
            data["position"] = position
        if industry:
            data["industry"] = industry
        if region:
            data["region"] = region
        if graduation_year:
            data["graduation_year"] = graduation_year
        if background:
            data["background"] = background
        if contact_info:
            data["contact_info"] = contact_info
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if notes:
            data["notes"] = notes
        
        result = client.table("alumni").insert(data).execute()
        
        if result.data:
            return f"✅ 成功添加校友：{name}"
        else:
            return "❌ 添加失败"
            
    except Exception as e:
        return f"❌ 添加失败：{str(e)}"


@tool
def update_alumni(
    name: str,
    company: Optional[str] = None,
    position: Optional[str] = None,
    industry: Optional[str] = None,
    region: Optional[str] = None,
    graduation_year: Optional[int] = None,
    background: Optional[str] = None,
    contact_info: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    notes: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    更新校友
    
    Args:
        name: 姓名（必填，用于查找要更新的记录）
        company: 公司（可选，更新时用）
        position: 职位（可选）
        industry: 行业（可选）
        region: 地区（可选）
        graduation_year: 毕业年份（可选）
        background: 背景介绍（可选）
        contact_info: 其他联系方式（可选）
        email: 邮箱（可选）
        phone: 电话（可选）
        notes: 备注（可选）
    
    Returns:
        更新结果
    """
    ctx = runtime.context if runtime else new_context(method="update_alumni")
    
    try:
        client = get_supabase_client(ctx=ctx)
        
        data = {}
        
        if company:
            data["company"] = company
        if position:
            data["position"] = position
        if industry:
            data["industry"] = industry
        if region:
            data["region"] = region
        if graduation_year:
            data["graduation_year"] = graduation_year
        if background:
            data["background"] = background
        if contact_info:
            data["contact_info"] = contact_info
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if notes:
            data["notes"] = notes
        
        if not data:
            return "❌ 没有提供要更新的字段"
        
        result = client.table("alumni").update(data).eq("name", name).execute()
        
        if result.data:
            return f"✅ 成功更新校友：{name}"
        else:
            return f"❌ 更新失败，未找到姓名为 {name} 的记录"
            
    except Exception as e:
        return f"❌ 更新失败：{str(e)}"


# 导出
__all__ = [
    'search_alumni',
    'get_all_alumni',
    'get_alumni_by_company',
    'get_alumni_by_position',
    'add_alumni',
    'update_alumni',
]
