# AI‑chat – Övergripande kommentarer och snabbguide

Den här filen ger en kort överblick över hur du kör projektet, ställer in nycklar och vad koden gör på en hög nivå. För detaljer, läs källkoden i respektive modul (`app.py`, `llm_handler.py`, `memory_manager.py`, `config.py`).

## Överblick
- UI byggt i Streamlit (`app.py`).
- LLM‑anrop kapslade i `LLMHandler` (`llm_handler.py`).
- Konversationsminne och debug lagras i `MemoryManager` (`memory_manager.py`).
- Konfiguration (modell, temperatur, feltexter) i `config.py`.

## Installation
```
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## API‑nyckel
Lägg till i `.env` (checka inte in):
```
printf "OPENAI_API_KEY=din-nyckel\n" > .env
```
eller exportera i terminalen:
```
export OPENAI_API_KEY="din-nyckel"
```

## Starta appen
```
streamlit run app.py
```

## Användning (kort)
- Skriv i chatten och tryck Enter för att skicka.
- “Rensa chatt” tömmer historiken. “Exportera chatt” laddar ner JSON.
- Debugpanelen visar senaste anropsdata (modell, temperatur, svarstid m.m.).

## Tips
- Håll hemligheter i `.env` (inte i git).
- Kör alltid `pip install -r requirements.txt` i en aktiverad virtuell miljö.
- Om något strular: kontrollera API‑nyckel, nätverk och fel i debugpanelen.
