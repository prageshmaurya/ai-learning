import os

from langchain_classic import hub
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)

# Give AI tools to use. This is an agent's hands.
search_tool = DuckDuckGoSearchRun()
tools = [search_tool]


# Thought -> Action -> Observation -> Repeat
# prompt = PromptTemplate.from_template("""
# Answer the following questions using available tools.
#
# Tools available: {tools}
# Tool names: {tool_names}
#
# Format:
# Thought: think about what to do
# Action: tool_name
# Action input: input for tool
# Observation: tool result
# ... (repeat as needed)
# Final Answer: your answer
#
# Question: {input}
# {agent_scratchpad}
# """)

# ReAct prompt - standard agent thinking pattern
# This is a battle-tested prompt for agent reasoning
prompt = hub.pull("hwchase17/react")

agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True, # Shows thinking process
    max_iterations=5, # Prevent infinite loop
    handle_parsing_errors=True # Fixes most grok formatting issues
)

# Run it - Watch AI think step by step in terminal
result = executor.invoke({
    "input": "What are the latest best practices for Kubernetes security in 2026 and how to fix it?"
})

print("\n========Final Answer========")
print(result["output"])
