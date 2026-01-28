# 提取模块工作流程图

## 整体架构

```mermaid
flowchart TB
    subgraph Input["📄 输入"]
        PDF["PDF 文件"]
    end

    subgraph Step1["Step 1: 文档解析"]
        OCR["PaddleOCR-VL<br/>(MCP 服务)"]
        MD["Markdown 文本<br/>+ 图片标签"]
    end

    subgraph Step2["Step 2: 文本处理"]
        CHUNK["chunk_text()<br/>文本分块"]
        CHUNKS["68 个文本块"]
    end

    subgraph Step3["Step 3: Figure 引用提取"]
        EXTRACT_REF["extract_figure_references()"]
        EXTRACT_IMG["extract_image_paths_from_markdown()"]
        REFS["Figure 引用列表<br/>(fig_id, context, pos)"]
        IMG_TAGS["图片标签列表"]
    end

    subgraph Step4["Step 4: PDF 图片提取"]
        IMG_EXT["PDFImageExtractor"]
        EMBED{"有嵌入图片?"}
        EXTRACT_EMB["提取嵌入图片"]
        RENDER["渲染页面为图片"]
        MATCH["match_images_to_figures()"]
        IMG_MAP["Figure-图片映射"]
    end

    subgraph Step5["Step 5: 图像语义分析"]
        VLM_CHECK{"VLM 可用?"}
        VLM["VLMClient<br/>(ERNIE-VL)"]
        FALLBACK["Fallback<br/>(LLM 文本分析)"]
        RETRY["重试机制<br/>(指数退避)"]
        RESULT["结构化结果<br/>{entities, relations, summary}"]
    end

    subgraph Output["📊 输出"]
        KG_DATA["知识图谱数据"]
    end

    %% 连接
    PDF --> OCR
    OCR --> MD
    MD --> CHUNK
    CHUNK --> CHUNKS
    
    MD --> EXTRACT_REF
    MD --> EXTRACT_IMG
    EXTRACT_REF --> REFS
    EXTRACT_IMG --> IMG_TAGS
    
    PDF --> IMG_EXT
    IMG_EXT --> EMBED
    EMBED -->|是| EXTRACT_EMB
    EMBED -->|否| RENDER
    EXTRACT_EMB --> MATCH
    RENDER --> MATCH
    REFS --> MATCH
    MATCH --> IMG_MAP
    
    IMG_MAP --> VLM_CHECK
    REFS --> VLM_CHECK
    VLM_CHECK -->|是| VLM
    VLM_CHECK -->|否| FALLBACK
    VLM -->|429/500| RETRY
    RETRY --> VLM
    VLM --> RESULT
    FALLBACK --> RESULT
    
    RESULT --> KG_DATA
    CHUNKS --> KG_DATA
```

## 详细模块说明

### 📁 文件结构

```
extraction/
├── __init__.py              # 模块导出
├── paddleocr_vl.py          # PaddleOCR-VL MCP 客户端
├── text_extractor.py        # chunk_text() 文本分块
├── vision_extractor.py      # Figure 引用 + VLM 分析
└── image_extractor.py       # PDF 图片提取

utils/
└── vllm_client.py           # VLM 客户端 (重试 + Fallback)
```

### 🔄 数据流详解

```mermaid
flowchart LR
    subgraph A["1️⃣ PaddleOCR-VL"]
        A1["PDF"] --> A2["MCP 服务"]
        A2 --> A3["Markdown<br/>202K chars"]
    end

    subgraph B["2️⃣ 文本分块"]
        B1["Markdown"] --> B2["按标题分割"]
        B2 --> B3["68 chunks<br/>~3000 chars/chunk"]
    end

    subgraph C["3️⃣ 引用提取"]
        C1["正则匹配"] --> C2["Figure X"]
        C1 --> C3["Fig. X"]
        C1 --> C4["图 X"]
        C2 & C3 & C4 --> C5["7 个引用"]
    end

    subgraph D["4️⃣ 图片提取"]
        D1["PyMuPDF"] --> D2{"嵌入图片?"}
        D2 -->|有| D3["提取"]
        D2 -->|无| D4["渲染页面"]
        D3 & D4 --> D5["3 张图片"]
    end

    subgraph E["5️⃣ VLM 分析"]
        E1["图片 + 上下文"] --> E2{"VLM OK?"}
        E2 -->|是| E3["ERNIE-VL"]
        E2 -->|否| E4["LLM Fallback"]
        E3 & E4 --> E5["JSON 结果"]
    end

    A3 --> B1
    A3 --> C1
    C5 --> D1
    D5 --> E1
    C5 --> E1
```

### ⚡ 错误处理与重试机制

```mermaid
flowchart TD
    START["调用 VLM"] --> CHECK{"响应状态?"}
    
    CHECK -->|200 OK| SUCCESS["✅ 返回结果"]
    CHECK -->|429 限流| WAIT1["等待 2^n 秒"]
    CHECK -->|500 服务器错误| WAIT2["等待 2^n 秒"]
    CHECK -->|403 禁止| FALLBACK["🔄 Fallback"]
    CHECK -->|其他错误| FALLBACK
    
    WAIT1 --> RETRY{"重试次数 < 3?"}
    WAIT2 --> RETRY
    
    RETRY -->|是| START
    RETRY -->|否| FALLBACK
    
    FALLBACK --> LLM["LLMClient<br/>(DeepSeek-v3)"]
    LLM --> ANALYZE["分析图注文本"]
    ANALYZE --> SUCCESS2["✅ 返回结果"]
    
    style SUCCESS fill:#90EE90
    style SUCCESS2 fill:#90EE90
    style FALLBACK fill:#FFE4B5
```

### 📊 输出数据结构

```mermaid
classDiagram
    class ExtractedChunk {
        +str content
        +str section_title
        +int start_pos
        +int end_pos
    }
    
    class FigureReference {
        +str figure_id
        +str context_sentence
        +int start_pos
        +int end_pos
    }
    
    class ExtractedImage {
        +str path
        +int page
        +str size
        +str type
    }
    
    class FigureAnalysis {
        +List~Entity~ entities
        +List~Relation~ relations
        +str summary
    }
    
    class Entity {
        +str type
        +str name
    }
    
    class Relation {
        +str source
        +str target
        +str type
    }
    
    FigureAnalysis --> Entity
    FigureAnalysis --> Relation
```

## 🎯 关键函数调用链

```
main.py
│
├── PaddleOCRVLClient.parse_pdf(pdf_path)
│   └── → markdown: str
│
├── chunk_text(markdown)
│   └── → chunks: List[str]
│
├── extract_figure_references(markdown)
│   └── → refs: List[(fig_id, context, start, end)]
│
├── PDFImageExtractor.extract_images(pdf_path)
│   ├── extract_embedded_images()
│   └── extract_page_as_image() [fallback]
│       └── → images: List[Dict]
│
├── match_images_to_figures(images, refs, markdown)
│   └── → matches: Dict[fig_id → image_info]
│
└── VLMClient.analyze_figure(image_path, caption, context)
    ├── _call_with_retry()
    │   └── → VLM response
    └── _fallback_text_analysis() [if VLM unavailable]
        └── → {entities, relations, summary}
```

## 📈 性能指标 (测试文件)

| 步骤 | 耗时 | 输出 |
|------|------|------|
| PaddleOCR-VL | ~10s | 202,731 chars |
| 文本分块 | <1s | 68 chunks |
| 引用提取 | <1s | 7 refs |
| 图片提取 | ~2s | 3 images |
| VLM/Fallback | ~3s | 9 entities, 6 relations |

---

*Generated for AI科研辅助智能体 Demo*
