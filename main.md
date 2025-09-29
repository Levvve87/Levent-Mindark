# LangChain ChatOpenAI Implementation - Detaljerad Förklaring

## Hela Koden

```python
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
```

## Detaljerad Förklaring av Koden

### 1. Docstring och Imports

```python
"""
LangChain ChatOpenAI Implementation
Använder .invoke() metod enligt LangChain dokumentation
"""
# """ = triple quotes som startar en docstring (dokumentationssträng)
# LangChain ChatOpenAI Implementation = beskrivning av vad programmet gör
# Använder .invoke() metod enligt LangChain dokumentation = teknisk beskrivning
# """ = triple quotes som avslutar docstring

import os  # För att läsa miljövariabler från systemet
# import = Python-nyckelord för att importera moduler
# os = modul för operativsystemsfunktioner
# # = kommentar som förklarar vad modulen gör
# För att läsa miljövariabler från systemet = förklaring av os-modulens funktion

from dotenv import load_dotenv  # För att läsa .env filer
# from = Python-nyckelord för att importera specifika funktioner från en modul
# dotenv = modulnamn (paket som läser .env filer)
# import = Python-nyckelord för att importera
# load_dotenv = funktionsnamn som vi importerar
# # = kommentar
# För att läsa .env filer = förklaring av load_dotenv-funktionens syfte

from langchain_openai import ChatOpenAI  # OpenAI integration för LangChain
# from = Python-nyckelord för att importera specifika funktioner
# langchain_openai = modulnamn (LangChain paket för OpenAI)
# import = Python-nyckelord för att importera
# ChatOpenAI = klassnamn som vi importerar
# # = kommentar
# OpenAI integration för LangChain = förklaring av ChatOpenAI-klassens syfte
```

### 2. Main-funktionen

```python
def main():
    """
    Huvudfunktion som kör hela chat-programmet
    """
    # def = Python-nyckelord för att definiera en funktion
    # main = funktionsnamn (kan heta vad som helst)
    # () = parenteser för funktionsparametrar (inga i detta fall)
    # : = kolon som säger "nu kommer funktionens kod"
    # """ = triple quotes som startar funktionens docstring
    # Huvudfunktion som kör hela chat-programmet = beskrivning av funktionen
    # """ = triple quotes som avslutar docstring
```

### 3. Miljövariabler och API-nyckel

```python
load_dotenv()
# load_dotenv = funktion som läser .env filen
# () = parenteser runt funktionen (inga parametrar behövs)
# Detta läser in OPENAI_API_KEY från .env filen = förklaring av vad som händer

api_key = os.getenv("OPENAI_API_KEY")
# api_key = variabelnamn som sparar API-nyckeln
# = = tilldelningsoperator (sparar värdet)
# os = modul för operativsystemsfunktioner
# . = punkt för att använda en metod från modulen
# getenv = metod som hämtar en miljövariabel
# () = parenteser runt metoden
# "OPENAI_API_KEY" = sträng med namnet på miljövariabeln vi vill ha
# os.getenv() läser miljövariabeln från systemet = förklaring av vad som händer

if not api_key:
    # if = Python-nyckelord för villkor
    # not = Python-nyckelord som inverterar (gör sant till falskt)
    # api_key = variabeln vi kontrollerar
    # : = kolon som säger "om villkoret är sant, kör koden nedan"
    print("Fel: OPENAI_API_KEY miljövariabel saknas!")
    # print() = funktion som skriver text
    # "Fel: OPENAI_API_KEY..." = sträng som skrivs ut
    # () = parenteser runt funktionen
    print("Sätt den med: export OPENAI_API_KEY='din-nyckel-här'")
    # print() = funktion som skriver text
    # "Sätt den med..." = sträng med instruktioner
    # () = parenteser runt funktionen
    return  # Avsluta funktionen tidigt
    # return = Python-nyckelord som avslutar funktionen
    # Avsluta funktionen tidigt = förklaring av vad return gör
```

### 4. AI-modell Setup

