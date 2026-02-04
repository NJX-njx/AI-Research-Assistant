#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一测试运行脚本
================
运行所有模块的测试
"""
import os
import sys
import argparse

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def run_extraction_test():
    """运行提取模块测试"""
    print("\n" + "=" * 70)
    print("📄 运行提取模块测试")
    print("=" * 70)
    from tests.test_extraction_complete import test_extraction_pipeline
    return test_extraction_pipeline()


def run_kg_test():
    """运行知识图谱模块测试"""
    print("\n" + "=" * 70)
    print("🕸️ 运行知识图谱模块测试")
    print("=" * 70)
    from tests.test_kg_module import test_kg_module
    return test_kg_module()


def run_animation_test():
    """运行动画模块测试"""
    print("\n" + "=" * 70)
    print("🎬 运行动画模块测试")
    print("=" * 70)
    from tests.test_animation_module import test_animation_module
    return test_animation_module()


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("🧪 AI科研辅助智能体 - 完整测试套件")
    print("=" * 70)
    
    all_results = {}
    
    # 1. 提取模块测试
    try:
        extraction_results = run_extraction_test()
        all_results["extraction"] = extraction_results
    except Exception as e:
        print(f"❌ 提取模块测试异常: {e}")
        all_results["extraction"] = {"error": str(e)}
    
    # 2. 知识图谱模块测试
    try:
        kg_results = run_kg_test()
        all_results["knowledge_graph"] = kg_results
    except Exception as e:
        print(f"❌ 知识图谱模块测试异常: {e}")
        all_results["knowledge_graph"] = {"error": str(e)}
    
    # 3. 动画模块测试
    try:
        animation_results = run_animation_test()
        all_results["animation"] = animation_results
    except Exception as e:
        print(f"❌ 动画模块测试异常: {e}")
        all_results["animation"] = {"error": str(e)}
    
    # 汇总
    print("\n" + "=" * 70)
    print("📊 完整测试结果汇总")
    print("=" * 70)
    
    for module, results in all_results.items():
        if isinstance(results, dict) and "error" not in results:
            passed = sum(1 for v in results.values() if v is True or v == True)
            skipped = sum(1 for v in results.values() if v == "skipped")
            total = len(results) - skipped
            status = "✅" if total == 0 or passed == total else "⚠️"
            suffix = f"{passed}/{total} 通过"
            if skipped:
                suffix += f", {skipped} 跳过"
            print(f"   {status} {module}: {suffix}")
        else:
            print(f"   ❌ {module}: 异常")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(description="运行测试")
    parser.add_argument(
        "--module", "-m",
        choices=["extraction", "kg", "animation", "all"],
        default="all",
        help="要测试的模块 (默认: all)"
    )
    
    args = parser.parse_args()
    
    if args.module == "extraction":
        run_extraction_test()
    elif args.module == "kg":
        run_kg_test()
    elif args.module == "animation":
        run_animation_test()
    else:
        run_all_tests()


if __name__ == "__main__":
    main()
