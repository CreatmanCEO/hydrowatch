# Architecture

## System Context (C4 Level 1)

```mermaid
graph TB
    User["Hydrogeologist / Operator"]
    HW["HydroWatch System"]
    LLM["LLM Providers"]
    DB["PostgreSQL + PostGIS"]

    User -->|"browser"| HW
    HW -->|"API calls"| LLM
    HW -->|"spatial queries"| DB

    subgraph LLM Providers
        Gemini["Gemini 2.5 Flash"]
        Cerebras["Cerebras Llama 3.3 70B"]
        Haiku["Anthropic Haiku 4.5"]
        Sonnet["Anthropic Sonnet 4.5"]
    end
```

## Container Diagram (C4 Level 2)

```mermaid
graph TB
    subgraph Browser
        Map["MapLibre GL<br/>Wells, Depression Cones, Layers"]
        Chat["Chat Panel<br/>SSE Streaming, Structured Cards"]
        Metrics["Metrics Dashboard<br/>Model Comparison"]
        Stores["Zustand Stores<br/>Map State, Chat State"]
    end

    subgraph "FastAPI Backend"
        SSE["SSE Chat Endpoint<br/>POST /api/chat/stream"]
        PE["Prompt Engine<br/>3-level hierarchy"]
        Router["LLM Router<br/>Pool A + Pool B"]
        TE["Tool Executor<br/>5 MCP-style tools"]
        AD["Anomaly Detector<br/>Debit, TDS, Sensor"]
        Eval["Eval Pipeline<br/>48 cases, batch comparison"]
        Wells["Wells API<br/>GeoJSON, History"]
        Upload["CSV Upload<br/>Validation"]
    end

    subgraph "Data Layer"
        PG["PostgreSQL + PostGIS"]
        GeoJSON["wells.geojson"]
        CSV["observations/*.csv"]
    end

    subgraph "LLM Providers"
        PoolA["Pool A: Gemini Flash ↔ Cerebras Llama"]
        PoolB["Pool B: Haiku 4.5 → Sonnet 4.5"]
    end

    Map --> Stores
    Chat --> Stores
    Stores -->|"Context Bridge"| SSE
    Chat -->|"SSE"| SSE
    Map --> Wells
    Chat --> Upload

    SSE --> PE
    PE --> Router
    Router --> PoolA
    Router --> PoolB
    SSE --> TE
    TE --> AD
    TE --> Wells
    TE --> Upload

    Wells --> GeoJSON
    Wells --> CSV
    AD --> CSV
    Upload --> CSV
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant CB as Context Bridge
    participant API as FastAPI
    participant PE as Prompt Engine
    participant LLM as LLM Router
    participant TE as Tool Executor

    U->>F: "Show anomalies in viewport"
    F->>CB: Serialize map state (viewport, layers, selection)
    CB->>API: POST /api/chat/stream + MapContext
    API->>PE: Build system prompt (role + domain + adaptor + task + output + context)
    PE->>LLM: Route to Pool B (complex task)
    LLM-->>API: Tool call: detect_anomalies({well_id: ...})
    API->>TE: Execute tool (read-only, Pydantic validated)
    TE-->>API: List[AnomalyCard]
    API->>LLM: Feed tool results back
    LLM-->>API: Stream interpretation tokens
    API-->>F: SSE events: meta → tool_call → tool_result → tokens → done
    F->>U: Render: streaming text + AnomalyCard components
```

## Prompt Engine Architecture

```
Final Prompt = Level 0: Base Role (~200 tokens)
             + Level 1: Domain Knowledge (~600 tokens)
             + Model Adaptor (per provider, ~150 tokens)
             + Task Instructions (per task type, ~200 tokens)
             + Output Format (per response type, ~80 tokens)
             + Level 2: Context Bridge (runtime, variable)
```

Level 1 domain knowledge simulates what a fine-tuned model would know natively. For production, this knowledge would be embedded via fine-tuning; here we inject it as context for faster iteration with the same effect.

## Model Routing

| Pool | Models | Fallback | Tasks |
|------|--------|----------|-------|
| Pool A | Gemini 2.5 Flash ↔ Cerebras Llama 3.3 70B | Mutual | validate_csv, query_wells, get_region_stats, get_well_history |
| Pool B | Anthropic Haiku 4.5 | — | detect_anomalies, interpret_anomaly, general_question |
| Pool B+ | Anthropic Sonnet 4.5 | — | calibration_advice (complex reasoning) |

## Architecture Decision Records

See [docs/adr/](docs/adr/) for detailed rationale behind key technical decisions.
