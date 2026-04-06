# RAG System (Most Important Week 2 Topic)
import os

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

# Your DevOps runbooks as Document
# In real use load it from .txt or .md files
runbook = [
    Document(page_content="""
        OOMKilled Resolution Runbook
        1. kubectl describe pod <pod_name> to check limits
        2. kubectl top pod <pod_name> to see actual usage
        3. Increase memory limit in deployment yaml
        4. Check for memory leaks in application logs
        5. Setup HPA for automatic scaling        
    """, metadata={"source": "OOMKilled-Runbook"}),

    Document(page_content="""
        CrashLoopBackOff Resolution Runbook
        1. kubectl logs pod <pod_name> --previous
        2. Check liveness probe configuration
        3. Verify environment variables are set correctly
        4. Check if dependent services are running
        5. Review resource limit - may be too restrictive
    """, metadata={"source": "CrashLoop-Runbook"}),

    Document(page_content="""
        Argocd sync failed runbook
        1. Check argocd app get <app_name> for sync status
        2. Verify git repository is accessible
        3. Check for YAML syntax error in manifests
        4. Make sure RBAC permissions are correct
        5. Hard refresh: argocd get app <app_name> --hard-refresh
    """, metadata={"source": "Argocd-Runbook"})
]

# Create embedding (run locally - no api needed)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Store in vector database
vectorstore = Chroma.from_documents(
    documents=runbook,
    embedding=embeddings,
)

retriever = vectorstore.as_retriever()

# LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN")
)

# RAG prompt
prompt = ChatPromptTemplate.from_template("""
You are a SRE assistant. Answer only using the provide runbooks.
If answer in not in runbook then say "No runbook found for this issue."

Runbook context:
{context}

Incident question: {question}

Provide step by step resolution.
""")

# RAG Chain
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Test it
print(rag_chain.invoke("My pod keep restarting, what should I check?"))
print("--------")
print(rag_chain.invoke("Argocd is not syncing my application."))
