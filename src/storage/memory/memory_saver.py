"""
Agent短期记忆模块
使用内存保存对话历史，支持滑动窗口
"""

from langgraph.checkpoint.memory import MemorySaver

# 全局记忆存储实例
_memory_saver = None

def get_memory_saver() -> MemorySaver:
    """
    获取记忆存储实例
    
    Returns:
        MemorySaver实例
    """
    global _memory_saver
    
    if _memory_saver is None:
        _memory_saver = MemorySaver()
    
    return _memory_saver
