import os
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from groq import InternalServerError, RateLimitError

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# =========================
# 🛠️ Helper: API Key Manager & Concurrency Control
# =========================

# Using the plural key from merged .env
GROQ_KEYS = os.getenv("GROQ_API_KEYS", os.getenv("GROQ_API_KEY", "")).split(",")
GROQ_KEYS = [k.strip() for k in GROQ_KEYS if k.strip()]

# Global Semaphore to limit concurrent AI calls
AI_SEMAPHORE = asyncio.Semaphore(5)

class APIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def get_key(self):
        if not self.keys:
            return os.getenv("GROQ_API_KEY") # Fallback to singular
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

key_manager = APIKeyManager(GROQ_KEYS)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, InternalServerError, Exception))
)
async def invoke_llm_with_retry(chain_or_llm, inputs):
    async with AI_SEMAPHORE:
        current_key = key_manager.get_key()
        temp_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=4096,
            groq_api_key=current_key
        )
        return await chain_or_llm.ainvoke(inputs)

def get_chat_model():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_tokens=4096,
        groq_api_key=key_manager.get_key()
    )

# =========================
# Web Search Tool
# =========================
search_tool = TavilySearch(max_results=10)

# =========================
# State Definition
# =========================
class AgentState(TypedDict):
    query: str
    research_check: str 
    search_results: str
    analysis: str
    report: str
    suggestions: List[str]
    revision_number: int
    reviewer_feedback: str
    history: List[str]
    is_relevant: bool

# =========================
# Nodes Implementation
# =========================

gatekeeper_prompt = PromptTemplate.from_template(
    """
    You are a Gatekeeper for an Energy Research Assistant.
    Determine if the query is related to the Energy Industry (renewables, grid, policy, sustainability, etc.).
    Query: {query}
    Reply ONLY "YES" or "NO".
    """
)

async def gatekeeper_node(state: AgentState):
    query = state["query"]
    chain = gatekeeper_prompt | get_chat_model() | StrOutputParser()
    try:
        result = await invoke_llm_with_retry(chain, {"query": query})
        result = result.strip().upper()
    except:
        result = "YES" # Fail open
    
    if "YES" in result:
        return {"is_relevant": True}
    else:
        return {
            "is_relevant": False, 
            "report": "I specialize in the Energy industry. Please ask a question related to energy or sustainability.",
            "suggestions": []
        }

research_prompt = PromptTemplate.from_template(
    """
    You are an Energy Industry Researcher.
    Topic: {query}
    Web Results: {search_results}
    History: {history}
    Extract 5-8 most critical, data-rich bullet points that directly address the topic.
    """
)

async def research_node(state: AgentState):
    query = state["query"]
    history = state.get("history", [])
    history_text = "\n".join(history[-3:]) if history else "No context."
    
    results = search_tool.run(query)
    chain = research_prompt | get_chat_model() | StrOutputParser()
    summary = await invoke_llm_with_retry(chain, {
        "query": query,
        "search_results": results,
        "history": history_text
    })
    
    return {
        "search_results": results, 
        "research_check": summary,
        "revision_number": 0,
        "reviewer_feedback": ""
    }

analysis_prompt = PromptTemplate.from_template(
    """
    Analyze the following energy research. Summarize the key findings, potential ROI, and critical risks in a concise manner.
    Research: {research}
    """
)

async def analysis_node(state: AgentState):
    research_summary = state["research_check"]
    chain = analysis_prompt | get_chat_model() | StrOutputParser()
    analysis = await invoke_llm_with_retry(chain, {"research": research_summary})
    return {"analysis": analysis}

writing_prompt = PromptTemplate.from_template(
    """
    Based on the following analysis, provide a VERY CONCISE, professional response (max 300 words) 
    that directly answers the user's initial query. 
    Avoid long structural sections like Executive Summary or SWOT unless explicitly asked.
    Focus on a direct, data-driven answer.
    Analysis: {analysis}
    Feedback: {feedback}
    """
)

async def writing_node(state: AgentState):
    analysis_text = state["analysis"]
    feedback = state.get("reviewer_feedback", "")
    current_rev = state.get("revision_number", 0)
    
    chain = writing_prompt | get_chat_model() | StrOutputParser()
    report = await invoke_llm_with_retry(chain, {
        "analysis": analysis_text,
        "feedback": feedback
    })
    return {"report": report, "revision_number": current_rev + 1}

reviewer_prompt = PromptTemplate.from_template(
    """
    Review this energy report. Is it detailed and accurate?
    Report: {report}
    Reply ONLY "PASS" or "FAIL: <feedback>".
    """
)

async def reviewer_node(state: AgentState):
    report_text = state["report"]
    chain = reviewer_prompt | get_chat_model() | StrOutputParser()
    try:
        result = await invoke_llm_with_retry(chain, {"report": report_text})
    except:
        result = "PASS"
    
    if "FAIL" in result:
        return {"reviewer_feedback": result.replace("FAIL:", "").strip()}
    return {"reviewer_feedback": "PASS"}

suggestions_prompt = PromptTemplate.from_template(
    """ Generate 3 short follow-up questions from this report. Return ONLY questions.
    Report: {report}
    """
)

async def suggestions_node(state: AgentState):
    report_text = state["report"]
    query = state["query"]
    chain = suggestions_prompt | get_chat_model() | StrOutputParser()
    result = await invoke_llm_with_retry(chain, {"report": report_text})
    questions = [q.strip() for q in result.strip().split('\n') if q.strip()]
    
    current_history = state.get("history", [])
    new_entry = f"User: {query}\nAI Report Summary: {report_text[:200]}..." 
    return {"suggestions": questions[:3], "history": current_history + [new_entry]}

# =========================
# 🚀 Graph Orchestration
# =========================

def should_continue(state: AgentState):
    if state.get("reviewer_feedback") == "PASS" or state.get("revision_number", 0) >= 3:
        return "suggester"
    return "writer" 

def check_relevance(state: AgentState):
    return "researcher" if state["is_relevant"] else END

workflow = StateGraph(AgentState)
workflow.add_node("gatekeeper", gatekeeper_node)
workflow.add_node("researcher", research_node)
workflow.add_node("analyst", analysis_node)
workflow.add_node("writer", writing_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("suggester", suggestions_node)

workflow.set_entry_point("gatekeeper")
workflow.add_conditional_edges("gatekeeper", check_relevance, {"researcher": "researcher", END: END})
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "writer")
workflow.add_edge("writer", "reviewer")
workflow.add_conditional_edges("reviewer", should_continue, {"suggester": "suggester", "writer": "writer"})
workflow.add_edge("suggester", END)

app = workflow.compile(checkpointer=MemorySaver())

async def run_full_research(query: str, thread_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = await app.ainvoke({"query": query}, config=config)
    return {
        "report": result.get("report", "No report generated."),
        "suggestions": result.get("suggestions", [])
    }
