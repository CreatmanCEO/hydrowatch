# HydroWatch — Research Summary
## Итоги исследования: финальный стек и ключевые решения

---

## ФИНАЛЬНЫЙ СТЕК ПРОЕКТА

### Backend (Python)
```bash
pip install fastapi uvicorn litellm "instructor[google-genai]" \
  langfuse deepeval pydantic pydantic-settings \
  numpy scipy pandas geopandas shapely pyproj \
  adtk statsmodels folium
```

| Компонент | Библиотека | Версия | Зачем |
|-----------|-----------|--------|-------|
| Web framework | FastAPI | latest | REST API + SSE streaming |
| LLM routing | LiteLLM | 1.83+ | Gemini Flash/Pro, fallback, единый API |
| Structured output | Instructor | 1.15+ | Pydantic-модели из LLM ответов |
| Observability | Langfuse | 4.3+ | Трейсинг, cost, latency (self-hosted) |
| LLM тестирование | DeepEval | 3.9+ | Hallucination, faithfulness, accuracy |
| Валидация данных | Pydantic v2 | latest | Schemas, Settings, API contracts |
| Гидромоделирование | scipy.special.exp1 | — | Формула Тейса, 15 строк, без внешних deps |
| Данные | numpy + pandas | — | Временные ряды, CSV |
| Геоданные | geopandas + shapely + pyproj | — | GeoJSON, буферы, координаты |
| Аномалии | adtk | latest | Rule-based детекция, валидация |
| Тренды | statsmodels | latest | Декомпозиция временных рядов |
| Dev-карты | folium | latest | HTML-карта для проверки данных |

### Frontend (TypeScript)
```bash
npm install react-map-gl maplibre-gl @turf/circle zustand \
  @microsoft/fetch-event-source
```

| Компонент | Библиотека | Зачем |
|-----------|-----------|-------|
| Карта | react-map-gl + maplibre-gl | Декларативные слои, events |
| Тайлы | OpenFreeMap | Бесплатно, без ключей, без лимитов |
| Воронки | @turf/circle | Концентрические кольца для depression cones |
| State management | Zustand | Viewport, layers, filters → context bridge |
| SSE клиент | @microsoft/fetch-event-source | POST + SSE streaming |
| Framework | Next.js 15 | App Router, TypeScript |

### LLM
| Модель | Использование | Цена |
|--------|--------------|------|
| Gemini 2.5 Flash | Основная (tool calling, structured output) | Free tier: 10 RPM |
| Gemini 2.5 Pro | Сложные задачи (fallback) | Free tier: 5 RPM |
| Gemini 2.5 Flash-Lite | Eval (batch, дешёвые тесты) | $0.10/1M input |
| gemini-embedding-001 | Embeddings (если будет RAG) | Бесплатно |
| Gemini Batch API | Eval pipeline (50% скидка) | 50% от стандарта |

**Бюджет: < $5 из $20**

---

## КЛЮЧЕВЫЕ РЕШЕНИЯ ПО РЕЗУЛЬТАТАМ RESEARCH

### 1. LLM: Instructor + LiteLLM (не raw API)
- **Instructor** гарантирует Pydantic-модели из ответов Gemini
- При ошибке валидации — автоматический retry с feedback
- LiteLLM — единый интерфейс, можно менять провайдера одной строкой

### 2. Гидромоделирование: scipy, не FloPy
- Формула Тейса через `scipy.special.exp1` — 15 строк
- Суперпозиция для интерференции — ещё 20 строк
- FloPy требует MODFLOW бинарник — overkill для демо

### 3. Карта: react-map-gl + OpenFreeMap
- OpenFreeMap — 0$, без API ключей, без лимитов
- react-map-gl — декларативный React-подход (`<Source>`, `<Layer>`)
- Воронки: концентрические кольца через @turf/circle

### 4. SSE: FastAPI EventSourceResponse
- FastAPI 0.115+ имеет нативный `EventSourceResponse`
- Frontend: `@microsoft/fetch-event-source` для POST + SSE

### 5. State: Zustand с getApiContext()
- `useMapStore.getState().getApiContext()` — доступ вне React
- Сериализация viewport + layers + filters → отправка на бэкенд

### 6. Eval: DeepEval + Gemini Batch API
- DeepEval для hallucination/faithfulness тестов
- Gemini Batch API для сравнения Flash vs Pro (50% скидка)
- Langfuse для runtime observability

### 7. Данные: собственный генератор
- 25-30 скважин в районе Абу-Даби (Al Wathba, Mussafah, Sweihan, Al Khatim)
- Параметры: TDS 2000-8000 мг/л, глубины 60-350м, дебит 2-30 л/с
- Аномалии: депрессионная воронка, падение дебита, интерференция
- Формат: GeoJSON (скважины) + CSV (временные ряды)

---

## ПРОПУЩЕННЫЕ БИБЛИОТЕКИ (и почему)

| Библиотека | Почему пропустили |
|-----------|------------------|
| LangChain | Overkill, абстракции мешают, тяжёлые deps |
| LlamaIndex | Нет RAG в демо |
| DSPy | Нужен dataset, сложно, нестабильный API |
| FloPy/MODFLOW | Требует внешний бинарник, overkill |
| Outlines/jsonformer | Только для локальных моделей, не для API |
| PyOD | Overkill для аномалий, ADTK достаточно |
| MockSeries | Проще написать руками на numpy |
| ChromaDB | Нет RAG-компонента в MVP |

---

## GEMINI API — КЛЮЧЕВЫЕ GOTCHAS

1. **Temperature для Gemini 2.5**: LiteLLM дефолтит 1.0. Для structured output ставить 0.0-0.3
2. **Free tier урезан** (декабрь 2025): Flash 10 RPM / 250 RPD — достаточно для демо, но не для нагрузочного eval
3. **Batch API**: inline до 20 MB, JSONL до 2 GB. Результаты через polling (PENDING → RUNNING → SUCCEEDED)
4. **Function calling через LiteLLM**: используй стандартный OpenAI формат `tools`, LiteLLM конвертирует
5. **Parallel tool calls**: не полностью стабильны с Gemini 2.5 Flash — тестировать

---

## РЕАЛИСТИЧНЫЕ ПАРАМЕТРЫ СКВАЖИН АБУ-ДАБИ

| Параметр | Диапазон | Единица |
|----------|----------|---------|
| Глубина скважины | 60–350 | м |
| Статический уровень | 20–80 | м от поверхности |
| Динамический уровень | 40–120 | м |
| Дебит | 2–30 (типично 5-15) | л/с |
| TDS | 2,000–8,000 | мг/л |
| pH | 7.0–8.5 | — |
| Хлориды | 300–5,000 | мг/л |
| Температура воды | 28–38 | °C |
| Водопроводимость (T) | 50–2,000 | м²/сут |
| Водоотдача (S) | 0.001–0.01 | — |

**Горизонты**: Dammam (80-200м), Umm Er Radhuma (150-350м), песчаник (300-500м), аллювий (10-60м)
**Координаты**: WGS84, район 24.2-24.6°N, 54.3-55.8°E
