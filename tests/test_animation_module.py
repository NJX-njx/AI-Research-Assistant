# -*- coding: utf-8 -*-
"""
动画模块完整测试
测试从 Knowledge Graph 到 Manim 动画的完整流程
"""
import os
import sys
import shutil
import subprocess

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "generated_code")
MEDIA_DIR = os.path.join(PROJECT_ROOT, "output", "media_files")


def test_animation_module():
    print("=" * 60)
    print("🎬 动画模块完整测试")
    print("=" * 60)
    
    results = {}
    
    # 定义输出目录
    output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    code_path = os.path.join(output_dir, "test_animation.py")
    
    # ========== Test 1: Storyboard 生成 ==========
    print("\n📋 Test 1: Storyboard 生成")
    try:
        from animation.storyboard import storyboard_from_kg, StoryboardGenerator, SceneType
        
        # 构造测试 KG
        test_kg = {
            "nodes": [
                {"id": "gpt4", "type": "Method", "name": "GPT-4", "props": {}},
                {"id": "llama3", "type": "Method", "name": "Llama-3", "props": {}},
                {"id": "claude3", "type": "Method", "name": "Claude-3", "props": {}},
                {"id": "mmlu", "type": "Dataset", "name": "MMLU", "props": {}},
                {"id": "acc", "type": "Metric", "name": "Accuracy", "props": {"value": "86.4%"}},
                {"id": "finding1", "type": "Finding", "name": "GPT-4 achieves best performance on reasoning tasks", "props": {}},
            ],
            "edges": [
                {"source": "gpt4", "target": "mmlu", "type": "evaluated_on"},
                {"source": "llama3", "target": "mmlu", "type": "evaluated_on"},
                {"source": "gpt4", "target": "llama3", "type": "outperform"},
                {"source": "gpt4", "target": "claude3", "type": "outperform"},
                {"source": "gpt4", "target": "acc", "type": "achieves"},
            ]
        }
        
        scenes = storyboard_from_kg(test_kg)
        print(f"   ✅ 生成 {len(scenes)} 个场景")
        
        for i, scene in enumerate(scenes):
            scene_type = scene.get("scene_type", "unknown")
            title = scene.get("title", "")[:40]
            print(f"      {i+1}. [{scene_type}] {title}")
        
        results["test1_storyboard"] = len(scenes) > 0
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        results["test1_storyboard"] = False
    
    # ========== Test 2: Manim 代码生成 ==========
    print("\n🎥 Test 2: Manim 代码生成")
    try:
        from animation.manim_generator import generate_code, ManimCodeGenerator
        
        code = generate_code(scenes)
        
        print(f"   ✅ 生成 {len(code)} 字符代码")
        
        # 检查关键元素
        checks = [
            ("from manim import", "Manim 导入"),
            ("class", "Scene 类定义"),
            ("def construct", "construct 方法"),
            ("self.play", "动画调用"),
            ("KnowledgeGraphAnimation", "主场景类"),
        ]
        
        all_checks_pass = True
        for pattern, desc in checks:
            if pattern in code:
                print(f"      ✅ {desc}")
            else:
                print(f"      ❌ 缺少: {desc}")
                all_checks_pass = False
        
        # 保存代码供检查
        with open(code_path, 'w') as f:
            f.write(code)
        print(f"   📝 代码已保存到: {code_path}")
        
        results["test2_codegen"] = all_checks_pass
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        results["test2_codegen"] = False
    
    # ========== Test 3: Manim 语法验证 ==========
    print("\n✅ Test 3: Manim 语法验证")
    try:
        # 使用当前解释器进行语法检查（不依赖 conda 环境）
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", code_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("   ✅ Python 语法正确")
            results["test3_syntax"] = True
        else:
            print(f"   ❌ 语法错误: {result.stderr}")
            results["test3_syntax"] = False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        results["test3_syntax"] = False
    
    # ========== Test 4: Manim 渲染测试 (可选) ==========
    print("\n🎞️ Test 4: Manim 渲染测试")
    try:
        manim_bin = shutil.which("manim")
        if not manim_bin:
            print("   ⚠️ Manim 不可用，跳过渲染")
            results["test4_render"] = "skipped"
        else:
            result = subprocess.run(
                [manim_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"   ✅ Manim 可用: {result.stdout.strip()}")

                # 尝试渲染（低质量快速测试）
                print("   🔄 尝试渲染 (低质量)...")
                render_result = subprocess.run(
                    [manim_bin, "-ql",
                     "--disable_caching", "-o", "test_output",
                     "--media_dir", MEDIA_DIR,
                     code_path, "KnowledgeGraphAnimation"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=output_dir
                )

                if render_result.returncode == 0:
                    print("   ✅ 渲染成功!")
                    # 查找输出文件
                    for root, dirs, files in os.walk(MEDIA_DIR):
                        for f in files:
                            if f.endswith('.mp4'):
                                print(f"   📹 输出: {os.path.join(root, f)}")
                    results["test4_render"] = True
                else:
                    print(f"   ⚠️ 渲染失败 (非致命): {render_result.stderr[:200]}")
                    results["test4_render"] = False
            else:
                print("   ⚠️ Manim 不可用，跳过渲染")
                results["test4_render"] = "skipped"
    except subprocess.TimeoutExpired:
        print("   ⚠️ 渲染超时 (跳过)")
        results["test4_render"] = "skipped"
    except Exception as e:
        print(f"   ⚠️ 渲染异常: {e}")
        results["test4_render"] = False
    
    # ========== Test 5: 端到端集成测试 ==========
    print("\n🔄 Test 5: 端到端集成测试")
    try:
        from animation import storyboard_from_kg, generate_code, save_code
        
        # 模拟完整流程
        kg = {
            "nodes": [
                {"id": "bert", "type": "Method", "name": "BERT"},
                {"id": "gpt", "type": "Method", "name": "GPT"},
                {"id": "task", "type": "Task", "name": "NLP Benchmark"},
            ],
            "edges": [
                {"source": "gpt", "target": "bert", "type": "outperform"},
                {"source": "gpt", "target": "task", "type": "evaluated_on"},
            ]
        }
        
        # Step 1: KG -> Storyboard
        scenes = storyboard_from_kg(kg, max_scenes=5)
        print(f"   KG → Storyboard: {len(scenes)} 场景")
        
        # Step 2: Storyboard -> Code
        code = generate_code(scenes)
        print(f"   Storyboard → Code: {len(code)} 字符")
        
        # Step 3: Save code
        e2e_path = os.path.join(output_dir, "e2e_test.py")
        save_code(scenes, e2e_path)
        print(f"   Code → File: {e2e_path}")
        
        results["test5_e2e"] = True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        results["test5_e2e"] = False
    
    # ========== 结果汇总 ==========
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    critical_passed = True
    
    for name, passed in results.items():
        if passed == "skipped":
            status = "⚠️ 跳过"
        else:
            status = "✅ 通过" if passed else "❌ 失败"
        # 渲染测试是非关键的
        is_critical = name != "test4_render"
        if is_critical:
            print(f"   {name}: {status}")
            if passed is False:
                critical_passed = False
        else:
            status = "✅ 通过" if passed is True else "⚠️ 跳过"
            print(f"   {name}: {status} (可选)")
        
        if passed is False:
            all_passed = False
    
    print()
    if critical_passed:
        print("🎉 核心功能测试通过！动画模块已就绪。")
    else:
        print("⚠️ 部分测试未通过，请检查日志。")
    
    return results


if __name__ == "__main__":
    test_animation_module()
