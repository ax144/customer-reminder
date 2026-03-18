"""
Supabase 数据库客户端
"""
import os
from supabase import create_client, Client
from typing import Optional, Any

_client = None

def get_supabase_client(ctx: Optional[Any] = None) -> Client:
    global _client
    if _client:
        return _client
    
    # 优先从COZE环境变量获取
    url = os.environ.get('COZE_SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    key = os.environ.get('COZE_SUPABASE_ANON_KEY') or os.environ.get('SUPABASE_ANON_KEY')
    
    if not url or not key:
        raise ValueError("请设置 SUPABASE_URL 和 SUPABASE_ANON_KEY 环境变量")
    
    _client = create_client(url, key)
    return _client
