"""
services/mentor_ai_service.py

All IBM Granite prompt logic for the AI Startup Mentor incubation report.
Personality, tone, and style are read from AGENT_INSTRUCTIONS.yaml at runtime.
"""

import json
import re
import logging
import traceback
from services.watsonx_service import generate_text
from utils.agent_config import get_agent_config

logger = logging.getLogger(__name__)
print("[TRACE] MODULE LOAD services.mentor_ai_service __file__ =", __file__)
print("[TRACE] services.mentor_ai_service.generate_text =", generate_text)
print("[TRACE] services.mentor_ai_service.generate_text.__globals__['__file__'] =", generate_text.__globals__.get("__file__"))


# ------------------------------------------------------------------ #
# Public entry point                                                   #
# ------------------------------------------------------------------ #

def generate_incubation_report(app, data: dict) -> dict:
    """
    Generate a complete incubation report for *data* using AGENT_INSTRUCTIONS config.

    Returns a dict with:
        validation_score  – int 0-100
        sections          – dict keyed by section slug → text content
    """
    print("[TRACE] ENTER services.mentor_ai_service.generate_incubation_report(app, data)")
    print("[TRACE] services.mentor_ai_service __file__ =", __file__)
    print("[TRACE] Incubation uses shared generate_text from =", generate_text.__globals__.get("__file__"))
    print("[TRACE] generate_incubation_report data =", repr(data))
    try:
        cfg = get_agent_config()
        print("[TRACE] generate_incubation_report agent cfg =", repr(cfg))
        prompt = _build_incubation_prompt(data, cfg)
        print("[TRACE] generate_incubation_report prompt length =", len(prompt))
        print("[TRACE] generate_incubation_report prompt preview =", repr(prompt[:1000]))
        raw = generate_text(app, prompt, max_new_tokens=4096)
        print("[TRACE] generate_incubation_report raw AI response length =", len(raw))
        print("[TRACE] generate_incubation_report raw AI response =", raw)
        parsed = _parse_incubation_report(raw)
        print("[TRACE] EXIT services.mentor_ai_service.generate_incubation_report(app, data)")
        return parsed
    except Exception:
        print("[TRACE] EXCEPTION in services.mentor_ai_service.generate_incubation_report(app, data)")
        traceback.print_exc()
        raise


# ------------------------------------------------------------------ #
# Prompt builder — tuned from AGENT_INSTRUCTIONS                      #
# ------------------------------------------------------------------ #

