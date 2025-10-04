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
