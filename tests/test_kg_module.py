# -*- coding: utf-8 -*-
"""
知识图谱模块完整性测试
测试 entity_extractor 和 graph_builder 的核心功能
"""
import os
import sys
import json

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_kg_module():
    print("=" * 60)
    print("🧪 知识图谱模块测试")
    print("=" * 60)
    
    results = {}
    
    # ========== Test 1: Schema 验证 ==========
    print("\n📋 Test 1: Schema 数据结构")
    try:
        from knowledge_graph.schema import Entity, Relation, Triplet, ContextEdge, Hypothesis
        
        # 测试 Entity
        e1 = Entity(id="e1", type="Method", name="GPT-4", props={"version": "turbo"})
        e2 = Entity(id="e2", type="Dataset", name="MMLU", props={})
        print(f"   ✅ Entity: {e1.name} ({e1.type})")
        
        # 测试 Relation
        r = Relation(source="e1", target="e2", type="evaluated_on")
        print(f"   ✅ Relation: {r.source} --{r.type}--> {r.target}")
        
        # 测试 Triplet
        t = Triplet(head=e1, relation="evaluated_on", tail=e2, context={"setting": "zero-shot"})
        print(f"   ✅ Triplet: {t.head.name} --{t.relation}--> {t.tail.name}")
        
        # 测试 ContextEdge
        ce = ContextEdge(relation=r, context={"score": 0.85}, evidence=["Table 1"])
        print(f"   ✅ ContextEdge: context={ce.context}")
        
        # 测试 Hypothesis
        h = Hypothesis(id="h1", text="Scaling improves performance", links=["e1", "e2"])
        print(f"   ✅ Hypothesis: {h.text}")
        
        results["test1_schema"] = True
    except Exception as ex:
        print(f"   ❌ 异常: {ex}")
        results["test1_schema"] = False
    
    # ========== Test 2: 实体类型/关系类型验证 ==========
    print("\n🔍 Test 2: 类型验证")
    try:
        from knowledge_graph.entity_extractor import validate_entity, validate_relation, VALID_ENTITY_TYPES, VALID_RELATION_TYPES
        
        print(f"   有效实体类型: {VALID_ENTITY_TYPES}")
        print(f"   有效关系类型: {VALID_RELATION_TYPES}")
        
        # 测试有效实体
        valid_ent = validate_entity({"id": "e1", "type": "Method", "name": "BERT"})
        assert valid_ent is not None, "Valid entity should pass"
        print(f"   ✅ 有效实体验证通过")
        
        # 测试无效实体类型
        invalid_ent = validate_entity({"id": "e2", "type": "InvalidType", "name": "Test"})
        assert invalid_ent is None, "Invalid type should fail"
        print(f"   ✅ 无效类型正确拒绝")
        
        # 测试关系验证
        assert validate_relation("uses") == True
        assert validate_relation("invalid_rel") == False
        print(f"   ✅ 关系类型验证正确")
        
        results["test2_validation"] = True
    except Exception as ex:
        print(f"   ❌ 异常: {ex}")
        results["test2_validation"] = False
    
    # ========== Test 3: KnowledgeGraph 构建 ==========
    print("\n🕸️ Test 3: KnowledgeGraph 构建")
    try:
        from knowledge_graph.graph_builder import KnowledgeGraph
        from knowledge_graph.schema import Entity, Relation, Triplet, Hypothesis
        
        kg = KnowledgeGraph()
        
        # 添加实体 (L1)
        e1 = Entity(id="gpt4", type="Method", name="GPT-4", props={})
        e2 = Entity(id="mmlu", type="Dataset", name="MMLU", props={})
        e3 = Entity(id="acc", type="Metric", name="Accuracy", props={"value": "86.4%"})
        
        kg.add_entity(e1)
        kg.add_entity(e2)
        kg.add_entity(e3)
        print(f"   ✅ 添加 3 个实体 (L1)")
        
        # 添加关系 (L1)
        r1 = Relation(source="gpt4", target="mmlu", type="evaluated_on")
        r2 = Relation(source="gpt4", target="acc", type="achieves")
        kg.add_relation(r1)
        kg.add_relation(r2)
        print(f"   ✅ 添加 2 个关系 (L1)")
        
        # 添加带上下文的边 (L2)
        from knowledge_graph.schema import ContextEdge
        ce = ContextEdge(
            relation=Relation(source="gpt4", target="mmlu", type="evaluated_on"),
            context={"setting": "5-shot", "model_size": "unknown"},
            evidence=["Table 2 shows GPT-4 achieves 86.4% on MMLU"],
            confidence=0.95
        )
        kg.add_context_edge(ce)
        print(f"   ✅ 添加上下文边 (L2): context={ce.context}")
        
        # 添加假设节点 (L3)
        h = Hypothesis(
            id="hyp1",
            text="Larger models show emergent abilities on complex tasks",
            links=["gpt4", "mmlu"],
            rationale="Based on scaling law observations"
        )
        kg.add_hypothesis(h)
        print(f"   ✅ 添加假设节点 (L3)")
        
        # 导出为字典
        kg_dict = kg.to_dict()
        print(f"   📊 图统计: {len(kg_dict['nodes'])} 节点, {len(kg_dict['edges'])} 边")
        
        results["test3_graph"] = True
    except Exception as ex:
        print(f"   ❌ 异常: {ex}")
        import traceback
        traceback.print_exc()
        results["test3_graph"] = False
    
    # ========== Test 4: LLM 实体抽取 (真实调用) ==========
    print("\n🤖 Test 4: LLM 实体抽取")
    try:
        if not os.getenv("AISTUDIO_API_KEY"):
            print("   ⚠️ 跳过: 缺少 AISTUDIO_API_KEY")
            results["test4_extraction"] = "skipped"
        else:
            from knowledge_graph.entity_extractor import extract_from_chunk, normalize

            test_text = """
            In this paper, we introduce OR-Bench, a comprehensive benchmark for evaluating 
            over-refusal in large language models. We evaluate GPT-4, Claude-3, and Llama-3 
            on our benchmark. Results show that GPT-4 achieves the best balance between 
            safety and helpfulness with an over-refusal rate of 12.3%.
            """

            print(f"   📝 测试文本: {test_text[:80]}...")

            raw_result = extract_from_chunk(test_text)
            print(f"   📦 原始抽取: {len(raw_result.get('entities', []))} 实体, {len(raw_result.get('triplets', []))} 三元组")

            # 检查是否有 "raw" 字段（表示 JSON 解析失败）
            if "raw" in raw_result:
                print(f"   ⚠️ JSON 解析失败，原始返回: {raw_result['raw'][:200]}...")

            # 归一化
            normalized = normalize(raw_result, deduplicate=False)
            entities = normalized.get("entities", [])
            triplets = normalized.get("triplets", [])

            print(f"   ✅ 归一化后: {len(entities)} 有效实体, {len(triplets)} 有效三元组")

            if entities:
                for e in entities[:3]:
                    print(f"      - {e.type}: {e.name}")

            if triplets:
                for t in triplets[:3]:
                    print(f"      - {t.head.name} --{t.relation}--> {t.tail.name}")

            results["test4_extraction"] = len(entities) > 0
    except Exception as ex:
        print(f"   ❌ 异常: {ex}")
        import traceback
        traceback.print_exc()
        results["test4_extraction"] = False
    
    # ========== Test 5: 完整流程测试 ==========
    print("\n🔄 Test 5: 完整流程 (抽取 → 去重 → 构图)")
    try:
        if not os.getenv("AISTUDIO_API_KEY"):
            print("   ⚠️ 跳过: 缺少 AISTUDIO_API_KEY")
            results["test5_pipeline"] = "skipped"
        else:
            from knowledge_graph.entity_extractor import EntityExtractor
            from knowledge_graph.graph_builder import KnowledgeGraph

            extractor = EntityExtractor()
            kg = KnowledgeGraph()

            # 模拟多个文本块
            chunks = [
                "GPT-4 is a large language model developed by OpenAI. It uses transformer architecture.",
                "The model was evaluated on MMLU dataset and achieved 86.4% accuracy.",
                "Compared to GPT-3.5, GPT-4 outperforms on most reasoning tasks."
            ]

            all_entities = []
            all_triplets = []

            for i, chunk in enumerate(chunks):
                print(f"   处理 chunk {i+1}/{len(chunks)}...")
                result = extractor.extract_all(chunk, deduplicate=False)
                all_entities.extend(result.get("entities", []))
                all_triplets.extend(result.get("triplets", []))

            print(f"   📊 抽取结果: {len(all_entities)} 实体, {len(all_triplets)} 三元组")

            # 添加到知识图谱
            for t in all_triplets:
                kg.add_triplet(t)

            kg_dict = kg.to_dict()
            print(f"   🕸️ 最终图谱: {len(kg_dict['nodes'])} 节点, {len(kg_dict['edges'])} 边")

            results["test5_pipeline"] = len(kg_dict['nodes']) > 0
    except Exception as ex:
        print(f"   ❌ 异常: {ex}")
        import traceback
        traceback.print_exc()
        results["test5_pipeline"] = False
    
    # ========== 结果汇总 ==========
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        if passed == "skipped":
            status = "⚠️ 跳过"
        else:
            status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {name}: {status}")
        if passed is False:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！知识图谱模块工作正常。")
    else:
        print("\n⚠️ 部分测试未通过，请检查日志。")
    
    return results


if __name__ == "__main__":
    test_kg_module()
