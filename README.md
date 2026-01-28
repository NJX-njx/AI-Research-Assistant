# 🎬 AI 科研辅助智能体 Demo

一个将科研论文自动转化为知识图谱并生成可视化动画的 AI 智能体系统。

## 📋 项目概述

本项目实现了一个完整的科研文档处理流水线：

```
PDF 论文 → 文本/图像提取 → 知识图谱构建 → 动画视频生成
```

### 核心功能

| 模块 | 功能 | 技术栈 |
|------|------|--------|
| **文档提取** | PDF 解析、OCR、图像提取 | PaddleOCR-VL, PyMuPDF |
| **知识图谱** | 实体/关系抽取、图谱构建 | DeepSeek-v3, NetworkX |
| **动画生成** | 故事板规划、Manim 代码生成 | Manim Community, LLM |

---

## 🚀 快速开始

### 1. 环境配置

```bash
# 创建 conda 环境
conda create -n demo_env python=3.10 -y
conda activate demo_env

# 安装依赖
pip install -r requirements.txt

# 安装 Manim (推荐使用 conda-forge)
conda install -c conda-forge manim
```

### 2. API 配置

项目使用百度 AI Studio 提供的 LLM 服务，默认配置已内置。如需自定义：

```python
# utils/llm_client.py 中的默认配置
DEFAULT_BASE_URL = "https://aistudio.baidu.com/llm/lmapi/v3"
DEFAULT_API_KEY = "your_api_key"  
DEFAULT_MODEL = "deepseek-v3"
```

### 3. 运行测试

```bash
# 运行所有模块测试
python tests/run_tests.py

# 运行单个模块测试
python tests/run_tests.py -m extraction   # 文档提取
python tests/run_tests.py -m kg           # 知识图谱
python tests/run_tests.py -m animation    # 动画生成
```

---

## 📖 使用指南

### 方式一：完整流水线

```python
from main import run_pipeline

# 运行完整流程
result = run_pipeline("path/to/paper.pdf")
```

### 方式二：分步调用

#### Step 1: 文档提取

```python
from extraction import parse_pdf_with_mcp, chunk_text

# 解析 PDF
content = parse_pdf_with_mcp("paper.pdf")

# 文本分块
chunks = chunk_text(content, max_chunk_size=3000)
```

#### Step 2: 知识图谱构建

```python
from knowledge_graph import extract_entities_relations, build_graph

# 提取实体和关系
entities, relations = extract_entities_relations(chunks)

# 构建知识图谱
kg = build_graph(entities, relations)
kg_dict = kg.to_dict()  # 导出为字典
```

#### Step 3: 动画生成

**规则驱动模式** (快速、稳定)：
```python
from animation import storyboard_from_kg, save_code

# 生成故事板
scenes = storyboard_from_kg(kg_dict, max_scenes=8)

# 保存 Manim 代码
save_code(scenes, "output/generated_code/animation.py")
```

**LLM 增强模式** (智能、有创意)：
```python
from animation import llm_animation_pipeline

# 完整流程：智能故事板 + 混合代码生成
llm_animation_pipeline(kg_dict, "output/generated_code/llm_animation.py", max_scenes=6)
```

#### Step 4: 渲染视频

```bash
# 进入代码目录
cd output/generated_code

# 渲染动画 (低质量快速预览)
manim -ql --media_dir ../media_files animation.py KnowledgeGraphAnimation

# 渲染选项
# -ql : 低质量 480p15  (快速预览)
# -qm : 中质量 720p30  (一般用途)
# -qh : 高质量 1080p60 (演示用)
# -qk : 4K 2160p60     (高清输出)
```

---

## 📂 目录结构

