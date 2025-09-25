# LangChain ChatOpenAI Implementation

## Dokumentationslänkar

### LangChain ChatOpenAI-integration:
https://python.langchain.com/docs/integrations/chat/openai/?utm_source=chatgpt.com

### LangChain Runnable-koncept (t.ex. .invoke()):
https://python.langchain.com/docs/concepts/runnables/?utm_source=chatgpt.com

### langchain-openai på PyPI (paket och import):
https://pypi.org/project/langchain-openai/?utm_source=chatgpt.com

### OpenAI modellöversikt:
https://platform.openai.com/docs/models?utm_source=chatgpt.com

### OpenAI API-nyckel och säker hantering:
https://platform.openai.com/docs/quickstart/step-2-setup-your-api-key?utm_source=chatgpt.com

### OpenAI allmän dokumentation (råd & best practices):
https://platform.openai.com/docs/?utm_source=chatgpt.com

## Modellval

Baserat på [OpenAI:s modellöversikt](https://platform.openai.com/docs/models?utm_source=chatgpt.com) har vi valt **gpt-4o-mini** eftersom:
- Den är kostnadseffektiv
- Snabb respons
- Bra prestanda för enkla uppgifter
- Stöds av LangChain ChatOpenAI

## Installation

### Beroenden
Baserat på [langchain-openai på PyPI](https://pypi.org/project/langchain-openai/?utm_source=chatgpt.com):

```bash
pip install langchain-openai python-dotenv
```

### API-nyckelkonfiguration
Följ [OpenAI:s guide för API-nyckel](https://platform.openai.com/docs/quickstart/step-2-setup-your-api-key?utm_source=chatgpt.com):

#### Linux/Mac:
```bash
export OPENAI_API_KEY="din-api-nyckel-här"
```

#### Windows:
```cmd
set OPENAI_API_KEY=din-api-nyckel-här
```

#### .env fil:
Skapa en `.env` fil i projektroten:
```
OPENAI_API_KEY=din-api-nyckel-här
```

## Användning

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini")
response = model.invoke("Hej!")
print(response.content)
```

## Felsökning

### Vanliga fel:

1. **ImportError: No module named 'langchain_openai'**
   - Lösning: Installera paketet med `pip install langchain-openai`
   - Referens: [langchain-openai på PyPI](https://pypi.org/project/langchain-openai/?utm_source=chatgpt.com)

2. **AuthenticationError: Invalid API key**
   - Lösning: Kontrollera att OPENAI_API_KEY är satt korrekt
   - Referens: [OpenAI API-nyckel guide](https://platform.openai.com/docs/quickstart/step-2-setup-your-api-key?utm_source=chatgpt.com)

3. **AttributeError: 'AIMessage' object has no attribute 'content'**
   - Lösning: Använd `response.content` istället för bara `response`
   - Referens: [LangChain Runnable dokumentation](https://python.langchain.com/docs/concepts/runnables/?utm_source=chatgpt.com)

## Exempeloutput

```
Användare: Hej! Kan du berätta en kort vits på svenska?
Assistent: [AI:n svarade med en svensk vits - exakt output varierar]
```

**Not:** Scriptet kördes framgångsrikt med gpt-4o-mini modellen via LangChain ChatOpenAI och .invoke() metoden. Varningen om urllib3/OpenSSL är bara en kompatibilitetsnotis och påverkar inte funktionaliteten.

## Implementationsdetaljer

- **Import**: `from langchain_openai import ChatOpenAI` ([LangChain ChatOpenAI docs](https://python.langchain.com/docs/integrations/chat/openai/?utm_source=chatgpt.com))
- **Modell**: `gpt-4o-mini` ([OpenAI modellöversikt](https://platform.openai.com/docs/models?utm_source=chatgpt.com))
- **Anrop**: `.invoke()` metod ([LangChain Runnable docs](https://python.langchain.com/docs/concepts/runnables/?utm_source=chatgpt.com))
- **API-nyckel**: Via miljövariabel `OPENAI_API_KEY` ([OpenAI API guide](https://platform.openai.com/docs/quickstart/step-2-setup-your-api-key?utm_source=chatgpt.com))