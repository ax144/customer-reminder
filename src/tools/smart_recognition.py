"""
智能识别模块
自动识别用户上传的内容类型，并路由到对应的管理工具
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from typing import Optional, Dict, Any, List
import re


def _detect_content_type(content: str, filename: str = None) -> Dict[str, Any]:
    """
    智能识别内容类型
    
    Args:
        content: 文本内容
        filename: 文件名（可选）
    
    Returns:
        {
            'type': 'document' | 'schedule' | 'customer' | 'unknown',
            'category': 具体分类,
            'confidence': 置信度,
            'suggested_action': 建议操作
        }
    """
    content_lower = content.lower()
    result = {
        'type': 'unknown',
        'category': None,
        'confidence': 0,
        'suggested_action': None
    }
    
    # 文档类关键词
    doc_keywords = ['报告', '分析', '方案', '需求', '文档', '清单', '名单', '总结', '规划', '策略', '调研']
    doc_patterns = ['分析报告', '需求文档', '方案文档', '调研报告', '清单', '名单']
    
    # 工作安排关键词
    schedule_keywords = ['安排', '任务', '计划', '待办', '截止', '负责人', '跟进', '推进']
    schedule_patterns = ['工作安排', '任务分配', '待办事项', '工作计划']
    
    # 客户信息关键词
    customer_keywords = ['客户', '联系', '公司', '职位', '推荐人', '项目']
    customer_patterns = ['保存客户', '新增客户', '客户信息']
    
    # 计算各类型得分
    doc_score = sum(1 for kw in doc_keywords if kw in content_lower)
    doc_score += sum(2 for p in doc_patterns if p in content_lower)
    
    schedule_score = sum(1 for kw in schedule_keywords if kw in content_lower)
    schedule_score += sum(2 for p in schedule_patterns if p in content_lower)
    
    customer_score = sum(1 for kw in customer_keywords if kw in content_lower)
    customer_score += sum(2 for p in customer_patterns if p in content_lower)
    
    # 文件名加分
    if filename:
        filename_lower = filename.lower()
        if any(ext in filename_lower for ext in ['.docx', '.doc', '.pdf', '.xlsx', '.pptx']):
            doc_score += 3
        if '报告' in filename or '分析' in filename or '方案' in filename:
            doc_score += 5
        if '安排' in filename or '计划' in filename:
            schedule_score += 5
    
    # 判断类型
    max_score = max(doc_score, schedule_score, customer_score)
    
    if max_score == 0:
        result['type'] = 'unknown'
        result['suggested_action'] = '请明确内容类型：文档/工作安排/客户信息'
    elif doc_score == max_score:
        result['type'] = 'document'
        result['category'] = _detect_document_category(content_lower)
        result['confidence'] = min(doc_score / 10, 1.0)
        result['suggested_action'] = '保存到文档库'
    elif schedule_score == max_score:
        result['type'] = 'schedule'
        result['category'] = '工作安排'
        result['confidence'] = min(schedule_score / 10, 1.0)
        result['suggested_action'] = '保存到工作安排'
    elif customer_score == max_score:
        result['type'] = 'customer'
        result['category'] = '客户信息'
        result['confidence'] = min(customer_score / 10, 1.0)
        result['suggested_action'] = '保存到客户库'
    
    return result


def _detect_document_category(content: str) -> str:
    """识别文档具体分类"""
    categories = {
        '分析报告': ['分析报告', '需求分析', '市场分析', '行业分析', '调研报告'],
        '需求文档': ['需求文档', '需求说明', '需求清单', '需求梳理'],
        '方案文档': ['方案', '解决方案', '实施方案', '推广方案'],
        '客户清单': ['客户清单', '客户名单', '企业名单', '联系人名单'],
        '会议纪要': ['会议纪要', '会议记录', '会议总结'],
        '合同文档': ['合同', '协议', '合作框架'],
    }
    
    for category, keywords in categories.items():
        for kw in keywords:
            if kw in content:
                return category
    
    return '其他文档'


def _extract_document_info(content: str, filename: str = None) -> Dict[str, Any]:
    """从内容中提取文档信息"""
    lines = content.split('\n')
    
    # 提取标题（通常在第一行或包含"报告"等关键词的行）
    title = None
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) < 100:
            if any(kw in line for kw in ['报告', '方案', '清单', '名单', '分析']):
                title = line
                break
    
    if not title and lines:
        title = lines[0].strip()[:100] if lines[0].strip() else '未命名文档'
    
    # 提取关键词
    keywords = []
    keyword_patterns = ['PLM', '数字化转型', '汽车零部件', '半导体', '新能源', 
                       '助力科技', '合肥', '需求', '营销', '推广', '客户']
    for kw in keyword_patterns:
        if kw in content:
            keywords.append(kw)
    
    # 提取项目名
    project = None
    project_match = re.search(r'([^\s]+项目)', content)
    if project_match:
        project = project_match.group(1)
    
    return {
        'title': title,
        'category': _detect_document_category(content.lower()),
        'content': content[:500] + '...' if len(content) > 500 else content,
        'keywords': keywords[:10],
        'project': project,
        'file_path': filename
    }


def _extract_schedule_info(content: str) -> Dict[str, Any]:
    """从内容中提取工作安排信息"""
    lines = content.split('\n')
    
    # 提取标题
    title = None
    for line in lines[:3]:
        line = line.strip()
        if line and len(line) < 50:
            title = line
            break
    if not title:
        title = '工作安排'
    
    # 提取负责人
    assignee = None
    assignee_match = re.search(r'(负责人|对接人|执行人)[：:]\s*([^\s，,。\n]+)', content)
    if assignee_match:
        assignee = assignee_match.group(2)
    
    # 提取截止日期
    due_date = None
    date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})', content)
    if date_match:
        due_date = date_match.group(1).replace('年', '-').replace('月', '-').replace('/', '-')
    
    # 判断优先级
    priority = 'medium'
    if any(kw in content for kw in ['紧急', '重要', '优先', '尽快', '立即']):
        priority = 'high'
    elif any(kw in content for kw in ['稍后', '不急', '低优先']):
        priority = 'low'
    
    return {
        'title': title,
        'assignee': assignee,
        'content': content[:300],
        'priority': priority,
        'due_date': due_date
    }


@tool
def smart_save(
    content: str,
    filename: str = None,
    force_type: str = None,
    runtime: ToolRuntime = None
) -> str:
    """
    智能保存内容到对应的库（自动识别类型）。
    
    Args:
        content: 文本内容
        filename: 文件名（可选，用于辅助识别）
        force_type: 强制指定类型（document/schedule/customer，可选）
    
    Returns:
        保存结果
    """
    ctx = runtime.context if runtime else new_context(method="smart_save")
    
    # 识别内容类型
    if force_type:
        detected = {'type': force_type, 'category': force_type, 'confidence': 1.0}
    else:
        detected = _detect_content_type(content, filename)
    
    content_type = detected['type']
    
    if content_type == 'document':
        from tools.document_manager import _save_document_impl
        info = _extract_document_info(content, filename)
        result = _save_document_impl(
            title=info['title'],
            category=info['category'],
            content=info['content'],
            keywords=info['keywords'],
            project=info['project'],
            file_path=info['file_path']
        )
        return f"📄 已识别为【{info['category']}】\n{result}"
    
    elif content_type == 'schedule':
        from tools.schedule_manager import _save_schedule_impl
        info = _extract_schedule_info(content)
        result = _save_schedule_impl(
            title=info['title'],
            assignee=info['assignee'],
            content=info['content'],
            priority=info['priority'],
            due_date=info['due_date']
        )
        return f"📅 已识别为【工作安排】\n{result}"
    
    elif content_type == 'customer':
        return "👤 识别为客户信息，请使用 save_customer 工具保存"
    
    else:
        return f"""❓ 无法自动识别内容类型

建议手动指定类型：
- 保存文档：使用 save_document 工具
- 保存工作安排：使用 save_schedule 工具  
- 保存客户：使用 save_customer 工具

或重新提供更明确的内容"""


__all__ = [
    '_detect_content_type',
    '_detect_document_category',
    '_extract_document_info',
    '_extract_schedule_info',
    'smart_save',
]
