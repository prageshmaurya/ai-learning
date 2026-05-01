import os

from langchain_classic import hub
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)


@tool
def get_incident_history(service_name: str) -> str:
    """
    Get past incident history for a service.
    Use to identify recurring patterns.
    Input: service name
    """
    return """
    Past incidents for payment-service (last 30 days):
    - Apr 01: OOMKilled - fixed by increasing memory limit
    - Mar 28: OOMKilled - fixed by increasing memory limit
    - Mar 15: OOMKilled - fixed by increasing memory limit
    Pattern: OOMKilled occurring every ~7 days
    Root pattern: Memory leak suspected, temporary fix applied each time
    """


tools = [get_incident_history]

# Agent with memory — tracks conversation across multiple invocations
prompt = hub.pull("hwchase17/react-chat")  # Chat version supports memory

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Session memory store
store = {}


def get_session(session_id):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


agent_with_memory = RunnableWithMessageHistory(
    executor,
    get_session,
    input_messages_key="input",
    history_messages_key="chat_history"
)

session = {"configurable": {"session_id": "oncall-shift-1"}}

# Multi-turn investigation
r1 = agent_with_memory.invoke(
    {"input": "payment-service is OOMKilled again. Check history."},
    config=session
)
print(r1["output"])

r2 = agent_with_memory.invoke(
    {"input": "Based on the pattern you found, what permanent fix should we implement?"},
    config=session
)
print(r2["output"])
# Agent remembers the history from r1 — no need to repeat context
