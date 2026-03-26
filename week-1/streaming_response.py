import os

from groq import Groq

client = Groq(api_key=os.environ.get("GROK_TOKEN"))
messages = [{
    "role": "system",
    "content": "You are a SRE engineer with 15 years of experience. You analyse incident, suggest root cause and "
               "provide remediation step in structure format only."
}]


def create_prompt_template(template_type, **kwargs):
    templates = {
        "incident_rca": """
                Analyze the following {component} incident.
                Error: {error}
                Environment: {environment}
                Provide structure RCA with fix steps.
            """,
        "pipeline_review": """
                Revieww this {pipeline_tool} pipeline configuration.
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


prompt = create_prompt_template(
    "incident_rca",
    component="AgroCD",
    error="Sync failed - Resource not found",
    environment="Production"
)

messages.append({
    "role": "user",
    "content": prompt
})

def stream_response(prompt):
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        # max_tokens=512,
        # temperature=0.1,
        stream=True
    )

    for chunk in stream:
        content = chunk.choices[0].delta.content

        if content:
            print(content, end="", flush=True)

stream_response("Write a detailed Kubernetes troubleshooting guide")