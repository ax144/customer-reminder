"""
Supabase数据库客户端
提供统一的数据库连接管理
"""

import os
from typing import Optional
from supabase import create_client, Client

# 全局客户端实例
_supabase_client: Optional[Client] = None

def get_supabase_client(ctx=None) -> Client:
    """
    获取Supabase客户端实例
    
    Args:
        ctx: 运行时上下文（用于获取环境变量）
    
    Returns:
        Supabase客户端实例
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    # 从环境变量获取配置（支持COZE_前缀和不带前缀两种格式）
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("COZE_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("COZE_SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "缺少Supabase配置！请设置环境变量：\n"
            "- SUPABASE_URL 或 COZE_SUPABASE_URL\n"
            "- SUPABASE_ANON_KEY 或 COZE_SUPABASE_ANON_KEY"
        )
    
    # 创建客户端
    _supabase_client = create_client(supabase_url, supabase_key)
    
    return _supabase_client


def init_database():
    """
    初始化数据库表结构
    创建customers表（如果不存在）
    """
    client = get_supabase_client()
    
    # 注意：Supabase的表结构需要通过控制台创建
    # 这里只是检查表是否存在的示例代码
    
    try:
        # 尝试查询customers表
        client.table("customers").select("id").limit(1).execute()
        print("✅ 数据库表结构正常")
        return True
    except Exception as e:
        print(f"❌ 数据库表不存在或配置错误：{e}")
        print("""
        请在Supabase控制台执行以下SQL创建表：
        
        CREATE TABLE customers (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name TEXT NOT NULL,
            company TEXT,
            position TEXT,
            phone TEXT,
            email TEXT,
            wechat TEXT,
            birthday DATE,
            source TEXT,
            notes TEXT,
            last_contact_date DATE,
            next_follow_up_date DATE,
            relationship_strength TEXT CHECK (relationship_strength IN ('强', '中', '弱')),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX idx_customers_name ON customers(name);
        CREATE INDEX idx_customers_company ON customers(company);
        CREATE INDEX idx_customers_birthday ON customers(birthday);
        CREATE INDEX idx_customers_next_follow_up ON customers(next_follow_up_date);
        """)
        return False


if __name__ == "__main__":
    # 测试数据库连接
    print("测试Supabase连接...")
    try:
        client = get_supabase_client()
        print(f"✅ Supabase连接成功")
        print(f"   URL: {os.getenv('SUPABASE_URL') or os.getenv('COZE_SUPABASE_URL')}")
        init_database()
    except Exception as e:
        print(f"❌ 连接失败：{e}")
