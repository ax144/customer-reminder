"""
批量导入工具模块
- import_customers_from_excel: 从Excel批量导入客户信息
- get_import_template: 获取导入模板
"""

from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from src.storage.database.supabase_client import get_supabase_client
from datetime import datetime
from typing import Optional
import io

@tool
def get_import_template(runtime: ToolRuntime = None) -> str:
    """
    获取客户信息导入模板
    
    Returns:
        模板说明和字段格式
    """
    template = """📋 客户信息导入模板

请按以下格式准备Excel/CSV文件（第一行为表头）：

| 字段名 | 说明 | 是否必填 | 格式示例 |
|--------|------|----------|----------|
| name | 客户姓名 | ✅ 必填 | 张三 |
| company | 公司名称 | 选填 | 科大讯飞 |
| position | 职位 | 选填 | 技术总监 |
| phone | 电话 | 选填 | 13800138000 |
| email | 邮箱 | 选填 | zhangsan@example.com |
| wechat | 微信号 | 选填 | zhangsan_wx |
| birthday | 生日 | 选填 | 1985-06-15 |
| source | 认识渠道 | 选填 | 行业峰会 |
| notes | 备注 | 选填 | 对AI产品感兴趣 |
| last_contact_date | 最后联系日期 | 选填 | 2024-01-15 |
| next_follow_up_date | 下次跟进日期 | 选填 | 2024-02-01 |
| relationship_strength | 关系强度 | 选填 | 强/中/弱 |

💡 提示：
1. 日期格式统一使用 YYYY-MM-DD
2. 关系强度只能填写：强、中、弱
3. 文件支持 .xlsx, .xls, .csv 格式
4. 重复姓名的客户会被更新而非新增

准备好文件后，请上传文件，我会帮您导入。
"""
    return template

@tool
def import_customers_from_excel(
    file_url: str,
    runtime: ToolRuntime = None
) -> str:
    """
    从Excel文件批量导入客户信息
    
    Args:
        file_url: Excel文件的URL地址（支持xlsx, xls, csv格式）
    
    Returns:
        导入结果统计
    """
    ctx = runtime.context if runtime else new_context(method="import_customers_from_excel")
    
    try:
        import pandas as pd
        import requests
        
        # 下载文件
        response = requests.get(file_url, timeout=30)
        if response.status_code != 200:
            return f"❌ 文件下载失败：HTTP {response.status_code}"
        
        # 读取Excel/CSV
        if file_url.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(response.content))
        else:
            df = pd.read_excel(io.BytesIO(response.content))
        
        # 验证必填字段
        if 'name' not in df.columns:
            return "❌ 文件缺少必填字段：name（客户姓名）"
        
        # 连接数据库
        client = get_supabase_client(ctx)
        
        # 统计导入结果
        success_count = 0
        update_count = 0
        error_count = 0
        error_details = []
        
        # 逐行导入
        for index, row in df.iterrows():
            try:
                # 跳过空行
                if pd.isna(row.get('name')) or str(row.get('name')).strip() == '':
                    continue
                
                # 构建客户数据
                customer_data = {
                    "name": str(row['name']).strip(),
                    "company": str(row.get('company', '')).strip() if pd.notna(row.get('company')) else None,
                    "position": str(row.get('position', '')).strip() if pd.notna(row.get('position')) else None,
                    "phone": str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else None,
                    "email": str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                    "wechat": str(row.get('wechat', '')).strip() if pd.notna(row.get('wechat')) else None,
                    "birthday": str(row.get('birthday', '')).strip() if pd.notna(row.get('birthday')) else None,
                    "source": str(row.get('source', '')).strip() if pd.notna(row.get('source')) else None,
                    "notes": str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else None,
                    "last_contact_date": str(row.get('last_contact_date', '')).strip() if pd.notna(row.get('last_contact_date')) else None,
                    "next_follow_up_date": str(row.get('next_follow_up_date', '')).strip() if pd.notna(row.get('next_follow_up_date')) else None,
                    "relationship_strength": str(row.get('relationship_strength', '')).strip() if pd.notna(row.get('relationship_strength')) else None,
                    "updated_at": datetime.now().isoformat()
                }
                
                # 移除None值
                customer_data = {k: v for k, v in customer_data.items() if v}
                
                # 检查是否已存在
                existing = client.table("customers").select("id").eq("name", customer_data['name']).execute()
                
                if existing.data:
                    # 更新
                    customer_id = existing.data[0]["id"]
                    client.table("customers").update(customer_data).eq("id", customer_id).execute()
                    update_count += 1
                else:
                    # 新增
                    customer_data["created_at"] = datetime.now().isoformat()
                    client.table("customers").insert(customer_data).execute()
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                error_details.append(f"第{index+2}行：{str(e)}")
        
        # 生成结果报告
        result = f"""📊 导入完成！

✅ 新增客户：{success_count} 条
📝 更新客户：{update_count} 条
❌ 失败：{error_count} 条
"""
        
        if error_details:
            result += "\n⚠️ 失败详情：\n"
            for detail in error_details[:5]:  # 只显示前5条错误
                result += f"  - {detail}\n"
            if len(error_details) > 5:
                result += f"  ... 还有 {len(error_details)-5} 条错误\n"
        
        return result
        
    except ImportError:
        return "❌ 缺少依赖：pandas, openpyxl。请联系管理员安装。"
    except Exception as e:
        return f"❌ 导入失败：{str(e)}"
