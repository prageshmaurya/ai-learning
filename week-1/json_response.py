import json
from groq import Groq
import os


client = Groq(api_key=os.environ.get("GROK_TOKEN"))

def analyze_incident(log_input):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an SRE incident analyzer.
                Always respond in this exact JSON format only.
                No extra text, no markdown, pure JSON:
                {
                    "severity": "P1/P2/P3/P4",
                    "root_cause": "string",
                    "affected_components": ["list"],
                    "immediate_actions": ["list"],
                    "estimated_resolution_time": "string"
                }"""
            },
            {
                "role": "user",
                "content": f"Analyze this incident log: {log_input}"
            }
        ],
        temperature=0.1  # Low temperature for consistent JSON
    )
    
    raw = response.choices[0].message.content
    
    # Parse and return clean JSON
    return json.loads(raw)

# Test with a real scenario you've faced
result = analyze_incident("""
    ERROR: OOMKilled - Container exceeded memory limit
    Pod: payment-service-7d9f8b-xkp2m
    Namespace: production
    Memory limit: 512Mi
    Actual usage: 890Mi
""")

print(json.dumps(result, indent=2))