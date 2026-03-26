# Reusable prompt structures — 
# same concept as Helm templates but for AI

def create_devops_prompt(template_type, **kwargs):
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

#usage
prompt = create_devops_prompt(
    "incident_rca",
    component="ArgoCD",
    error="Sync failed - resource not found" ,
    environment="production"
)


if __name__ == "__main__":
    print(prompt)

