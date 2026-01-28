# 🎬 AI Research Assistant Demo

An AI agent system that converts research papers into a knowledge graph and generates visual animation.

## 📋 Project Overview

This project implements a complete research document processing pipeline:

```
PDF → Text/Image Extraction → Knowledge Graph Construction → Animation Generation
```

### Core Features

| Module | Function | Stack |
|--------|---------:|------:|
| **Extraction** | PDF parsing, OCR, image extraction | PaddleOCR-VL, PyMuPDF |
| **Knowledge Graph** | Entity/relation extraction, graph building | DeepSeek-v3, NetworkX |
| **Animation Generation** | Storyboard planning, Manim code generation | Manim Community, LLM |

---

## 🚀 Quick Start

### 1. Environment setup

```bash
# create conda environment
conda create -n demo_env python=3.10 -y
conda activate demo_env

# install dependencies
pip install -r requirements.txt

# install Manim (conda-forge recommended)
conda install -c conda-forge manim
```

### 2. API configuration

The project uses Baidu AI Studio LLM services by default. To customize:

```python
# Default config in utils/llm_client.py
DEFAULT_BASE_URL = "https://aistudio.baidu.com/llm/lmapi/v3"
DEFAULT_API_KEY = "your_api_key"
DEFAULT_MODEL = "deepseek-v3"
```

### 3. Run tests

```bash
# Run all module tests
python tests/run_tests.py

# Run a single module test
python tests/run_tests.py -m extraction   # document extraction
python tests/run_tests.py -m kg           # knowledge graph
python tests/run_tests.py -m animation    # animation generation
```

---

## 📖 Usage Guide

### Option 1: Full pipeline

```python
from main import run_pipeline

# Run the full pipeline
result = run_pipeline("path/to/paper.pdf")
```

### Option 2: Step-by-step

#### Step 1: Document extraction

```python
from extraction import parse_pdf_with_mcp, chunk_text

# Parse PDF
content = parse_pdf_with_mcp("paper.pdf")

# Split text into chunks
chunks = chunk_text(content, max_chunk_size=3000)
```

#### Step 2: Knowledge graph construction

```python
from knowledge_graph import extract_entities_relations, build_graph

# Extract entities and relations
entities, relations = extract_entities_relations(chunks)

# Build knowledge graph
kg = build_graph(entities, relations)
kg_dict = kg.to_dict()  # export as dict
```

#### Step 3: Animation generation

**Rule-driven mode** (fast, stable):

```python
from animation import storyboard_from_kg, save_code

# Generate storyboard
scenes = storyboard_from_kg(kg_dict, max_scenes=8)

# Save Manim code
save_code(scenes, "output/generated_code/animation.py")
```

**LLM-enhanced mode** (more creative):

```python
from animation import llm_animation_pipeline

# Full pipeline: intelligent storyboard + hybrid code generation
llm_animation_pipeline(kg_dict, "output/generated_code/llm_animation.py", max_scenes=6)
```

#### Step 4: Render video

```bash
# change to code directory
cd output/generated_code

# render animation (quick low-quality preview)
manim -ql --media_dir ../media_files animation.py KnowledgeGraphAnimation

# Render quality options
# -ql : low-quality 480p15 (quick preview)
# -qm : medium-quality 720p30
# -qh : high-quality 1080p60
# -qk : 4K 2160p60
```

---

## 📂 Directory Structure

```
demo_code/
├── animation/              # animation generation module
│   ├── storyboard.py       # rule-driven storyboard
│   ├── manim_generator.py  # templated code generation
│   └── llm_enhanced.py     # LLM-enhanced generation
│
├── extraction/             # document extraction module
│   ├── paddleocr_mcp_client.py  # OCR service client
│   ├── text_extractor.py   # text chunking
│   ├── vision_extractor.py # figure reference extraction
│   └── image_extractor.py  # PDF image extraction
│
├── knowledge_graph/        # knowledge graph module
│   ├── schema.py           # data model definitions
│   ├── entity_extractor.py # entity/relation extraction
│   └── graph_builder.py    # graph construction
│
├── utils/                  # utility modules
│   ├── llm_client.py       # LLM client
│   └── vllm_client.py      # VLM client
│
├── tests/                  # tests
├── test_data/              # test data
├── output/                 # outputs
│   ├── extracted_data/     # extracted JSON/MD
│   ├── generated_code/     # generated code (.py)
│   └── media_files/        # media files (videos, images)
│
├── docs/                   # documentation
├── main.py                 # main entrypoint
└── requirements.txt        # dependencies
```

---

## 🎨 Two animation modes

### 1. Rule-driven mode

```
Pros: Fast, stable, no API calls
Cons: Fixed effects, simple narration

Use case: batch processing, quick previews
```

### 2. LLM-enhanced mode (recommended)

```
Pros: Intelligent storyboards, vivid narration, creative animations
Cons: Requires LLM API calls, may need code tuning

Use case: presentations, demos, high-quality output
```

| Comparison | Rule-driven | LLM-enhanced |
|-----------:|:-----------:|:------------:|
| Title | "Knowledge Graph Visualization" | "A Journey Through LLM Performance" |
| Narration | simple concatenation | vivid, instructional |
| Scene planning | fixed order | intelligent, progressive |
| Effects | basic templates | progress bars, flash, creative effects |
| Speed | fast (no API) | slower (API calls) |
| Stability | high | may need tuning |

---

## 🔧 Configuration

### LLM service configuration

```python
# utils/llm_client.py
DEFAULT_BASE_URL = "https://aistudio.baidu.com/llm/lmapi/v3"
DEFAULT_API_KEY = "your_api_key"
DEFAULT_MODEL = "deepseek-v3"
```

### PaddleOCR-VL MCP service

```python
# extraction/paddleocr_mcp_client.py
MCP_URL = "https://d2kdt3p7v87ac6bf.aistudio-app.com"
```

### Output directories

All outputs are stored under `output/`:
- `extracted_data/` - extracted JSON and Markdown
- `generated_code/` - generated Manim Python code
- `media_files/` - rendered videos and images

---

## 📊 Example outputs

### Knowledge graph JSON

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

### LLM-generated storyboard

```json
{
  "title": "A Journey Through LLM Performance",
  "summary": "GPT-4 outperforms Llama-3 on the MMLU benchmark",
  "scenes": [
    {
      "scene_type": "title",
      "title": "Exploring the Arena of AI Models",
      "narration": "Welcome to the evaluation world of large language models..."
    }
  ]
}
```

---

## 🧪 Test commands

```bash
# Run full test suite
python tests/run_tests.py

# Module tests
python tests/test_extraction_complete.py
python tests/test_kg_module.py
python tests/test_animation_module.py
python tests/test_llm_animation.py

# Generate demo animation
python tests/generate_demo_animation.py

# Render animation
cd output/generated_code
manim -ql --media_dir ../media_files demo_animation.py KnowledgeGraphAnimation
```

---

## 📚 Documentation

- Project structure: `docs/PROJECT_STRUCTURE.md`
- Extraction flowchart: `docs/extraction_flowchart.md`
- Animation pipeline: `docs/animation_pipeline.md`

---

## 🛠️ Dependencies

Main requirements:
- Python 3.10+
- Manim Community v0.19.0+
- OpenAI Python SDK (for LLM calls)
- PyMuPDF (PDF processing)
- NetworkX (graph construction)
- Pydantic (data validation)

See `requirements.txt` for complete list.

---

## 📝 License

MIT License

---

## 👤 Author

Demo project
