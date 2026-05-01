import os

from crewai import Agent, Task, Crew, Process, LLM

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.environ.get("GROK_TOKEN"),
    temperature=0.1
)

# ---- AGENTS ----
# Each agent has a role, goal, and backstory.
# Backstory shapes HOW the agent thinks and responds

monitor_agent = Agent(
    role="Infrastructure Monitor",
    goal="Detect and classify infrastructure incidents with precision",
    backstory="""You are a Senior SRE with 10 years experience at 
    large scale systems. You have seen every type of incident and 
    can classify severity instantly. You are calm under pressure 
    and methodical in your analysis.""",
    llm=llm,
    verbose=True,
    allow_delegation=False  # This agent works alone, no sub-delegation
)

diagnosis_agent = Agent(
    role="Root Cause Analyst",
    goal="Identify the true root cause of incidents, not just symptoms",
    backstory="""You are a distributed systems expert who specializes 
    in finding root causes of complex failures. You never stop at the 
    surface symptom — you always ask why 5 times until you find 
    the real cause.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

resolution_agent = Agent(
    role="Incident Resolver",
    goal="Write clear, executable resolution plans anyone can follow",
    backstory="""You are a DevOps engineer who has resolved 2000+ 
    incidents. You write runbooks that junior engineers can follow 
    without any additional guidance. Every step has exact commands.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ---- TASKS ----
# Tasks define WHAT each agent must do
# context parameter chains tasks — output of one feeds the next

incident_data = """
ALERT: Production incident detected
Service: payment-service
Namespace: production
Error: OOMKilled - 7 restarts in 10 minutes
Memory limit: 512Mi | Actual usage: 890Mi
Transaction volume: 340% spike in last hour
Related: fraud-detection-api showing 800ms latency
Time: 02:31 IST
"""

detect_task = Task(
    description=f"""
    Analyze this incident alert and provide:
    1. Severity classification (P1/P2/P3/P4) with justification
    2. Affected components list
    3. Business impact assessment
    4. Initial hypothesis of what went wrong

    Incident data:
    {incident_data}
    """,
    agent=monitor_agent,
    expected_output="""
    Structured incident classification with:
    - Severity level and justification
    - Affected components
    - Business impact
    - Initial hypothesis
    """
)

diagnose_task = Task(
    description="""
    Based on the incident classification provided,
    perform deep root cause analysis:
    1. Identify the PRIMARY root cause (not just symptoms)
    2. Identify CONTRIBUTING factors
    3. Explain the failure cascade chain
    4. Assess if this is a recurring pattern
    5. Identify what monitoring gap allowed this to happen
    """,
    agent=diagnosis_agent,
    expected_output="""
    Complete RCA with:
    - Primary root cause
    - Contributing factors
    - Failure cascade explanation
    - Recurrence risk assessment
    - Monitoring gaps identified
    """,
    context=[detect_task]  # Gets monitor_agent output automatically
)

resolve_task = Task(
    description="""
    Based on the root cause analysis provided,
    create a complete resolution plan:
    1. IMMEDIATE actions (next 15 minutes) with exact commands
    2. SHORT TERM fixes (next 24 hours)
    3. LONG TERM prevention (next sprint)
    4. Rollback plan if fix makes things worse
    5. Verification steps to confirm fix worked
    """,
    agent=resolution_agent,
    expected_output="""
    Complete resolution plan with:
    - Immediate commands to run right now
    - Short term fixes with owners
    - Long term prevention tasks
    - Rollback procedure
    - Verification checklist
    """,
    context=[detect_task, diagnose_task]  # Gets both previous outputs
)

# ---- CREW ----
# Crew orchestrates agents and tasks

crew = Crew(
    agents=[monitor_agent, diagnosis_agent, resolution_agent],
    tasks=[detect_task, diagnose_task, resolve_task],
    process=Process.sequential,  # Tasks run in order
    verbose=True
)

# Kickoff — watch agents collaborate
result = crew.kickoff()

print("\n" + "="*50)
print("FINAL INCIDENT REPORT")
print("="*50)
print(result)
