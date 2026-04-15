import json
import os

from langchain_classic import hub
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_groq import ChatGroq


# Define custom tools
# @tools decorator change any python method into agent tool
# Docstring is CRITICAL - agent read it to decide when to use the tool.

@tool
def get_pod_status(namespace: str) -> str:
    """
    Get the status of all pods running in the cluster.
    Use this to find out pod health status or find failing pods.
    Input: namespace name (e.g. production, staging, development)
    """
    # Simulated kubectl output - replaces later with real subprocess later
    pods = {
        "production": [
            {"name": "payment-service-7d9f8b", "status": "OOMKilled", "restarts": 7},
            {"name": "auth-service-9f8d7c", "status": "Running", "restarts": 0},
            {"name": "api-gateway-6e7f8a", "status": "Running", "restarts": 0},
            {"name": "notification-svc-3k9m", "status": "CrashLoopBackOff", "restarts": 12}
        ],
        "staging": [
            {"name": "payment-service-staging", "status": "Running", "restarts": 0}
        ]
    }

    result = pods.get(namespace, [{"error": f"Namespace {namespace} not found"}])
    return json.dumps(result, indent=2)

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


# BUILD AGENT WITH CUSTOM TOOLS
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)

tools = [get_pod_status, get_pod_logs, get_resource_metrics, check_related_services]

prompt = hub.pull("hwchase17/react")

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=8,
    handle_parsing_errors=True
)

result = executor.invoke({
    "input": """
        I am the on-call engineer. Production namespace has issues.
        Please investigate all problems, find root causes,
        and give me a prioritized list of what to fix first.
    """
})

print("\n=== INCIDENT REPORT ===")
print(result["output"])
