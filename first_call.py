import os
from groq import Groq
from dotenv import load_dotenv

# Load your API key from .env file
load_dotenv()

# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROK_TOKEN")
)

# Make your first API call
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful DevOps assistant."
        },
        {
            "role": "user",
            "content": "Explain Kubernetes in 5 simple lines."
        }
    ],
    model="llama-3.3-70b-versatile",  # Best free model on Groq
)

# Print the response
print(chat_completion.choices[0].message.content)