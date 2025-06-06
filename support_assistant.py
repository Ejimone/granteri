from vapi import Vapi
import os
from dotenv import load_dotenv
load_dotenv()
client = Vapi(token=os.getenv("VAPI_TOKEN"))

"defining the system prompt"

system_prompt = """You are Alex, a customer service voice assistant for TechSolutions. Your primary purpose is to help customers resolve issues with their products, answer questions about services, and ensure a satisfying support experience.
- Sound friendly, patient, and knowledgeable without being condescending
- Use a conversational tone with natural speech patterns
- Speak with confidence but remain humble when you don't know something
- Demonstrate genuine concern for customer issues"""


def create_support_assistant():
    try:
        assistant = client.assistants.create(
            name="Customer Support Assistant",
            # Configure the AI model
            model={
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    }
                ],
            },
            # Configure the voice
            voice={
                "provider": "playht",
                "voice_id": "jennifer",
            },
            # Set the first message
            first_message="Hi there, this is Alex from OpenCode customer support. How can I help you today?",
        )
        
        print(f"Assistant created: {assistant.id}")
        return assistant
    except Exception as error:
        print(f"Error creating assistant: {error}")
        raise error
    




# Create the assistant
create_support_assistant()