def _build_incubation_prompt(d: dict, cfg: dict) -> str:
    print("[TRACE] ENTER services.mentor_ai_service._build_incubation_prompt(d, cfg)")
    personality   = cfg.get("mentor_personality", "encouraging")
    tone          = cfg.get("business_tone", "professional")
    creativity    = cfg.get("creativity", 7)
    industry_focus = cfg.get("industry_focus", "")
    country_ctx   = d.get("country") or cfg.get("default_country", "United States")
    funding_focus = cfg.get("funding_focus", "mixed")
    writing_style = cfg.get("writing_style", "structured")
    mentor_name   = cfg.get("mentor_name", "Granite Mentor")
    sections_cfg  = cfg.get("sections", {})

    persona_map = {
        "encouraging": "You are highly encouraging, optimistic, and motivating. You celebrate potential while being honest about challenges.",
        "direct":      "You are direct, no-nonsense, and action-oriented. You give blunt, practical feedback without sugar-coating.",
        "socratic":    "You use the Socratic method, asking probing questions and guiding the founder to discover insights themselves.",
        "analytical":  "You are highly data-driven and analytical. You cite statistics, frameworks, and evidence in all your responses.",
        "visionary":   "You are a visionary thinker who helps founders see the biggest possible future for their startup.",
    }
    persona_desc = persona_map.get(personality, persona_map["encouraging"])

    funding_map = {
        "bootstrapping": "Focus advice on lean, self-funded growth strategies.",
        "angel":         "Prioritise angel investor outreach and early-stage fundraising.",
        "vc":            "Focus on venture-capital ready growth, metrics, and pitch preparation.",
        "grants":        "Highlight government grants, research funding, and non-dilutive capital.",
        "mixed":         "Cover a balanced mix of funding approaches suitable for the stage.",
    }
    funding_desc = funding_map.get(funding_focus, funding_map["mixed"])

    style_map = {
        "concise":      "Be concise. Use short paragraphs. Avoid filler text.",
        "detailed":     "Be thorough and detailed. Cover every aspect comprehensively.",
        "bullet-heavy": "Use bullet points heavily. Minimise prose paragraphs.",
        "narrative":    "Write in a narrative, story-telling style.",
        "structured":   "Use clear structure with headers, bullets, and numbered lists where appropriate.",
    }
    style_desc = style_map.get(writing_style, style_map["structured"])

    industry_note = f"You have deep expertise in the {industry_focus} sector." if industry_focus else ""
    creativity_note = f"Creativity level: {creativity}/10 — {'be highly creative and unconventional' if creativity >= 8 else 'balance creativity with practicality' if creativity >= 5 else 'stay conventional and proven'}."

    # Build section list based on sections_cfg
    active_sections = []
    all_sections_with_prompts = [
        ("VALIDATION_SCORE", "<score between 0 and 100 as a single integer, e.g. 78>"),
        ("EXECUTIVE_SUMMARY", "<2-3 paragraph compelling executive summary of this startup>"),
        ("PROBLEM_ANALYSIS", "<Detailed analysis of the core problem being solved, its scale, and why existing solutions fail>"),
        ("SOLUTION", "<Description of the proposed solution, how it works, and its unique value proposition>"),
        ("CUSTOMER_PERSONAS", "<3 detailed customer personas: name, age, role, pain points, goals, how this startup helps them>"),
        ("MARKET_RESEARCH", "<Market size (TAM/SAM/SOM), growth rates, key trends, and market dynamics with specific numbers>"),
        ("COMPETITOR_ANALYSIS", "<List 4-5 competitors in format: Competitor Name | Strengths | Weaknesses | Our Advantage>"),
        ("SWOT_ANALYSIS", "<Strengths: list 4 items. Weaknesses: list 4 items. Opportunities: list 4 items. Threats: list 4 items. Use labels STRENGTHS:, WEAKNESSES:, OPPORTUNITIES:, THREATS:>"),
        ("BUSINESS_MODEL_CANVAS", "<Nine building blocks in format — Key Partners: ... | Key Activities: ... | Key Resources: ... | Value Propositions: ... | Customer Relationships: ... | Channels: ... | Customer Segments: ... | Cost Structure: ... | Revenue Streams: ...>"),
        ("REVENUE_MODEL", "<Detailed explanation of how the startup makes money, primary and secondary revenue streams>"),
        ("PRICING_STRATEGY", "<Recommended pricing tiers, rationale, and competitive positioning>"),
        ("ESTIMATED_BUDGET", "<Breakdown of budget allocation: technology, marketing, operations, team, legal, contingency>"),
        ("FUNDING_SUGGESTIONS", f"<Recommended funding stages, amounts, investor types, and fundraising timeline. {funding_desc}>"),
        ("GOVERNMENT_SCHEMES", f"<Relevant government grants, incubator programs, and startup schemes available in {country_ctx}>"),
        ("LEGAL_CHECKLIST", "<Checklist of legal requirements: business registration, IP protection, contracts, compliance, licenses>"),
        ("TECHNOLOGY_RECOMMENDATION", "<Recommended tech stack, tools, platforms, and infrastructure for building this startup>"),
        ("DEVELOPMENT_ROADMAP", "<Phase 1 (0-3 months), Phase 2 (3-6 months), Phase 3 (6-12 months) milestones and deliverables>"),
        ("WEEKLY_TIMELINE", "<Week 1-4 plan: specific tasks and goals for the first month to get started immediately>"),
        ("MARKETING_STRATEGY", "<Complete marketing strategy: brand positioning, content marketing, SEO, social media, PR>"),
        ("CUSTOMER_ACQUISITION_PLAN", "<Step-by-step customer acquisition funnel, channels, CAC estimates, and conversion tactics>"),
        ("INVESTOR_PITCH", "<A compelling 6-sentence investor pitch covering problem, solution, market, traction, team, ask>"),
        ("RISK_ANALYSIS", "<Top 5 risks with impact level (High/Medium/Low) and mitigation strategies for each>"),
        ("SUCCESS_METRICS", "<Key Performance Indicators (KPIs), OKRs, and milestone targets for Year 1 and Year 2>"),
        ("MENTOR_ADVICE", "<Personalized, direct mentor advice: top 5 things this founder must do right now to succeed>"),
    ]

    for key, prompt_hint in all_sections_with_prompts:
        section_key = key.lower()
        if sections_cfg.get(section_key, True):
            active_sections.append(f"[{key}]\n{prompt_hint}")

    sections_text = "\n\n".join(active_sections)

    prompt = f"""You are {mentor_name}, an elite AI Startup Mentor with 25 years of experience in venture capital, product strategy, market research, legal compliance, and business development.

Personality: {persona_desc}
Tone: {tone}.
{style_desc}
{creativity_note}
{industry_note}

A founder has submitted their startup idea. Generate a COMPLETE, DETAILED, and PROFESSIONAL Incubation Report.

STARTUP DETAILS:
- Startup Name: {d.get('startup_name', 'N/A')}
- Founder: {d.get('founder_name', 'N/A')}
- Country: {country_ctx}
- Industry: {d.get('industry', 'N/A')}
- Budget: {d.get('budget', 'N/A')}
- Target Audience: {d.get('target_audience', 'N/A')}
- Business Goal: {d.get('business_goal', 'N/A')}
- Idea Description: {d.get('idea_description', 'N/A')}

Generate EXACTLY the following sections, using EXACTLY these section markers. Write 2-5 paragraphs or bullet points per section. Be specific, data-driven, and actionable. Do not be generic.

{sections_text}
"""
    print("[TRACE] _build_incubation_prompt active section count =", len(active_sections))
    print("[TRACE] EXIT services.mentor_ai_service._build_incubation_prompt(d, cfg)")
    return prompt


