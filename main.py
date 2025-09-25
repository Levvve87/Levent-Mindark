"""
LangChain ChatOpenAI Implementation
Använder .invoke() metod enligt LangChain dokumentation
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def main():
    # Ladda miljövariabler från .env fil
    load_dotenv()
    
    # Kontrollera att API-nyckeln finns
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Fel: OPENAI_API_KEY miljövariabel saknas!")
        print("Sätt den med: export OPENAI_API_KEY='din-nyckel-här'")
        return
    
    # Initiera ChatOpenAI med gpt-4o-mini (vald från OpenAI:s modellöversikt)
    model = ChatOpenAI(
        model="gpt-4o-mini",  # Kostnadseffektiv modell från OpenAI:s officiella översikt
        temperature=0.7
    )
    
    # Använd .invoke() metod enligt LangChain Runnable dokumentation
    message = "Hej! Kan du berätta en kort vits på svenska?"
    
    print("Användare:", message)
    print("Assistent:", end=" ")
    
    try:
        # Anropa modellen med .invoke() - detta är kärnan i uppgiften
        response = model.invoke(message)
        print(response.content)
        
    except Exception as e:
        print(f"Fel vid anrop till OpenAI: {e}")
        print("Kontrollera att din API-nyckel är korrekt och att du har internetanslutning.")

if __name__ == "__main__":
    main()