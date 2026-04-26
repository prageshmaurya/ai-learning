import json
import os

from langchain_classic import hub
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.tools import tool, ToolException
from langchain_groq import ChatGroq

# ---- BUILD RAG SYSTEM ----
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


@tool
def check_jenkins_pipeline(pipeline_name: str) -> str:
    """
    Check the status of a Jenkins pipeline.
    Use when investigating CI/CD failures.
    Input: pipeline name
    """
    # Simulate occasional failures like real APIs
    import random
    if random.random() < 0.3:  # 30% chance of failure
        raise ToolException(f"Jenkins API timeout for pipeline: {pipeline_name}")

    return f"""
    Pipeline: {pipeline_name}
    Status: FAILED
    Stage failed: Integration Tests
    Duration: 4m 32s
    Failure reason: Connection timeout to test database
    Last successful build: 2 hours ago
    """


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
def check_sonarqube_report(project_key: str) -> str:
    """
    Get SonarQube code quality report for a project.
    Use when checking code quality gate status.
    Input: SonarQube project key
    """
    return f"""
    Project: {project_key}
    Quality Gate: FAILED
    Issues found:
    - Critical bugs: 2
    - Security vulnerabilities: 1 (SQL injection risk)
    - Code coverage: 61% (threshold: 80%)
    - Code smells: 47
    Recommendation: Fix critical bugs and security issue before merge
    """


@tool
def check_argocd_sync(app_name: str) -> str:
    """
    Check ArgoCD application sync status.
    Use when deployment is not reflecting latest changes.
    Input: ArgoCD application name
    """
    return f"""
    Application: {app_name}
    Sync Status: OutOfSync
    Health: Degraded
    Last sync: 3 hours ago
    Reason: Resource 'payment-configmap' not found in cluster
    Git revision: a3f8c92
    Target revision: HEAD
    """


@tool
def get_pod_status(namespace: str) -> str:
    """Get pod status in a Kubernetes namespace"""
    import json
    return json.dumps([
        {"name": "payment-service-7d9f8b", "status": "OOMKilled", "restarts": 7},
        {"name": "notification-svc-3k9m", "status": "CrashLoopBackOff", "restarts": 12}
    ], indent=2)


@tool
def check_related_services(service_name: str) -> str:
    """
    Check if services that this service depends on are healthy.
    Use this to identify cascading failures or dependency issues.
    Input: service name (e.g., 'payment-service')
    """
    dependencies = {
        "payment-service": {
            "database": "healthy",
            "redis-cache": "healthy",
            "fraud-detection-api": "degraded - high latency 800ms",
            "kafka": "healthy"
        },
        "notification-svc": {
            "kafka": "unreachable",
            "email-provider": "healthy",
            "sms-gateway": "healthy"
        }
    }
    name = service_name.replace("-7d9f8b", "").replace("-3k9m", "")
    return json.dumps(
        dependencies.get(name, {"error": "Service not found"}),
        indent=2
    )


@tool
def get_pod_logs(pod_name: str) -> str:
    """
    Fetch recent error logs from a specific pod.
    Use this when you need to investigate why a pod is failing.
    Input: pod name (e.g., 'payment-service-7d9f8b')
    """
    logs = {
        "payment-service-7d9f8b": """
            ERROR 2025-04-09 02:31:14 - java.lang.OutOfMemoryError: Java heap space
            ERROR 2025-04-09 02:31:14 - Container memory usage: 890Mi / 512Mi limit
            WARN  2025-04-09 02:28:01 - Memory usage crossed 80% threshold
            INFO  2025-04-09 02:15:00 - Transaction volume spike detected: +340%
            INFO  2025-04-09 02:00:00 - Service started successfully
        """,
        "notification-svc-3k9m": """
            ERROR 2025-04-09 02:30:55 - Connection refused: kafka:9092
            ERROR 2025-04-09 02:30:45 - Failed to connect to Kafka broker after 3 retries
            ERROR 2025-04-09 02:30:35 - KAFKA_BROKER_URL environment variable not set
            WARN  2025-04-09 02:30:30 - Starting without message queue connection
        """
    }
    return logs.get(pod_name, f"No logs found for pod: {pod_name}")


@tool
def get_resource_metrics(pod_name: str) -> str:
    """
    Get CPU and memory resource usage for a specific pod.
    Use this to understand resource consumption patterns.
    Input: pod name
    """
    metrics = {
        "payment-service-7d9f8b": {
            "cpu_usage": "450m",
            "cpu_limit": "500m",
            "memory_usage": "890Mi",
            "memory_limit": "512Mi",
            "memory_percentage": "174%",
            "trend": "increasing"
        }
    }
    return json.dumps(
        metrics.get(pod_name, {"error": "Metrics not available"}),
        indent=2
    )


@tool
def respond_in_severity_and_plan() -> str:
    """
    You are an SRE incident analyzer.
    Always respond in this exact JSON format only.
    No extra text, no Markdown, pure JSON:
    {
        "severity": "P1/P2/P3/P4",
        "root_cause": "string",
        "affected_components": ["list"],
        "immediate_actions": ["list"],
        "estimated_resolution_time": "string"
    }
    """

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)

tools = [
    get_pod_status,
    search_runbooks,
    check_jenkins_pipeline,
    check_sonarqube_report,
    check_argocd_sync,
    check_related_services,
    get_pod_logs,
    get_resource_metrics,
    respond_in_severity_and_plan
]

prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(
    agent=agent,
    max_iterations=8,
    handle_parsing_errors=True,
    tools=tools,
    verbose=True,
    return_intermediate_steps=True
)

alert_message = """
    Production has failing pods.
    Check the namespace, identify issues,
    search the runbooks and give me
    exact commands to fix each problem.
"""

result = executor.invoke({
    "input": f"ALERT: {alert_message}. Investigate and resolve."
})

print("#========== Severity and Resolution Plan ==========#")
print(result["output"])


