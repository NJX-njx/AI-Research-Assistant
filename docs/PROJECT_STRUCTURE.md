# 📁 项目目录结构说明

```
demo_code/
│
├── 📂 animation/              # 动画生成模块
│   ├── __init__.py
│   ├── storyboard.py          # 从 KG 生成故事板场景 (规则驱动)
│   ├── manim_generator.py     # 生成 Manim 动画代码 (模板驱动)
│   └── llm_enhanced.py        # 🆕 LLM 增强动画生成 (智能驱动)
│
├── 📂 extraction/             # 文档提取模块
│   ├── __init__.py
│   ├── paddleocr_mcp_client.py  # PaddleOCR-VL MCP 客户端
│   ├── text_extractor.py      # 文本分块处理
│   ├── vision_extractor.py    # Figure 引用提取 + VLM 分析
│   └── image_extractor.py     # PDF 图片提取
│
├── 📂 knowledge_graph/        # 知识图谱模块
│   ├── __init__.py
│   ├── schema.py              # Pydantic 数据模型
│   ├── entity_extractor.py    # LLM 实体/关系抽取
│   └── graph_builder.py       # NetworkX 图谱构建
│
├── 📂 utils/                  # 工具模块
│   ├── __init__.py
│   ├── llm_client.py          # LLM 客户端 (DeepSeek-v3)
│   └── vllm_client.py         # VLM 客户端 (带重试和 Fallback)
│
├── 📂 tests/                  # 测试文件
│   ├── __init__.py
│   ├── run_tests.py           # 统一测试运行脚本
│   ├── test_extraction_complete.py  # 提取模块测试
│   ├── test_kg_module.py      # 知识图谱模块测试
│   ├── test_animation_module.py     # 动画模块测试 (规则驱动)
│   ├── test_llm_animation.py  # 🆕 LLM 增强动画测试
│   ├── generate_demo_animation.py   # Demo 动画生成
│   └── check_animation_status.py    # 动画状态检查
│
├── 📂 test_data/              # 测试数据
│   └── 541_OR_Bench_*.pdf     # 测试 PDF 文件
│
├── 📂 output/                 # 输出目录
│   ├── 📂 extracted_data/     # 提取的数据
│   │   ├── parsed_content.md  # OCR 解析结果
│   │   ├── entities.json      # 抽取的实体
│   │   ├── relations.json     # 抽取的关系
│   │   └── knowledge_graph.json  # 完整知识图谱
│   │
│   ├── 📂 generated_code/     # 生成的代码
│   │   ├── test_animation.py  # 生成的 Manim 代码
│   │   └── e2e_test.py        # 端到端测试代码
│   │
│   └── 📂 media_files/        # 媒体文件
│       ├── images/            # 提取的图片
│       └── media/videos/      # 渲染的动画视频
│
├── 📂 docs/                   # 文档
│   └── extraction_flowchart.md  # 提取模块流程图
│
├── main.py                    # 主程序入口
├── run_demo.py                # Demo 运行脚本
├── model_api.py               # API 配置
├── vllm_api.py                # VLM API 测试
├── requirements.txt           # Python 依赖
└── environment.yml            # Conda 环境配置
```

## 🚀 运行测试

```bash
# 运行所有测试
python tests/run_tests.py

# 运行单个模块测试
python tests/run_tests.py -m extraction   # 提取模块
python tests/run_tests.py -m kg           # 知识图谱模块
python tests/run_tests.py -m animation    # 动画模块
```

## 📊 模块说明

### 1. 提取模块 (extraction/)
- **输入**: PDF 文件
- **输出**: Markdown 文本 + 图片
- **流程**: PDF → PaddleOCR-VL → Markdown → 分块 → Figure 提取

### 2. 知识图谱模块 (knowledge_graph/)
- **输入**: 文本块
- **输出**: 知识图谱 (实体 + 关系)
- **流程**: 文本 → LLM 抽取 → 验证 → 去重 → 构图

### 3. 动画模块 (animation/)
- **输入**: 知识图谱
- **输出**: Manim 动画视频
- **两种模式**:
  - 规则驱动: KG → 规则故事板 → 模板代码 → 渲染 (快速、稳定)
  - LLM 增强: KG → 智能故事板 → 混合代码生成 → 渲染 (灵活、有创意)
