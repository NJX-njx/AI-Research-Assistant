# -*- coding: utf-8 -*-
"""
动画模块状态检查
"""
import os
import sys

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def check_animation_module():
    print("=" * 60)
    print("🎬 动画模块状态检查")
    print("=" * 60)
    
    status = {
        "storyboard": {"implemented": False, "working": False, "notes": []},
        "manim_generator": {"implemented": False, "working": False, "notes": []},
        "manim_installed": False,
        "end_to_end": False
    }
    
    # 1. 检查 storyboard.py
    print("\n📋 1. Storyboard 模块")
    try:
        from animation.storyboard import storyboard_from_kg
        status["storyboard"]["implemented"] = True
        
        # 测试功能
        test_kg = {
            "nodes": [
                {"id": "gpt4", "type": "Method", "name": "GPT-4"},
                {"id": "llama", "type": "Method", "name": "Llama-3"},
            ],
            "edges": [
                {"source": "gpt4", "target": "llama", "type": "outperform", "context": {"metric": "accuracy"}},
                {"source": "gpt4", "target": "mmlu", "type": "evaluated_on"},
            ]
        }
        
        scenes = storyboard_from_kg(test_kg)
        if scenes:
            status["storyboard"]["working"] = True
            print(f"   ✅ 已实现，生成 {len(scenes)} 个场景")
            for s in scenes:
                print(f"      - {s['title']}: {s['source']} → {s['target']}")
        else:
            print("   ⚠️ 已实现但返回空场景")
            status["storyboard"]["notes"].append("只处理 outperform/contradicts/supports 关系")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 2. 检查 manim_generator.py
    print("\n🎥 2. Manim Generator 模块")
    try:
        from animation.manim_generator import generate_code, HEADER
        status["manim_generator"]["implemented"] = True
        
        code = generate_code([{"title": "test"}])
        if code and "class RelationScene" in code:
            print("   ✅ 已实现，生成代码模板")
            print("   📝 生成的代码预览:")
            for line in code.strip().split('\n')[:10]:
                print(f"      {line}")
            status["manim_generator"]["working"] = True
        
        # 检查局限性
        status["manim_generator"]["notes"] = [
            "⚠️ 当前只返回固定模板代码",
            "⚠️ 未根据场景动态生成代码",
            "⚠️ 不支持多场景组合"
        ]
        for note in status["manim_generator"]["notes"]:
            print(f"   {note}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 3. 检查 Manim 安装
    print("\n📦 3. Manim 依赖")
    try:
        import manim
        status["manim_installed"] = True
        print(f"   ✅ Manim 已安装: {manim.__version__}")
    except ImportError:
        print("   ❌ Manim 未安装")
        print("   💡 安装命令: pip install manim")
    
    # 4. 端到端测试
    print("\n🔄 4. 端到端流程测试")
    if status["storyboard"]["working"] and status["manim_generator"]["working"]:
        try:
            from animation import storyboard_from_kg, generate_code
            
            # 模拟从 KG 到代码的完整流程
            kg = {
                "nodes": [
                    {"id": "bert", "type": "Method", "name": "BERT"},
                    {"id": "gpt", "type": "Method", "name": "GPT"},
                ],
                "edges": [
                    {"source": "gpt", "target": "bert", "type": "outperform"},
                ]
            }
            scenes = storyboard_from_kg(kg)
            code = generate_code(scenes)
            
            print(f"   📊 KG → Storyboard: {len(scenes)} 场景")
            print(f"   📝 Storyboard → Code: {len(code)} 字符")
            
            if status["manim_installed"]:
                print("   ✅ 端到端流程可用 (可渲染)")
                status["end_to_end"] = True
            else:
                print("   ⚠️ 端到端流程部分可用 (无法渲染)")
        except Exception as e:
            print(f"   ❌ 端到端测试失败: {e}")
    else:
        print("   ⏭️ 跳过 (前置模块未就绪)")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 动画模块状态总结")
    print("=" * 60)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│                    动画生成流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   KnowledgeGraph                                            │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────────────┐                                       │
│   │  storyboard.py  │ ← 已实现 (基础版)                      │
│   │  从 KG 生成场景   │   只处理 3 种关系类型                  │
│   └────────┬────────┘                                       │
│            │                                                │
│            ▼                                                │
│   ┌─────────────────┐                                       │
│   │ manim_generator │ ← 已实现 (占位版)                      │
│   │   生成 Manim 代码 │   返回固定模板，未动态生成              │
│   └────────┬────────┘                                       │
│            │                                                │
│            ▼                                                │
│   ┌─────────────────┐                                       │
│   │     Manim       │ ← ❌ 未安装                            │
│   │   渲染为视频     │                                       │
│   └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
""")
    
    print("🔴 需要完成的工作:")
    print("   1. 安装 Manim: pip install manim")
    print("   2. 增强 generate_code() 根据场景动态生成代码")
    print("   3. 支持更多实体/关系类型的可视化")
    print("   4. 添加渲染功能 (调用 manim render)")
    print("   5. 支持自定义样式和动画效果")
    
    return status


if __name__ == "__main__":
    check_animation_module()
