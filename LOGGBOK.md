## Loggbok

### Projekt: AI‑chat med debugpanel (Streamlit)
### Student: [Ditt namn]
### Datum: [Fyll i aktuellt datumintervall]

---

### Min resa genom projektet (kronologisk berättelse)

Jag började projektet med att sätta upp en grundläggande Streamlit‑app i `main.py`. Det var viktigt för mig att ha en tydlig struktur från början, så jag skapade ett eget lager för att hantera kommunikationen med OpenAI, som jag kallade `LLMHandler`. Detta gjorde det enklare att hålla koden organiserad och möjliggjorde framtida utbyggnader.

När grundstrukturen var på plats fokuserade jag på att bygga den första huvudfunktionen: "Få tips". Jag lade till en spinner för att visa användaren att något hände, implementerade modellinställningar så att användaren kunde välja mellan olika OpenAI‑modeller, och byggde upp ett system för att hantera systemprompts. Jag insåg tidigt att felhantering var kritisk, så jag lade till try‑except‑block runt alla API‑anrop för att ge tydliga felmeddelanden om något gick fel.

Efter att ha fått grundfunktionaliteten att fungera, bestämde jag mig för att lägga till ett "Demo/Exempel"‑läge. Detta skulle göra det enklare för användare att testa appen utan att behöva komma på egna prompts. Jag skapade en struktur med fördefinierade exempel som var organiserade efter ämne (som Programmering, Matematik, Språk, Design, Dataanalys och Projektledning) och svårighetsgrad (Lätt, Medel, Svår). Jag implementerade UI‑komponenter med radio‑knappar och selectboxar för att användarna enkelt skulle kunna välja mellan olika exempel.

Nästa steg blev att bygga en "Prompt Builder"‑funktion. Jag ville att användare skulle kunna spara sina egna prompts för återanvändning. Först byggde jag ett formulär där användare kunde ange namn, innehåll och en valfri beskrivning för sina prompts. Jag implementerade funktionalitet för att visa, redigera och ta bort sparade prompts. Senare, när jag implementerade databaslagring, kopplade jag detta till SQLite för att säkerställa att prompts sparades permanent.

Under tiden jag arbetade med dessa funktioner, märkte jag att koden började bli rörig. Jag bestämde mig för att förenkla och organisera bättre. Jag skapade hjälpfunktioner som `add_message_to_chat` och `get_system_prompt` för att undvika kodduplicering. Ett problem jag stötte på var ett "Unexpected indentation"‑fel, som visade sig bero på att jag hade duplicerad kod. Detta lärde mig vikten av att vara noggrann när man refaktorerar kod. Jag tog också bort alla emojis från UI:et på begäran, och diskuterade senare möjligheten att ersätta dem med text. För att göra koden renare tog jag bort alla kommentarer utom rubriker, vilket gjorde koden mer läsbar och professionell.

Parallellt med utvecklingen av appen arbetade jag också med flera Python‑övningar. Jag gick igenom uppgifter som "Till 120", "True/False", summor av tal och en funktion som heter `is_alt`. Genom dessa övningar lärde jag mig att hantera olika typer av fel: `TypeError` när jag försökte dividera strängar, `NameError` när jag hade stavfel i variabelnamn, och `IndentationError` när jag glömde indentera korrekt. Jag lärde mig också att läsa och tolka traceback‑meddelanden, vilket blev ovärderligt för felsökning.

En viktig insikt kom när jag började tänka på minneshantering. Jag upptäckte att jag lagrade meddelanden och feedback på flera ställen, vilket kunde leda till inkonsistens. Jag bestämde mig för att implementera en "single source of truth"‑princip. Runtime‑state skulle ligga i `st.session_state.messages` för snabb UI‑hantering, medan all persistent lagring skulle ske i SQLite via `feedback_db.py`. Jag tog bort dubbellagring av både meddelanden och feedback, vilket gjorde systemet mer robust och lättare att underhålla.

För att implementera persistent lagring skapade jag flera tabeller i SQLite: `conversations` för att spåra olika konversationer, `messages` för att lagra alla meddelanden i rätt ordning, `saved_prompts` för användarnas sparade prompts, och `feedback` för användarfeedback. Jag byggde funktioner för att spara, läsa och ta bort data, samt exportfunktioner som låter användare exportera data som JSON, CSV eller hela databasfilen. Detta gav användarna kontroll över sina data och möjliggjorde backup.

