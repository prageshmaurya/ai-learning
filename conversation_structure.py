from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROK_TOKEN"))

# Conversation history — this is how AI remembers context
messages = [
    {
        "role": "system",
        "content": """You are a Senior SRE engineer assistant.
        You analyze incidents, suggest root causes, and provide
        remediation steps in structured format only."""
    }
]

def chat(user_input):
    # Append user message to history
    messages.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.5,  # experiment with 0.1 to 1.0
        max_tokens=512
    )
    
    assistant_message = response.choices[0].message.content
    
    # Append AI response to maintain history
    messages.append({
        "role": "assistant", 
        "content": assistant_message
    })
    
    return assistant_message

# Test it
print("############################# reply - 1 #############################")
print(chat("My Kubernetes pod is in CrashLoopBackOff"))
print("############################# reply - 2 #############################")
print(chat("What logs should I check first?"))
print("############################# reply - 3 #############################")
print(chat("how are you?"))
# Notice it remembers context from previous message. But, context can be changed in same chat.