# ------------------------------------------------------------------ #
# Parser                                                               #
# ------------------------------------------------------------------ #

_SECTION_KEYS = [
    "VALIDATION_SCORE", "EXECUTIVE_SUMMARY", "PROBLEM_ANALYSIS", "SOLUTION",
    "CUSTOMER_PERSONAS", "MARKET_RESEARCH", "COMPETITOR_ANALYSIS", "SWOT_ANALYSIS",
    "BUSINESS_MODEL_CANVAS", "REVENUE_MODEL", "PRICING_STRATEGY", "ESTIMATED_BUDGET",
    "FUNDING_SUGGESTIONS", "GOVERNMENT_SCHEMES", "LEGAL_CHECKLIST",
    "TECHNOLOGY_RECOMMENDATION", "DEVELOPMENT_ROADMAP", "WEEKLY_TIMELINE",
    "MARKETING_STRATEGY", "CUSTOMER_ACQUISITION_PLAN", "INVESTOR_PITCH",
    "RISK_ANALYSIS", "SUCCESS_METRICS", "MENTOR_ADVICE",
]

_SECTION_TITLES = {
    "EXECUTIVE_SUMMARY":         "Executive Summary",
    "PROBLEM_ANALYSIS":          "Problem Analysis",
    "SOLUTION":                  "Solution",
    "CUSTOMER_PERSONAS":         "Customer Personas",
    "MARKET_RESEARCH":           "Market Research",
    "COMPETITOR_ANALYSIS":       "Competitor Analysis",
    "SWOT_ANALYSIS":             "SWOT Analysis",
    "BUSINESS_MODEL_CANVAS":     "Business Model Canvas",
    "REVENUE_MODEL":             "Revenue Model",
    "PRICING_STRATEGY":          "Pricing Strategy",
    "ESTIMATED_BUDGET":          "Estimated Budget",
    "FUNDING_SUGGESTIONS":       "Funding Suggestions",
    "GOVERNMENT_SCHEMES":        "Government Schemes",
    "LEGAL_CHECKLIST":           "Legal Checklist",
    "TECHNOLOGY_RECOMMENDATION": "Technology Recommendation",
    "DEVELOPMENT_ROADMAP":       "Development Roadmap",
    "WEEKLY_TIMELINE":           "Weekly Timeline",
    "MARKETING_STRATEGY":        "Marketing Strategy",
    "CUSTOMER_ACQUISITION_PLAN": "Customer Acquisition Plan",
    "INVESTOR_PITCH":            "Investor Pitch",
    "RISK_ANALYSIS":             "Risk Analysis",
    "SUCCESS_METRICS":           "Success Metrics",
    "MENTOR_ADVICE":             "Personalized Mentor Advice",
}


