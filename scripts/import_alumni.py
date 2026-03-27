#!/usr/bin/env python3
"""
导入安财校友Excel数据到数据库
"""

import os
import sys

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from tools.alumni_manager import _create_alumni_table, _import_alumni_from_excel


def main():
    excel_path = "assets/安财担任上市公司高管的校友录.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"❌ 找不到文件: {excel_path}")
        return
    
    print("📚 正在创建校友表...")
    result1 = _create_alumni_table()
    print(result1)
    
    print("\n📥 正在导入Excel数据...")
    result2 = _import_alumni_from_excel(excel_path)
    print(result2)
    
    print("\n✅ 导入完成！")


if __name__ == "__main__":
    main()