Jag gick igenom alla filer systematiskt för att hitta och fixa eventuella fel. Jag lade till kompakta rubriker i alla filer för bättre organisation och tog bort onödiga kommentarer. När jag var nöjd med kodkvaliteten började jag arbeta med Git. Jag gjorde flera commits och pushade dem till GitHub, inklusive commits för systemprompt‑hantering, konversationshantering och prompts i databasen. Jag diskuterade också med mig själv om hur commit‑meddelanden skulle formuleras för att vara tydliga men inte för långa.

En stor förbättring kom när jag implementerade strömmande AI‑svar. Jag bytte från synkrona API‑anrop till streaming, vilket innebar att svaret började visas direkt när det genererades, istället för att användaren behövde vänta tills hela svaret var klart. Jag aktiverade `streaming=True` i `LLMHandler` och skapade en ny `stream`‑metod som yieldar tokens löpande. I `handle_llm_request` uppdaterade jag koden för att rendera texten live med hjälp av en placeholder, implementerade en fungerande avbryt‑knapp som kontrolleras i loopen, och säkerställde att debug‑information registreras när svaret är klart eller om ett fel uppstår. Eftersom streaming nu var den enda metoden som användes, tog jag bort den gamla synkrona `invoke`‑metoden och rensade bort oanvända importer och onödig session‑state för debug.

Jag förtydligade också för mig själv vad "persistent" vs "runtime" innebär och hur de samspelar i appen. Runtime‑state i `st.session_state` är snabbt och används för UI‑interaktioner, medan persistent lagring i SQLite säkerställer att data finns kvar även efter att appen stängts. `MemoryManager` förenklades till att endast hantera debughistorik med en rolling window, eftersom all annan data nu hanteras i databasen.

Under projektets gång diskuterade jag också flera viktiga ämnen som tester, säkerhet, sandbox och backup. Jag lärde mig om bas‑unittester med pytest, hur man använder in‑memory databaser för testning, och hur man mockar externa beroenden. Jag gick igenom säkerhetsaspekter som att lagra API‑nycklar i `.env`‑filer istället för i koden, och diskuterade behovet av inputvalidering. Jag lärde mig också om sandbox‑miljöer och Docker, och hur man kan köra appen isolerat för säkerhet. För databasbackup diskuterade jag strategier som periodiska snapshots, rotation av backup‑filer, och möjligheten att lagra backups offsite.

Slutligen dokumenterade jag allt arbete i denna loggbok. Projektet har utvecklats från en grundläggande chattapp till ett mer robust verktyg med strömmande AI‑svar, tydlig state‑modell och persistens i SQLite. Detta har förbättrat användarupplevelsen avsevärt, möjliggjort återladdning av historik, och underlättat felsökning via debugpanelen. Jag är stolt över den resa jag har gjort och de färdigheter jag har utvecklat under projektets gång.

---

### Viktiga lärdomar

Genom projektet har jag lärt mig värdet av att ha en tydlig arkitektur från början, att undvika kodduplicering, och att tänka på både användarupplevelse och kodkvalitet. Jag har också förstått vikten av att ha en "single source of truth" för data, och hur streaming kan förbättra användarupplevelsen avsevärt. Att arbeta med databaser och persistent lagring har gett mig en bättre förståelse för hur moderna webbapplikationer fungerar.

---

### Teknisk översikt

Appen är byggd med Streamlit för UI, OpenAI:s API för AI‑funktionalitet via LangChain, och SQLite för persistent datalagring. Alla API‑nycklar hanteras säkert via `.env`‑filer, och appen stödjer export av data i flera format för användarnas kontroll och backup.

---

### Hur man kör appen

1. Skapa och aktivera virtuell miljö (om inte redan):
   - `python -m venv venv`
   - `source venv/bin/activate` (macOS/Linux) eller `venv\Scripts\activate` (Windows)
2. Installera beroenden: `pip install -r requirements.txt`
3. Skapa `.env` i projektroten med: `OPENAI_API_KEY=din-nyckel`
4. Starta appen: `streamlit run main.py`

---

### Exempel på viktiga commit‑meddelanden

- "Streaming: icke‑blockerande LLM‑svar och responsiv debugpanel"
- "Rensning: ta bort oanvänd kod och invoke"
- "Uppdatering: systemprompt, konversationshantering, prompts i databas"