def _parse_incubation_report(raw: str) -> dict:
    """Extract each section from the structured Granite output. Falls back gracefully."""
    print("[TRACE] ENTER services.mentor_ai_service._parse_incubation_report(raw)")
    print("[TRACE] _parse_incubation_report raw length =", len(raw))
    sections: dict[str, str] = {}
    validation_score = 72  # sensible default

    for i, key in enumerate(_SECTION_KEYS):
        marker = f"[{key}]"
        start_idx = raw.find(marker)
        print("[TRACE] Parser marker", marker, "start_idx =", start_idx)
        if start_idx == -1:
            sections[key] = ""
            print("[TRACE] Parser missing section", key)
            continue

        content_start = start_idx + len(marker)
        end_idx = len(raw)
        for next_key in _SECTION_KEYS[i + 1:]:
            ni = raw.find(f"[{next_key}]", content_start)
            if ni != -1:
                end_idx = ni
                break

        content = raw[content_start:end_idx].strip()
        print("[TRACE] Parser section", key, "content length =", len(content))

        if key == "VALIDATION_SCORE":
            m = re.search(r"\b(\d{1,3})\b", content)
            if m:
                validation_score = max(0, min(100, int(m.group(1))))
                print("[TRACE] Parser validation_score =", validation_score)
        else:
            sections[key] = content

    # Parse structured sub-sections
    sections["_competitor_rows"] = _parse_competitor_rows(sections.get("COMPETITOR_ANALYSIS", ""))
    sections["_swot"] = _parse_swot(sections.get("SWOT_ANALYSIS", ""))
    sections["_bmc"] = _parse_bmc(sections.get("BUSINESS_MODEL_CANVAS", ""))

    result = {
        "validation_score": validation_score,
        "sections": sections,
        "titles": _SECTION_TITLES,
    }
    print("[TRACE] _parse_incubation_report result validation_score =", validation_score)
    print("[TRACE] _parse_incubation_report result section keys =", sorted(sections.keys()))
    print("[TRACE] EXIT services.mentor_ai_service._parse_incubation_report(raw)")
    return result


def _parse_competitor_rows(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        line = line.strip().lstrip("-•* ")
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            rows.append({
                "name":       parts[0] if len(parts) > 0 else "",
                "strengths":  parts[1] if len(parts) > 1 else "",
                "weaknesses": parts[2] if len(parts) > 2 else "",
                "advantage":  parts[3] if len(parts) > 3 else "",
            })
    return rows or [{"name": text, "strengths": "", "weaknesses": "", "advantage": ""}]


def _parse_swot(text: str) -> dict:
    swot = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
    current = None
    label_map = {
        "strengths": "strengths",
        "weaknesses": "weaknesses",
        "opportunities": "opportunities",
        "threats": "threats",
    }
    for line in text.splitlines():
        line_lower = line.lower().strip()
        matched = False
        for label, key in label_map.items():
            if line_lower.startswith(label):
                current = key
                matched = True
                remainder = line[len(label):].lstrip(": ").strip()
                if remainder:
                    swot[current].append(remainder)
                break
        if not matched and current and line.strip().lstrip("-•* "):
            swot[current].append(line.strip().lstrip("-•* "))
    return swot


def _parse_bmc(text: str) -> dict:
    bmc_keys = [
        ("key_partners",           "Key Partners"),
        ("key_activities",         "Key Activities"),
        ("key_resources",          "Key Resources"),
        ("value_propositions",     "Value Propositions"),
        ("customer_relationships", "Customer Relationships"),
        ("channels",               "Channels"),
        ("customer_segments",      "Customer Segments"),
        ("cost_structure",         "Cost Structure"),
        ("revenue_streams",        "Revenue Streams"),
    ]
    result = {k: "" for k, _ in bmc_keys}

    if "|" in text:
        for k, label in bmc_keys:
            m = re.compile(rf"{re.escape(label)}\s*:\s*([^|]+)", re.IGNORECASE).search(text)
            if m:
                result[k] = m.group(1).strip()
    else:
        for k, label in bmc_keys:
            m = re.compile(
                rf"{re.escape(label)}\s*:\s*(.+?)(?=(?:{'|'.join(l for _, l in bmc_keys)})|$)",
                re.IGNORECASE | re.DOTALL,
            ).search(text)
            if m:
                result[k] = m.group(1).strip()

    if not any(result.values()):
        result["value_propositions"] = text
    return result
