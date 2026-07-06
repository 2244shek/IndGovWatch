"""
The agentic core. Three specialist agents run in sequence as a LangGraph graph
(not a single prompt) so each step is independently inspectable, loggable, and
replaceable. Every step's input/output is persisted to AgentRun for audit —
this is the "immutable logging" / traceability piece that real regulatory-AI
governance frameworks require.
"""
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.agents.llm import call_llm
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
    trace: list  # accumulates {agent, input, output} for audit logging


def _safe_json(text: str, fallback: dict) -> dict:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return fallback


def triage_node(state: RegState) -> RegState:
    prompt = f"""Classify this Indian government notification/press release.
Title: {state['title']}
Text: {state['raw_text'][:2000]}

Respond ONLY with JSON: {{"domain": "<one of: banking & finance, taxation, agriculture, defence, healthcare, education, infrastructure, digital & IT, environment, foreign affairs, other>", "urgency": "<low|medium|high>", "urgency_score": <0.0-1.0>}}"""
    raw = call_llm(prompt)
    parsed = _safe_json(raw, {"domain": "other", "urgency": "low", "urgency_score": 0.3})
    state["domain"] = parsed.get("domain", "other")
    state["urgency"] = parsed.get("urgency", "low")
    state["urgency_score"] = float(parsed.get("urgency_score", 0.3))
    state["trace"].append({"agent": "triage", "input": prompt, "output": raw})
    return state


def impact_node(state: RegState) -> RegState:
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
    state["impact_analysis"] = raw.strip()
    state["trace"].append({"agent": "impact_analyst", "input": prompt, "output": raw})
    return state


def summarizer_node(state: RegState) -> RegState:
    prompt = f"""Write a plain-English, 2-sentence executive summary of this Indian government
notification, suitable for a policy-tracking dashboard alert. No legal/bureaucratic jargon.

Title: {state['title']}
Domain: {state['domain']}
Impact analysis: {state['impact_analysis']}"""
    raw = call_llm(prompt)
    state["summary"] = raw.strip()
    state["trace"].append({"agent": "summarizer", "input": prompt, "output": raw})
    return state


def build_graph():
    graph = StateGraph(RegState)
    graph.add_node("triage", triage_node)
    graph.add_node("impact_analyst", impact_node)
    graph.add_node("summarizer", summarizer_node)
    graph.set_entry_point("triage")
    graph.add_edge("triage", "impact_analyst")
    graph.add_edge("impact_analyst", "summarizer")
    graph.add_edge("summarizer", END)
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
        "trace": [],
    }
    return _compiled_graph.invoke(initial)
