"""
services/watsonx_service.py

Thin wrapper around the IBM watsonx.ai Python SDK.
All credentials are sourced exclusively from app.config (loaded from .env).
"""

import json
import re
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams


def _build_client(app) -> ModelInference:
    """Construct an authenticated ModelInference client."""
    credentials = Credentials(
        url=app.config["IBM_URL"],
        api_key=app.config["IBM_API_KEY"],
    )
    params = {
        GenParams.MAX_NEW_TOKENS: app.config["WX_MAX_NEW_TOKENS"],
        GenParams.MIN_NEW_TOKENS: app.config["WX_MIN_NEW_TOKENS"],
        GenParams.TEMPERATURE: app.config["WX_TEMPERATURE"],
        GenParams.TOP_P: app.config["WX_TOP_P"],
        GenParams.TOP_K: app.config["WX_TOP_K"],
        GenParams.REPETITION_PENALTY: app.config["WX_REPETITION_PENALTY"],
    }
    return ModelInference(
        model_id=app.config["IBM_MODEL"],
        credentials=credentials,
        project_id=app.config["IBM_PROJECT_ID"],
        params=params,
    )


def generate_text(app, prompt: str) -> str:
    """
    Send *prompt* to Granite and return the generated text string.
    Raises RuntimeError on any SDK or network failure.
    """
    if not app.config.get("IBM_API_KEY") or not app.config.get("IBM_PROJECT_ID"):
        raise RuntimeError(
            "IBM credentials are not configured. "
            "Please set IBM_API_KEY and IBM_PROJECT_ID in your .env file."
        )
    try:
        client = _build_client(app)
        response = client.generate_text(prompt=prompt)
        return response.strip() if isinstance(response, str) else str(response)
    except Exception as exc:
        raise RuntimeError(f"watsonx.ai generation failed: {exc}") from exc


def analyze_startup(app, startup_data: dict) -> dict:
    """
    Run a structured business analysis of *startup_data* through Granite.

    Returns a dict with keys:
        content          - full markdown analysis text
        viability_score  - int 0-100
        market_score     - int 0-100
        innovation_score - int 0-100
        execution_score  - int 0-100
    """
    prompt = _build_analysis_prompt(startup_data)
    raw = generate_text(app, prompt)
    return _parse_analysis(raw)


def chat_with_mentor(app, user_message: str, context: dict | None = None) -> str:
    """
    Have a free-form conversation with the AI startup mentor.

    *context* may contain 'startup_name', 'industry', 'history' (list of dicts).
    """
    prompt = _build_chat_prompt(user_message, context or {})
    return generate_text(app, prompt)


# ------------------------------------------------------------------ #
# Private prompt builders                                              #
# ------------------------------------------------------------------ #

def _build_analysis_prompt(d: dict) -> str:
    return f"""You are an expert startup mentor and business analyst with 20 years of experience in venture capital, product strategy, and market research.

Analyze the following startup idea and provide a comprehensive, professional business assessment.

STARTUP DETAILS:
- Startup Name: {d.get('startup_name', 'N/A')}
- Founder: {d.get('founder_name', 'N/A')}
- Country: {d.get('country', 'N/A')}
- Industry: {d.get('industry', 'N/A')}
- Budget: {d.get('budget', 'N/A')}
- Target Audience: {d.get('target_audience', 'N/A')}
- Business Goal: {d.get('business_goal', 'N/A')}
- Idea Description: {d.get('idea_description', 'N/A')}

Provide your analysis in the following EXACT structure (keep the section headers exactly as shown):

## Executive Summary
[2-3 sentence overview of the startup and its potential]

## Problem & Solution
[Describe the problem being solved and how this startup addresses it]

## Market Opportunity
[Market size, trends, and growth potential]

## Competitive Landscape
[Key competitors and differentiation strategy]

## Business Model
[Revenue model, pricing strategy, and monetisation approach]

## Target Audience Analysis
[Detailed profile of the ideal customer]

## Go-To-Market Strategy
[Recommended launch and growth strategy]

## Financial Outlook
[Revenue projections, break-even analysis, and funding needs based on the stated budget]

## Risks & Challenges
[Top 3-5 risks and mitigation strategies]

## Actionable Recommendations
[5 concrete next steps the founder should take immediately]

## Scores (JSON)
Provide ONLY the following JSON block at the very end, no extra text:
{{"viability_score": <0-100>, "market_score": <0-100>, "innovation_score": <0-100>, "execution_score": <0-100>}}

Be specific, data-driven, and actionable. Avoid generic advice.
"""


def _build_chat_prompt(message: str, context: dict) -> str:
    startup_context = ""
    if context.get("startup_name"):
        startup_context = (
            f"The user is working on a startup called '{context['startup_name']}' "
            f"in the {context.get('industry', 'technology')} industry. "
        )

    history_text = ""
    history = context.get("history", [])
    if history:
        pairs = []
        for msg in history[-6:]:  # keep last 3 turns
            role_label = "User" if msg["role"] == "user" else "Mentor"
            pairs.append(f"{role_label}: {msg['content']}")
        history_text = "\n".join(pairs) + "\n"

    return f"""You are an expert AI startup mentor with deep knowledge in entrepreneurship, venture capital, product development, marketing, and technology. You provide clear, practical, and encouraging advice to founders.

{startup_context}

Conversation so far:
{history_text}User: {message}
Mentor:"""


def _parse_analysis(raw: str) -> dict:
    """Extract scores from the JSON block appended by Granite, fall back to defaults."""
    scores = {
        "viability_score": 70,
        "market_score": 70,
        "innovation_score": 70,
        "execution_score": 70,
    }

    # Try to find the JSON scores block.
    json_match = re.search(r"\{[^{}]*viability_score[^{}]*\}", raw, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            for key in scores:
                if key in parsed:
                    val = int(parsed[key])
                    scores[key] = max(0, min(100, val))
            # Remove the JSON block from the display content.
            raw = raw[: json_match.start()].rstrip()
        except (json.JSONDecodeError, ValueError):
            pass

    return {"content": raw, **scores}
