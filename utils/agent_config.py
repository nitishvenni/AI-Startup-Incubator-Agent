"""
utils/agent_config.py - Load and cache AGENT_INSTRUCTIONS.yaml.

Usage:
    from utils.agent_config import get_agent_config
    cfg = get_agent_config()
    print(cfg["mentor_personality"])
"""

import os
import yaml
import logging
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)

_INSTRUCTIONS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "AGENT_INSTRUCTIONS.yaml"
)

_DEFAULTS = {
    "mentor_personality": "encouraging",
    "business_tone": "professional",
    "creativity": 7,
    "industry_focus": "",
    "default_country": "United States",
    "funding_focus": "mixed",
    "writing_style": "structured",
    "language": "en",
    "mentor_name": "Granite Mentor",
    "sections": {
        "executive_summary": True,
        "problem_analysis": True,
        "solution": True,
        "customer_personas": True,
        "market_research": True,
        "competitor_analysis": True,
        "swot_analysis": True,
        "business_model_canvas": True,
        "revenue_model": True,
        "pricing_strategy": True,
        "estimated_budget": True,
        "funding_suggestions": True,
        "government_schemes": True,
        "legal_checklist": True,
        "technology_recommendation": True,
        "development_roadmap": True,
        "weekly_timeline": True,
        "marketing_strategy": True,
        "customer_acquisition_plan": True,
        "investor_pitch": True,
        "risk_analysis": True,
        "success_metrics": True,
        "mentor_advice": True,
    },
}

_lock = threading.Lock()
_cache: dict | None = None
_last_mtime: float = 0.0


def get_agent_config() -> dict:
    """Return the merged config (file values override defaults). Re-reads if file changed."""
    global _cache, _last_mtime

    try:
        mtime = os.path.getmtime(_INSTRUCTIONS_PATH)
    except OSError:
        return dict(_DEFAULTS)

    with _lock:
        if _cache is not None and mtime == _last_mtime:
            return _cache

        try:
            with open(_INSTRUCTIONS_PATH, "r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
            merged = {**_DEFAULTS, **raw}
            # Deep-merge the sections dict
            if isinstance(raw.get("sections"), dict):
                merged["sections"] = {**_DEFAULTS["sections"], **raw["sections"]}
            _cache = merged
            _last_mtime = mtime
            logger.debug("AGENT_INSTRUCTIONS.yaml reloaded.")
        except Exception as exc:
            logger.warning("Could not load AGENT_INSTRUCTIONS.yaml: %s", exc)
            _cache = dict(_DEFAULTS)
            _last_mtime = mtime

        return _cache