```
demo_code/
├── animation/              # 动画生成模块
│   ├── storyboard.py       # 规则驱动故事板
│   ├── manim_generator.py  # 模板代码生成
│   └── llm_enhanced.py     # LLM 增强生成
│
├── extraction/             # 文档提取模块
│   ├── paddleocr_mcp_client.py  # OCR 服务客户端
│   ├── text_extractor.py   # 文本分块
│   ├── vision_extractor.py # Figure 引用提取
│   └── image_extractor.py  # PDF 图片提取
│
├── knowledge_graph/        # 知识图谱模块
│   ├── schema.py           # 数据模型定义
│   ├── entity_extractor.py # 实体关系抽取
│   └── graph_builder.py    # 图谱构建
│
├── utils/                  # 工具模块
│   ├── llm_client.py       # LLM 客户端
│   └── vllm_client.py      # VLM 客户端
│
├── tests/                  # 测试文件
├── test_data/              # 测试数据
├── output/                 # 输出目录
│   ├── extracted_data/     # 提取的数据 (JSON, MD)
│   ├── generated_code/     # 生成的代码 (.py)
│   └── media_files/        # 媒体文件 (视频, 图片)
│
├── docs/                   # 文档
├── main.py                 # 主程序入口
└── requirements.txt        # 依赖列表
```

---

## 🎨 动画生成两种模式

### 1. 规则驱动模式

```
优点：快速、稳定、无 API 调用
缺点：动画效果固定、解说词简单

适用场景：批量处理、快速预览
```

### 2. LLM 增强模式 (推荐)

```
优点：智能故事板、生动解说词、创意动画
缺点：需要 LLM API 调用、可能需要代码微调

适用场景：演示、汇报、高质量输出
```

| 对比项 | 规则驱动 | LLM 增强 |
|--------|----------|----------|
| 标题 | "Knowledge Graph Visualization" | "大语言模型性能对比之旅" |
| 解说词 | 简单拼接 | 生动形象、有教学感 |
| 场景规划 | 固定顺序 | 智能规划、逻辑递进 |
| 动画效果 | 基础模板 | 进度条、Flash、创意动画 |
| 速度 | 快 (无 API) | 较慢 (需 LLM 调用) |
| 稳定性 | 高 | 可能需微调 |

---

## 🔧 配置说明

### LLM 服务配置

```python
# utils/llm_client.py
DEFAULT_BASE_URL = "https://aistudio.baidu.com/llm/lmapi/v3"
DEFAULT_API_KEY = "your_api_key"
DEFAULT_MODEL = "deepseek-v3"
```

### PaddleOCR-VL MCP 服务

```python
# extraction/paddleocr_mcp_client.py
MCP_URL = "https://d2kdt3p7v87ac6bf.aistudio-app.com"
```

### 输出目录配置

所有输出统一存放在 `output/` 目录下：
- `extracted_data/` - 提取的 JSON、Markdown 数据
- `generated_code/` - 生成的 Manim Python 代码
- `media_files/` - 渲染的视频和图片文件

---

## 📊 示例输出

### 知识图谱 JSON

```json
{
  "nodes": [
    {"id": "gpt4", "type": "Method", "name": "GPT-4"},
    {"id": "mmlu", "type": "Dataset", "name": "MMLU"}
  ],
  "edges": [
    {"source": "gpt4", "target": "mmlu", "type": "evaluated_on"}
  ]
}
```

### LLM 生成的故事板

```json
{
  "title": "大语言模型性能对比之旅",
  "summary": "GPT-4在MMLU基准测试上优于Llama-3",
  "scenes": [
    {
      "scene_type": "title",
      "title": "探索AI模型的竞技场",
      "narration": "欢迎来到大语言模型的能力评测世界..."
    }
  ]
}
```

---

## 🧪 测试命令汇总

```bash
# 完整测试
python tests/run_tests.py

# 单模块测试
python tests/test_extraction_complete.py
python tests/test_kg_module.py
python tests/test_animation_module.py
python tests/test_llm_animation.py

# 生成 Demo 动画
python tests/generate_demo_animation.py

# 渲染动画
cd output/generated_code
manim -ql --media_dir ../media_files demo_animation.py KnowledgeGraphAnimation
```

---

## 📚 文档

- [项目结构说明](docs/PROJECT_STRUCTURE.md)
- [文档提取流程图](docs/extraction_flowchart.md)
- [动画生成流程图](docs/animation_pipeline.md)

---

## 🛠️ 依赖

主要依赖：
- Python 3.10+
- Manim Community v0.19.0+
- OpenAI Python SDK (用于 LLM 调用)
- PyMuPDF (PDF 处理)
- NetworkX (图谱构建)
- Pydantic (数据验证)

完整依赖见 `requirements.txt`

---

## 📝 License

MIT License

---

## 👤 作者

Demo 项目
