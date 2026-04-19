"""JSON Schema definitions for LLM tool calling."""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "validate_csv",
            "description": "Validate an uploaded CSV file with groundwater observations. Checks columns, data types, value ranges, and metadata consistency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the CSV file to validate",
                    },
                    "expected_columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Expected column names",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_wells",
            "description": "Query monitoring wells with optional filters. Returns well info including location, depth, aquifer type, current yield, and water quality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                        "description": "Bounding box [west, south, east, north] in WGS84",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "maintenance"],
                        "description": "Filter by well status",
                    },
                    "cluster_id": {
                        "type": "string",
                        "description": "Filter by well cluster ID (e.g., AL_WATHBA, SWEIHAN)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": "Run anomaly detection on well time series data. Detects debit decline, TDS spikes, and sensor faults. Can analyze a single well or all wells.",
            "parameters": {
                "type": "object",
                "properties": {
                    "well_id": {
                        "type": "string",
                        "description": "Well ID to analyze (e.g., AUH-01-003). Omit to scan all wells.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_well_history",
            "description": "Get time series data for a specific well with trend analysis. Returns timestamps, values, and trend direction (rising/falling/stable).",
            "parameters": {
                "type": "object",
                "properties": {
                    "well_id": {
                        "type": "string",
                        "description": "Well ID (e.g., AUH-01-003)",
                    },
                    "parameter": {
                        "type": "string",
                        "enum": ["debit_ls", "tds_mgl", "ph", "chloride_mgl", "water_level_m", "temperature_c"],
                        "description": "Which parameter to retrieve",
                        "default": "debit_ls",
                    },
                    "last_n_days": {
                        "type": "integer",
                        "description": "Only return the last N days of data",
                    },
                },
                "required": ["well_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_region_stats",
            "description": "Get aggregated statistics for all wells within a bounding box. Returns well count, average debit, average TDS, and anomaly count.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                        "description": "Bounding box [west, south, east, north] in WGS84",
                    },
                },
                "required": ["bbox"],
            },
        },
    },
]
