import os

from langchain_classic import hub
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_groq import ChatGroq

# ---- BUILD RAG SYSTEM (your Week 2 code) ----
# Add your REAL runbooks here as actual content
runbooks = [
    Document(page_content="""
        OOMKilled Complete Resolution Guide:
        Immediate actions:
        1. kubectl describe pod <name> -n <namespace>
        2. kubectl top pod <name> -n <namespace>
        3. Edit deployment: kubectl edit deployment <name>
        4. Increase memory limit to 2x current usage
        5. Add memory request = 50% of limit
        Long term:
        6. Enable HPA: kubectl autoscale deployment <name> --min=2 --max=10
        7. Profile application for memory leaks
        8. Set up memory alerts at 80% threshold in Grafana
    """, metadata={"source": "oomkilled", "severity": "P1"}),

    Document(page_content="""
        CrashLoopBackOff Resolution Guide:
        Immediate actions:
        1. kubectl logs <pod> --previous (get logs before crash)
        2. kubectl describe pod <pod> (check events section)
        3. Check liveness probe: is it too aggressive?
        4. Verify all environment variables exist
        5. Check if ConfigMap and Secrets are mounted correctly
        Common causes:
        - Missing environment variables
        - Wrong image tag
        - Insufficient resources
        - Application startup taking too long
    """, metadata={"source": "crashloopbackoff", "severity": "P2"}),

    Document(page_content="""
        Kafka Connection Issues Resolution:
        Immediate actions:
        1. kubectl exec -it <pod> -- env | grep KAFKA
        2. Verify KAFKA_BROKER_URL is set correctly
        3. Test connectivity: kubectl exec -it <pod> -- nc -zv kafka 9092
        4. Check Kafka pod status in kafka namespace
        5. Review network policies blocking port 9092
        If Kafka is down:
        6. kubectl get pods -n kafka
        7. kubectl logs kafka-0 -n kafka
        8. Check PVC status: kubectl get pvc -n kafka
    """, metadata={"source": "kafka-connection", "severity": "P2"})
]

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Chroma.from_documents(documents=runbooks, embedding=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

# ---- WRAP RAG AS A TOOL ----
@tool
def search_runbooks(query: str) -> str:
    """
    Search internal DevOps runbooks for resolution procedures.
    Use this when you need step-by-step fix instructions for any incident.
    Input: description of the problem (e.g., 'OOMKilled pod fix steps')
    """
    docs = retriever.invoke(input=query)
    if not docs:
        return "No runbook found for this issue."

    results = []
    for doc in docs:
        results.append(f"Source: {doc.metadata.get('source')}\n{doc.page_content}")

    return "\n\n---\n\n".join(results)


# ---- COMBINE WITH OTHER TOOLS ----
@tool
def get_pod_status(namespace: str) -> str:
    """Get pod status in a Kubernetes namespace"""
    import json
    return json.dumps([
        {"name": "payment-service-7d9f8b", "status": "OOMKilled", "restarts": 7},
        {"name": "notification-svc-3k9m", "status": "CrashLoopBackOff", "restarts": 12}
    ], indent=2)


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)

tools = [get_pod_status, search_runbooks]

prompt = hub.pull("hwchase17/react")

agent = create_react_agent(
    prompt=prompt,
    tools=tools,
    llm=llm
)

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=8,
    handle_parsing_errors=True
)

result = executor.invoke({
    "input": """
        Production has failing pods.
        Check the namespace, identify issues,
        search the runbooks and give me
        exact commands to fix each problem.
    """
})

print("\n=== RESOLUTION PLAN ===")
print(result["output"])
