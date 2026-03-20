import os

from groq import Groq


def create_devops_prompt(template_type, **kwargs):
    templates = {
        "incident_rca": """
            Analyze the following {component} incident.
            Error: {error}
            Environment: {environment}
            Provide structure RCA with fix steps.
        """,
        "pipeline_review": """
            Review this {pipeline_tool} pipeline configuration.
            Config: {config}
            Check for: security issues, performance problem,
            best practice voilation.
        """,
        "runbook_generator": """
            Create a runbook for: {task}
            Technology stack: {stack}
            Format: Step by step with commands.
        """
    }

    return templates[template_type].format(**kwargs)


# usage
prompt = create_devops_prompt(
    "incident_rca",
    component="ArgoCD",
    error="Sync failed - resource not found",
    environment="production"
)

client = Groq(api_key=os.environ.get("GROK_TOKEN"))

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": """You are a Senior SRE engineer assistant.
                 You analyze incidents, suggest root causes, and provide
                 remediation steps in structured format only.
            """
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.1,
    model="llama-3.3-70b-versatile",
    max_tokens=512
)

print(response.choices[0].message.content)
