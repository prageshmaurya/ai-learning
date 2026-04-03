import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
)

# Prompt template cleaner than raw strings
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a DevOps expert assistant."),
    ("user", "{input}")
])

# Chain - pipe operator connect component.
# This is LangChain's core concept.
chain = prompt | llm | StrOutputParser()

# Invoke
response = chain.invoke({"input": "Explain GitOps in five lines."})
print(response)