```python
model = ChatOpenAI(
    model="gpt-4o-mini",  # Kostnadseffektiv modell från OpenAI
    temperature=0.7  # Kreativitet (0.0 = mycket fokuserad, 1.0 = mycket kreativ)
)
# model = variabelnamn som sparar AI-modellen
# = = tilldelningsoperator
# ChatOpenAI = klass som skapar en AI-modell
# () = parenteser runt konstruktorn
# model = parameter som anger vilken AI-modell vi vill använda
# = = tilldelningsoperator för parametern
# "gpt-4o-mini" = sträng med modellnamnet
# , = komma som separerar parametrar
# temperature = parameter som styr kreativiteten
# = = tilldelningsoperator för parametern
# 0.7 = decimaltal som anger kreativitetsnivå
# Detta skapar en anslutning till OpenAI:s API = förklaring av vad som händer
```

### 5. Konversationshistorik

```python
conversation_history = []
# conversation_history = variabelnamn för listan
# = = tilldelningsoperator
# [] = tom lista (square brackets)
# Skapa en lista för att spara konversationshistorik = förklaring av syftet

conversation_history.append({
    "role": "system",
    "content": "Kom ihåg hela konversationen och referera tillbaka till tidigare frågor och svar."
})
# conversation_history = listan vi skapade ovan
# . = punkt för att använda en metod
# append() = metod som lägger till något i listan
# () = parenteser runt metoden
# { = startar en dictionary (nyckel-värde par)
# "role" = nyckel som anger vem som skrev meddelandet
# : = kolon som separerar nyckel och värde
# "system" = värde som anger att detta är ett systemmeddelande
# , = komma som separerar nyckel-värde par
# "content" = nyckel som anger innehållet i meddelandet
# : = kolon som separerar nyckel och värde
# "Kom ihåg hela konversationen..." = sträng med instruktioner till AI:n
# } = avslutar dictionary
# ) = avslutar append-funktionen
```

### 6. Huvudloop

```python
while True:
    # while = Python-nyckelord för loop
    # True = konstant som alltid är sant
    # : = kolon som säger "kör koden nedan så länge villkoret är sant"
    # while True skapar en oändlig loop som körs tills vi avslutar den

    message = input("Skriv din fråga (eller 'quit' för att avsluta): ")
    # input() pausar programmet och väntar på att användaren skriver något
    # message = variabelnamn som sparar vad användaren skriver
    # input() = funktion som pausar och väntar på användarinput
    # "Skriv din fråga..." = text som visas för användaren (sträng)
    # () = parenteser runt funktionen

    if message.lower() == 'quit':
        # if = Python-nyckelord för villkor
        # message = variabeln vi skapade ovan
        # . = punkt för att använda en metod på variabeln
        # lower() = metod som gör text till små bokstäver
        # () = parenteser runt metoden
        # == = jämförelseoperator (är lika med)
        # 'quit' = sträng vi jämför med
        # : = kolon som säger "om villkoret är sant, kör koden nedan"
        print("Hej då!")
        # print() = funktion som skriver text
        # "Hej då!" = text som skrivs ut
        # () = parenteser runt funktionen
        break  # Avsluta while-loopen och gå vidare i programmet
        # break = Python-nyckelord som avslutar while-loopen
```

### 7. Lägg till användarmeddelande

```python
conversation_history.append({
    "role": "user",
    "content": message
})
# conversation_history = listan vi skapade tidigare
# . = punkt för att använda en metod
# append() = metod som lägger till något i listan
# () = parenteser runt metoden
# { = startar en dictionary (nyckel-värde par)
# "role" = nyckel (namn)
# : = kolon som separerar nyckel och värde
# "user" = värde (vem som skrev meddelandet)
# , = komma som separerar nyckel-värde par
# "content" = nyckel (innehållet)
# : = kolon som separerar nyckel och värde
# message = värde (vad användaren skrev)
# } = avslutar dictionary
# ) = avslutar append-funktionen
```

### 8. Visa meddelanden

