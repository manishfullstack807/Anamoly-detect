from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import settings
from agent.memory import memory
from datetime import datetime
from agent.tools import load_csv_files, log_decision

class AgentState(TypedDict):
    csv_data: str
    anomalies: str
    past_skills: list
    reasoning: str
    action: str


def get_llm(api_key: str = None, model: str = None):
    return ChatNVIDIA(
        model=model or "meta/llama-3.1-8b-instruct",
        api_key=api_key or settings.nvidia_api_key,
        temperature=0.1
    )


def build_agent(api_key: str = None, model: str = None):
    llm = get_llm(api_key, model)

    def load_data(state: AgentState) -> AgentState:
        data = load_csv_files()
        return {**state, "csv_data": data}

    def analyze(state: AgentState) -> AgentState:
        response = llm.invoke([
            SystemMessage(content="You are a supply chain analyst. Find anomalies in the data provided. List each anomaly clearly and briefly."),
            HumanMessage(content=f"Here is the supply chain data:\n\n{state['csv_data']}")
        ])
        return {**state, "anomalies": response.content}

    def recall(state: AgentState) -> AgentState:
        past = memory.recall(state["anomalies"])
        return {**state, "past_skills": past}

    def reason(state: AgentState) -> AgentState:
        past_text = "\n".join(state["past_skills"]) if state["past_skills"] else "No past decisions found."
        response = llm.invoke([
            SystemMessage(content="You are an autonomous supply chain agent. Think step by step and decide what action to take."),
            HumanMessage(content=f"""
ANOMALIES DETECTED:
{state['anomalies']}

PAST SIMILAR DECISIONS:
{past_text}

Think step by step:
1. What is the root cause?
2. How severe is this?
3. What action should be taken?
4. Final decision:
""")
        ])
        return {**state, "reasoning": response.content}

    def act(state: AgentState) -> AgentState:
        action_summary = state["reasoning"][-500:]
        log_decision(
            anomaly=state["anomalies"],
            reasoning=state["reasoning"],
            action=action_summary
        )
        memory.store(
            anomaly=state["anomalies"],
            reasoning=state["reasoning"],
            action=action_summary
        )
        return {**state, "action": action_summary}

    g = StateGraph(AgentState)
    g.add_node("load_data", load_data)
    g.add_node("analyze", analyze)
    g.add_node("recall", recall)
    g.add_node("reason", reason)
    g.add_node("act", act)
    g.set_entry_point("load_data")
    g.add_edge("load_data", "analyze")
    g.add_edge("analyze", "recall")
    g.add_edge("recall", "reason")
    g.add_edge("reason", "act")
    g.add_edge("act", END)
    return g.compile()


def run_agent(api_key: str = None, model: str = None):
    print(f"\n[AGENT] Running at {datetime.utcnow().isoformat()}")
    agent = build_agent(api_key, model)
    result = agent.invoke({
        "csv_data": "",
        "anomalies": "",
        "past_skills": [],
        "reasoning": "",
        "action": ""
    })
    print(f"[AGENT] Action taken: {result['action'][:200]}")
    return result


if __name__ == "__main__":
    from datetime import datetime
    from apscheduler.schedulers.blocking import BlockingScheduler

    run_agent()

    scheduler = BlockingScheduler()
    scheduler.add_job(run_agent, "interval", minutes=settings.monitor_interval_minutes)
    print(f"\n[AGENT] Scheduled every {settings.monitor_interval_minutes} minutes. Press Ctrl+C to stop.")
    scheduler.start()
