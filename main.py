"""
LangChain ChatOpenAI Implementation
Använder .invoke() metod enligt LangChain dokumentation
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def main():
    """
    Huvudfunktion som kör hela chat-programmet
    """
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Fel: OPENAI_API_KEY miljövariabel saknas!")
        print("Sätt den med: export OPENAI_API_KEY='din-nyckel-här'")
        return

    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7
    )

    conversation_history = []
    conversation_history.append({
        "role": "system",
        "content": "Kom ihåg hela konversationen och referera tillbaka till tidigare frågor och svar."
    })

    while True:
        message = input("Skriv din fråga (eller 'quit' för att avsluta): ")

        if message.lower() == 'quit':
            print("Hej då!")
            break

        conversation_history.append({
            "role": "user",
            "content": message
        })

        print("Användare:", message)
        print("Assistent:", end=" ")

        try:
            response = model.invoke(conversation_history)
            conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            print(response.content)

        except Exception as e:
            print(f"Fel vid anrop till OpenAI: {e}")
            print("Kontrollera att din API-nyckel är korrekt och att du har internetanslutning.")

if __name__ == "__main__":
    main()