```python
print("Användare:", message)
# print() = funktion som skriver text
# "Användare:" = text som skrivs ut
# , = komma som separerar argument
# message = variabeln med användarens meddelande

print("Assistent:", end=" ")  # end=" " gör att nästa print kommer på samma rad
# print() = funktion som skriver text
# "Assistent:" = text som skrivs ut
# end=" " = parameter som gör att nästa print kommer på samma rad
```

### 9. AI-anrop med felhantering

```python
try:
    # try = Python-nyckelord för att testa kod som kan ge fel
    # : = kolon som säger "kör koden nedan och fånga eventuella fel"

    response = model.invoke(conversation_history)
    # response = variabel som sparar AI:ns svar
    # = = tilldelningsoperator
    # model = AI-modellen vi skapade tidigare
    # . = punkt för att använda en metod
    # invoke() = metod som skickar meddelande till AI:n
    # () = parenteser runt metoden
    # conversation_history = hela listan med alla meddelanden
    # ) = avslutar invoke-funktionen

    conversation_history.append({
        "role": "assistant",
        "content": response.content
    })
    # conversation_history = listan vi skapade tidigare
    # . = punkt för att använda en metod
    # append() = metod som lägger till något i listan
    # () = parenteser runt metoden
    # { = startar en dictionary
    # "role" = nyckel
    # : = kolon
    # "assistant" = värde (AI:n skrev detta)
    # , = komma
    # "content" = nyckel
    # : = kolon
    # response = AI:ns svar
    # . = punkt för att använda en metod
    # content = metod som hämtar texten från svaret
    # } = avslutar dictionary
    # ) = avslutar append-funktionen

    print(response.content)  # .content innehåller AI:ns svar som text
    # print() = funktion som skriver text
    # response = AI:ns svar
    # . = punkt för att använda en metod
    # content = metod som hämtar texten från svaret
    # () = parenteser runt funktionen

except Exception as e:
    # except = Python-nyckelord för felhantering
    # Exception = typ av fel som fångas
    # as = nyckelord som ger felet ett namn
    # e = namn på felet (kan heta vad som helst)
    # : = kolon som säger "om det blir fel, kör koden nedan"
    print(f"Fel vid anrop till OpenAI: {e}")
    # print() = funktion som skriver text
    # f = f-string som låter oss lägga in variabler i texten
    # "Fel vid anrop till OpenAI: " = text som skrivs ut
    # {e} = variabeln med felmeddelandet
    # () = parenteser runt funktionen
    print("Kontrollera att din API-nyckel är korrekt och att du har internetanslutning.")
    # print() = funktion som skriver text
    # "Kontrollera att din API-nyckel..." = text som skrivs ut
    # () = parenteser runt funktionen
```

### 10. Programstart

```python
if __name__ == "__main__":
    # if = Python-nyckelord för villkor
    # __name__ = speciell variabel som innehåller modulnamnet
    # == = jämförelseoperator (är lika med)
    # "__main__" = sträng som betyder "denna fil körs direkt"
    # : = kolon som säger "om villkoret är sant, kör koden nedan"
    main()  # Anropa main() funktionen för att starta programmet
    # main() = anropar main-funktionen
    # () = parenteser runt funktionsanropet
    # Anropa main() funktionen för att starta programmet = förklaring av vad som händer
# Om filen importeras som en modul kommer denna kod inte att köras = förklaring av när koden körs
```

## Sammanfattning

Detta program skapar en interaktiv chat med OpenAI:s AI-modell genom LangChain. Det:

1. **Läser API-nyckeln** från en `.env` fil
2. **Skapar en AI-modell** med gpt-4o-mini
3. **Sparar konversationshistorik** i en lista
4. **Kör en oändlig loop** som:
   - Tar input från användaren
   - Skickar meddelandet till AI:n
   - Visar svaret
   - Sparar allt i historiken
5. **Hanterar fel** om något går snett

Alla superdetaljerade kommentarer finns nu i denna `main.md` fil så att `main.py` är ren och lättläst! 🎉
