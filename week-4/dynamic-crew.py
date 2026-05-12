import os

from crewai import LLM, Agent, Task, Crew, Process

llm = LLM(
    model="groq/meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=os.getenv("GROK_TOKEN"),
    temperature=0.1
)

def create_incident_crew(incident_alert: str):
    """
    Factory function — creates a fresh crew for any incident.
    Reusable for any alert your monitoring system sends.
    """

    monitor = Agent(
        role="Senior SRE",
        goal="Analyze incident and provide complete resolution",
        backstory="""10 year SRE veteran who handles P1 incidents 
        daily. Methodical, calm, always finds the root cause.""",
        llm=llm,
        verbose=True
    )

    analyze_task = Task(
        description=f"""
            Analyze this production incident completely:

            {incident_alert}

            Provide:
            1. Severity (P1/P2/P3/P4)
            2. Root cause
            3. Business impact
            4. Immediate fix commands
            5. Prevention steps
            """,
        agent=monitor,
        expected_output="Complete incident analysis and resolution plan"
    )

    return Crew(
        agents=[monitor],
        tasks=[analyze_task],
        process=Process.sequential,
        verbose=False  # Clean output for production use
    )

# Simulate different alerts coming in
alerts = [
    """
    ALERT: api-gateway CrashLoopBackOff
    Namespace: production
    Restarts: 15 in 20 minutes
    Error: Connection timeout to auth-service
    Impact: All API requests failing
    """,
    """
    ALERT: Jenkins pipeline payment-service-deploy FAILED
    Stage: Integration Tests
    Error: Test database connection refused
    Branch: main
    Impact: Deployment blocked, release delayed
    """,
    """
    ALERT: ArgoCD sync failed for order-service-prod
    Error: ConfigMap order-config not found in cluster
    Last successful sync: 6 hours ago
    Impact: New features not deployed to production
    """
]

# Process each alert with its own crew
for i, alert in enumerate(alerts, 1):
    print(f"\n{'=' * 50}")
    print(f"PROCESSING ALERT {i}")
    print('=' * 50)

    crew = create_incident_crew(alert)
    result = crew.kickoff()
    print(result)