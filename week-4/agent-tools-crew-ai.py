import json
import os

from crewai import LLM, Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.1,
    api_key=os.environ.get("GROK_TOKEN")
)

# ---- CrewAI Tools (different from LangChain tools) ----
# CrewAI has its own tool format using BaseTool

class PodStatusInput(BaseModel):
    namespace: str = Field(description="Kubernetes namespace to check")

class PodStatusTool(BaseTool):
    name: str = "get_pod_status"
    description: str = """Get status of all pods in a Kubernetes namespace.
    Use when you need to identify failing pods."""
    args_schema: type[BaseModel] = PodStatusInput

    def _run(self, namespace: str) -> str:
        pods = {
            "production": [
                {"name": "payment-service-7d9f8b",
                 "status": "OOMKilled", "restarts": 7},
                {"name": "auth-service-9f8d7c",
                 "status": "Running", "restarts": 0},
                {"name": "notification-svc-3k9m",
                 "status": "CrashLoopBackOff", "restarts": 12}
            ]
        }
        return json.dumps(pods.get(namespace, []), indent=2)

class PodLogsInput(BaseModel):
    pod_name: str = Field(description="Name of the pod to fetch logs from")

class PodLogsTool(BaseTool):
    name: str = "get_pod_logs"
    description: str = """Fetch error logs from a specific pod.
    Use to investigate why a pod is failing."""
    args_schema: type[BaseModel] = PodLogsInput

    def _run(self, pod_name: str) -> str:
        logs = {
            "payment-service-7d9f8b": """
                ERROR: java.lang.OutOfMemoryError: Java heap space
                ERROR: Memory usage 890Mi exceeds limit 512Mi
                WARN:  Transaction spike detected +340%
                INFO:  fraud-detection-api latency 800ms
            """,
            "notification-svc-3k9m": """
                ERROR: Connection refused kafka:9092
                ERROR: KAFKA_BROKER_URL not set
                WARN:  Starting without message queue
            """
        }
        return logs.get(pod_name, "No logs found")

class RunbookInput(BaseModel):
    error_type: str = Field(description="Type of error to search runbook for")

class RunbookTool(BaseTool):
    name: str = "search_runbook"
    description: str = """Search internal runbooks for resolution steps.
    Use to find exact commands to fix known issues."""
    args_schema: type[BaseModel] = RunbookInput

    def _run(self, error_type: str) -> str:
        runbooks = {
            "OOMKilled": """
                1. kubectl describe pod <name> -n production
                2. kubectl top pod <name> -n production  
                3. kubectl edit deployment <name> -n production
                4. Increase memory limit to 2Gi
                5. kubectl rollout status deployment/<name>
            """,
            "CrashLoopBackOff": """
                1. kubectl logs <pod> --previous -n production
                2. kubectl describe pod <pod> -n production
                3. Check env vars and configmaps
                4. Verify liveness probe settings
            """,
            "kafka": """
                1. kubectl get pods -n kafka
                2. kubectl exec -it <pod> -- env | grep KAFKA
                3. nc -zv kafka 9092
                4. Check network policies
            """
        }
        # Find best matching runbook
        for key in runbooks:
            if key.lower() in error_type.lower():
                return runbooks[key]
        return "No specific runbook found. Check general troubleshooting guide."

# ---- AGENTS WITH SPECIFIC TOOLS ----
# Monitor agent only needs pod status tool
monitor_agent = Agent(
    role="Infrastructure Monitor",
    goal="Detect all failing pods and classify the incident",
    backstory="""Senior SRE specializing in rapid incident detection.
    You check pod status systematically and never miss a failing service.""",
    tools=[PodStatusTool()],  # Only this tool
    llm=llm,
    verbose=True
)

# Diagnosis agent needs logs tool
diagnosis_agent = Agent(
    role="Root Cause Analyst",
    goal="Find root cause by analyzing pod logs deeply",
    backstory="""Systems detective who reads logs like a book.
    You always find the real cause hidden in the log output.""",
    tools=[PodLogsTool()],  # Only this tool
    llm=llm,
    verbose=True
)

# Resolution agent needs runbook tool
resolution_agent = Agent(
    role="Incident Resolver",
    goal="Find and execute the correct runbook for each issue",
    backstory="""Experienced DevOps engineer who knows every runbook.
    You always find the right procedure and present exact commands.""",
    tools=[RunbookTool()],  # Only this tool
    llm=llm,
    verbose=True
)

# Tasks
detect_task = Task(
    description="Check production namespace. List all failing pods with their issues.",
    agent=monitor_agent,
    expected_output="List of failing pods with status and restart counts"
)

diagnose_task = Task(
    description="""For each failing pod identified, fetch logs and determine
    the specific root cause of each failure.""",
    agent=diagnosis_agent,
    expected_output="Root cause for each failing pod with evidence from logs",
    context=[detect_task]
)

resolve_task = Task(
    description="""Search runbooks for each identified issue and compile
    a complete resolution plan with exact kubectl commands.""",
    agent=resolution_agent,
    expected_output="Step by step resolution commands for each failing service",
    context=[detect_task, diagnose_task]
)

crew = Crew(
    agents=[monitor_agent, diagnosis_agent, resolution_agent],
    tasks=[detect_task, diagnose_task, resolve_task],
    process=Process.sequential,
    verbose=True
)

result = crew.kickoff()
print("\n=== COMPLETE INCIDENT RESOLUTION ===")
print(result)
