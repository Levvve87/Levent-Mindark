"""
Enkel chat-version som tar frågor som argument
Användning: python chat.py "Din fråga här"
"""

import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def chat_with_ai(question):
    """
    Chatta med AI baserat på en fråga
    """
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Fel: OPENAI_API_KEY miljövariabel saknas!")
        return

    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7
    )

    conversation_history = [{
        "role": "system",
        "content": "Du är en hjälpsam AI-assistent."
    }, {
        "role": "user",
        "content": question
    }]

    try:
        response = model.invoke(conversation_history)
        print(f"Fråga: {question}")
        print(f"Svar: {response.content}")
    except Exception as e:
        print(f"Fel: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        chat_with_ai(question)
    else:
        print("Användning: python chat.py 'Din fråga här'")
        print("Exempel: python chat.py 'Vad är Python?'")


