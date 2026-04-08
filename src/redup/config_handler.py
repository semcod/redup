from redup.core.config import config_to_scan_config, load_config

SCAN_PROPERTIES = {
    "path": {
        "type": "string",
        "description": "Path to the project directory",
    },
    # other properties...
}

TOOL_SCHEMA_REDUP = {
    "analyze_project": {
        "name": "analyze_project",
        "description": "Analyze a project and generate duplication findings",
        "inputSchema": {
            "type": "object",
            "properties": SCAN_PROPERTIES,
            "required": ["path"],
        },
    },
    # other tools...
}