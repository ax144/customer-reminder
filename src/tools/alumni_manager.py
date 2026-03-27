"""
安徽财经大学校友信息管理工具
直接从Excel文件读取数据，不依赖数据库
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
import os
import pandas as pd
import re
from typing import Optional, List, Dict, Any


# 校友数据缓存
_alumni_data_cache = None
_cache_loaded = False


def _get_alumni_data() -> List[Dict[str, Any]]:
    """从Excel文件加载校友数据"""
    global _alumni_data_cache, _cache_loaded
    
    if _cache_loaded and _alumni_data_cache is not None:
        return _alumni_data_cache
    
    # Excel文件路径
    excel_path = "assets/安财担任上市公司高管的校友录.xlsx"
    
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"找不到校友数据文件: {excel_path}")
    
    # 读取Excel
    df = pd.read_excel(excel_path)
    
    alumni_list = []
    for _, row in df.iterrows():
        alumni = {
            'id': len(alumni_list) + 1,
            'name': str(row.get('校友姓名', '')),
            'background': str(row.get('相关专业/背景', '')),
            'company': str(row.get('上市公司（股票代码）', '')),
            'stock_code': '',
            'position': str(row.get('担任职务', ''))
        }
        
        # 提取股票代码
        company_str = alumni['company']
        if '（' in company_str and '）' in company_str:
            match = re.search(r'（([^）]+)）', company_str)
            if match:
                alumni['stock_code'] = match.group(1)
        
        alumni_list.append(alumni)
    
    _alumni_data_cache = alumni_list
    _cache_loaded = True
    
    return alumni_list


def _search_alumni_impl(
    name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    ctx=None
) -> List[Dict[str, Any]]:
    """查询校友信息"""
    try:
        alumni_list = _get_alumni_data()
        
        result = alumni_list
        
        if name:
            name_lower = name.lower()
            result = [a for a in result if name_lower in a['name'].lower()]
        
        if company:
            company_lower = company.lower()
            result = [a for a in result if company_lower in a['company'].lower()]
        
        if position:
            position_lower = position.lower()
            result = [a for a in result if position_lower in a['position'].lower()]
        
        # 按姓名排序
        result.sort(key=lambda x: x['name'])
        
        return result
        
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
        alumni_list = _get_alumni_data()
        alumni_list.sort(key=lambda x: x['name'])
        return alumni_list
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


# ============ Agent 工具函数 ============

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


# 导出
__all__ = [
    '_get_alumni_data',
    '_search_alumni_impl',
    '_get_all_alumni_impl',
    '_get_alumni_by_company_impl',
    '_get_alumni_by_position_impl',
    'search_alumni',
    'get_all_alumni',
    'get_alumni_by_company',
    'get_alumni_by_position',
]
