import os

from langchain.tools import ToolException, tool
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_groq import ChatGroq
from langchain_classic import hub

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

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)

tools = [check_jenkins_pipeline, check_sonarqube_report, check_argocd_sync]
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True,  # Handles LLM formatting errors
    return_intermediate_steps=True  # Returns full reasoning chain
)

result = executor.invoke({
    "input": """
        Our payment-service deployment pipeline is broken.
        Check Jenkins pipeline 'payment-service-deploy',
        SonarQube project 'payment-service',
        and ArgoCD app 'payment-service-prod'.
        Give me a full pipeline health report and what to fix first.
    """
})

print("\n=== PIPELINE HEALTH REPORT ===")
print(result["output"])

# This shows every step agent took — useful for debugging
print("\n=== AGENT REASONING STEPS ===")
for step in result["intermediate_steps"]:
    print(f"Tool used: {step[0].tool}")
    print(f"Tool input: {step[0].tool_input}")
    print("---")
