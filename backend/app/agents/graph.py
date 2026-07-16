"""
The agentic core. Three specialist agents run in sequence as a LangGraph graph
(not a single prompt) so each step is independently inspectable, loggable, and
replaceable. Every step's input/output is persisted to AgentRun for audit —
this is the "immutable logging" / traceability piece that real regulatory-AI
governance frameworks require.
"""
import json
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from app.agents.llm import call_llm, CITIZEN_IMPACT_SYSTEM_PROMPT, LAYMAN_EXPLAINER_SYSTEM_PROMPT
from app.vectorstore import query_similar


class RegState(TypedDict):
    title: str
    raw_text: str
    source: str
    url: str
    domain: str
    urgency: str
    urgency_score: float
    impact_analysis: str
    summary: str
    easy_view_headline: str
    easy_view_explanation: str
    trace: Annotated[list, operator.add]  # accumulates {agent, input, output} for audit logging


def _safe_json(text: str, fallback: dict) -> dict:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return fallback


def triage_node(state: RegState) -> dict:
    prompt = f"""Classify this Indian government notification/press release.
Title: {state['title']}
Text: {state['raw_text'][:2000]}

Respond ONLY with JSON: {{"domain": "<one of: banking & finance, taxation, agriculture, defence, healthcare, education, infrastructure, digital & IT, environment, foreign affairs, other>", "urgency": "<low|medium|high>", "urgency_score": <0.0-1.0>}}"""
    raw = call_llm(prompt)
    parsed = _safe_json(raw, {"domain": "other", "urgency": "low", "urgency_score": 0.3})
    return {
        "domain": parsed.get("domain", "other"),
        "urgency": parsed.get("urgency", "low"),
        "urgency_score": float(parsed.get("urgency_score", 0.3)),
        "trace": [{"agent": "triage", "input": prompt, "output": raw}]
    }


def impact_node(state: RegState) -> dict:
    # RAG: pull similar/prior documents from the vector store for context
    similar = query_similar(state["raw_text"][:1000], n_results=3)
    prior_titles = similar.get("documents", [[]])[0] if similar else []
    context = "\n".join(f"- {t[:200]}" for t in prior_titles) or "No closely related prior documents found."

    prompt = f"""Given this new Indian government notification and related prior items, explain in 3-4
sentences which citizens, businesses, or sectors are affected and what concretely changes for them.
Be specific, avoid boilerplate and avoid restating the title.

New document title: {state['title']}
New document text: {state['raw_text'][:2000]}

Related prior documents:
{context}"""
    raw = call_llm(prompt)
    return {
        "impact_analysis": raw.strip(),
        "trace": [{"agent": "impact_analyst", "input": prompt, "output": raw}]
    }


def summarizer_node(state: RegState) -> dict:
    prompt = f"""Write a plain-English, 2-sentence executive summary of this Indian government
notification, suitable for a policy-tracking dashboard alert. No legal/bureaucratic jargon.

Title: {state['title']}
Domain: {state['domain']}
Impact analysis: {state['impact_analysis']}"""
    raw = call_llm(prompt)
    return {
        "summary": raw.strip(),
        "trace": [{"agent": "summarizer", "input": prompt, "output": raw}]
    }


def citizen_impact_node(state: RegState) -> dict:
    prompt = f"""Explain the direct impact of this government notification/press release for the everyday citizen.
Title: {state['title']}
Text: {state['raw_text'][:2000]}"""
    raw = call_llm(prompt, system=CITIZEN_IMPACT_SYSTEM_PROMPT)
    return {
        "easy_view_explanation": raw.strip(),
        "trace": [{"agent": "citizen_impact_agent", "input": prompt, "output": raw}]
    }


def layman_explainer_node(state: RegState) -> dict:
    prompt = f"""Generate a single-sentence plain English headline for:
Title: {state['title']}
Text: {state['raw_text'][:2000]}"""
    raw = call_llm(prompt, system=LAYMAN_EXPLAINER_SYSTEM_PROMPT)
    return {
        "easy_view_headline": raw.strip(),
        "trace": [{"agent": "layman_explainer_agent", "input": prompt, "output": raw}]
    }


def join_node(state: RegState) -> dict:
    # Sync barrier node. It does not modify state but ensures all parallel branches have finished.
    return {"trace": []}


def build_graph():
    graph = StateGraph(RegState)
    graph.add_node("triage", triage_node)
    graph.add_node("impact_analyst", impact_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("citizen_impact_agent", citizen_impact_node)
    graph.add_node("layman_explainer_agent", layman_explainer_node)
    graph.add_node("join", join_node)
    
    graph.set_entry_point("triage")
    
    # Route to technical and public translation tracks in parallel
    graph.add_edge("triage", "impact_analyst")
    graph.add_edge("triage", "citizen_impact_agent")
    graph.add_edge("triage", "layman_explainer_agent")
    
    # Technical track pipeline
    graph.add_edge("impact_analyst", "summarizer")
    graph.add_edge("summarizer", "join")
    
    # Public translation track pipelines
    graph.add_edge("citizen_impact_agent", "join")
    graph.add_edge("layman_explainer_agent", "join")
    
    graph.add_edge("join", END)
    return graph.compile()


_compiled_graph = build_graph()


def run_pipeline(title: str, raw_text: str, source: str, url: str) -> RegState:
    initial: RegState = {
        "title": title,
        "raw_text": raw_text or title,
        "source": source,
        "url": url,
        "domain": "",
        "urgency": "",
        "urgency_score": 0.0,
        "impact_analysis": "",
        "summary": "",
        "easy_view_headline": "",
        "easy_view_explanation": "",
        "trace": [],
    }
    return _compiled_graph.invoke(initial)
