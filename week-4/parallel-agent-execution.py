import os
import time

from crewai import LLM, Agent, Task, Crew, Process

llm = LLM(
    model="groq/meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)

# When investigating multiple independent services
# they can be analyzed IN PARALLEL — saves time

payment_investigator = Agent(
    role="Payment Service Specialist",
    goal="Investigate and resolve payment service issues only",
    backstory="""Expert in Java microservices and payment systems.
    Knows payment-service architecture inside out.""",
    llm=llm,
    verbose=True
)

notification_investigator = Agent(
    role="Notification Service Specialist",
    goal="Investigate and resolve notification service issues only",
    backstory="""Expert in event-driven systems and Kafka.
    Specializes in async messaging failures.""",
    llm=llm,
    verbose=True
)

report_compiler = Agent(
    role="Incident Commander",
    goal="Compile all findings into executive incident report",
    backstory="""Senior Engineering Manager who synthesizes 
    technical findings into clear action plans with priorities.""",
    llm=llm,
    verbose=True
)

# These two tasks run in PARALLEL
payment_task = Task(
    description="""
    Investigate payment-service-7d9f8b:
    - Status: OOMKilled, 7 restarts
    - Memory: 890Mi used vs 512Mi limit
    - Context: 340% transaction spike
    Provide RCA and fix steps.
    """,
    agent=payment_investigator,
    expected_output="Payment service RCA and resolution steps"
)

notification_task = Task(
    description="""
    Investigate notification-svc-3k9m:
    - Status: CrashLoopBackOff, 12 restarts
    - Error: KAFKA_BROKER_URL not set
    - Cannot connect to kafka:9092
    Provide RCA and fix steps.
    """,
    agent=notification_investigator,
    expected_output="Notification service RCA and resolution steps"
)

# This task waits for both above to complete
compile_task = Task(
    description="""
    Compile findings from both service investigations into:
    1. Executive summary (3 sentences max)
    2. Priority order of fixes (which to fix first and why)
    3. Combined timeline for full resolution
    4. Post-incident action items
    """,
    agent=report_compiler,
    expected_output="Executive incident report with priorities",
    context=[payment_task, notification_task]
)

# Process.hierarchical enables parallel execution
crew = Crew(
    agents=[payment_investigator, notification_investigator, report_compiler],
    tasks=[payment_task, notification_task, compile_task],
    process=Process.hierarchical,  # Parallel where possible
    manager_llm=llm,               # Required for hierarchical
    verbose=True
)

result = crew.kickoff()
print("\n=== EXECUTIVE INCIDENT REPORT ===")
print(result)
