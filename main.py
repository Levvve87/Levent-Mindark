"""
LangChain ChatOpenAI Implementation
Använder .invoke() metod enligt LangChain dokumentation
"""

# Importera nödvändiga bibliotek
import os  # För att läsa miljövariabler från systemet
from dotenv import load_dotenv  # För att läsa .env filer
from langchain_openai import ChatOpenAI  # OpenAI integration för LangChain

def main():
    """
    Huvudfunktion som kör hela chat-programmet
    """
    # Ladda miljövariabler från .env fil
    # Detta läser in OPENAI_API_KEY från .env filen
    load_dotenv()
    
    # Kontrollera att API-nyckeln finns
    # os.getenv() läser miljövariabeln från systemet
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Om API-nyckeln saknas, visa felmeddelande och avsluta programmet
    if not api_key:
        print("Fel: OPENAI_API_KEY miljövariabel saknas!")
        print("Sätt den med: export OPENAI_API_KEY='din-nyckel-här'")
        return  # Avsluta funktionen tidigt
    
    # Initiera ChatOpenAI med gpt-4o-mini
    # Detta skapar en anslutning till OpenAI:s API
    model = ChatOpenAI(
        model="gpt-4o-mini",  # Kostnadseffektiv modell från OpenAI
        temperature=0.7  # Kreativitet (0.0 = mycket fokuserad, 1.0 = mycket kreativ)
    )
    
    # Interaktiv chat med OpenAI
    # while True skapar en oändlig loop som körs tills vi avslutar den
    while True:
        # Ta input från användaren
        # input() pausar programmet och väntar på att användaren skriver något
        message = input("Skriv din fråga (eller 'quit' för att avsluta): ")
        
        # Kontrollera om användaren vill avsluta
        # .lower() gör texten till små bokstäver så "QUIT" också fungerar
        if message.lower() == 'quit':
            print("Hej då!")
            break  # Avsluta while-loopen och gå vidare i programmet
            
        # Visa användarens meddelande
        print("Användare:", message)
        print("Assistent:", end=" ")  # end=" " gör att nästa print kommer på samma rad
        
        # Försök att skicka meddelandet till OpenAI
        try:
            # Anropa modellen med .invoke() - detta är kärnan i uppgiften
            # model.invoke() skickar meddelandet till OpenAI och får tillbaka ett svar
            response = model.invoke(message)
            print(response.content)  # .content innehåller AI:ns svar som text
            
        # Om något går fel, visa felmeddelande
        except Exception as e:
            print(f"Fel vid anrop till OpenAI: {e}")
            print("Kontrollera att din API-nyckel är korrekt och att du har internetanslutning.")

# Detta säger åt Python att köra main() funktionen när filen körs direkt
# Om filen importeras som en modul kommer denna kod inte att köras
if __name__ == "__main__":
    main()  # Anropa main() funktionen för att starta programmet