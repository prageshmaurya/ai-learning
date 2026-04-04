import os
from typing import Optional

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_groq import ChatGroq




llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.environ.get("GROK_TOKEN"))

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a travel guide who knows places near to Bengaluru very well."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

chain = prompt | llm

# Memory store
store = {}

def get_session_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Chain with memory
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# same session_id = remember conversation
config = {"configurable": {"session_id": "sre_session_1"}}

r1 = chain_with_memory.invoke({"input": "My pod is OOMKilled"}, config=config)
r2 = chain_with_memory.invoke({"input": "What memory limit should I set"}, config=config)

print(r1.content)
print(r2.content) # Knows context from r1
