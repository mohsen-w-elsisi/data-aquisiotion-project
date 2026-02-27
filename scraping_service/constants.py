"""
The constants requiered by the application.
"""

import yaml

with open("env.yaml", "r", encoding="utf-8") as f:
    _env_vars = yaml.safe_load(f)

SERB_API_KEY = _env_vars["serb_api_key"]
