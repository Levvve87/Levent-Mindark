## Loggbok

### Projekt: AI‑chat med debugpanel (Streamlit)
### Student: Levent Kantarci


---

### Vecka för vecka

**Vecka 1 – Planering och setup**  
- Inventerade krav, skissade UI‑layout och valde teknikstack (Streamlit + LangChain + SQLite).  
- Satt upp grundrepo, virtuell miljö och `.env`‑hantering för API‑nycklar.  
- Dokumenterade projektstrukturen i README och planerade loggbokslayouten.

**Vecka 2 – Basfunktionalitet**  
- Byggde huvudloopen i `main.py` med Streamlit‑widgets och statehantering.  
- Implementerade `LLMHandler` som abstraherar OpenAI-anrop och gav robust felhantering.  
- Första versionen av “Få tips” färdig: spinner, modellval, temperaturreglage och systemprompt.

**Vecka 3 – Exempel och promptverktyg**  
- Lade till “Demo/Exempel”-läget med färdiga prompts per ämne och svårighetsgrad.  
- Införde UI-komponenter (selectbox, select_slider) för att styra exempelvisningar.  
- Skapade “Prompt Builder” för att spara, läsa och ta bort egna prompts lokalt.

**Vecka 4 – Refaktorering och hjälpkomponenter**  
- Införde hjälpfunktioner (`add_message_to_chat`, `get_system_prompt`) för att minska duplicering.  
- Styrde UI‑logik och state tydligare genom att samla allt i `st.session_state`.  
- Rensade kodbasen på onödiga kommentarer, emojis och gamla experiment för att höja läsbarheten.

**Vecka 5 – Persistens och databaser**  
- Kopplade `feedback_db.py` till SQLite och skapade tabeller för `conversations`, `messages`, `saved_prompts`, `feedback`.  
- Implementerade spara/ladda funktioner för meddelanden, prompts och feedback samt export till JSON/CSV/DB.  
- Säkerställde “single source of truth”: runtime i `st.session_state`, persistens i databasen.

**Vecka 6 – Konversations- och debugpaneler**  
- Byggde sidopanel för att lista, ladda, skapa och ta bort konversationer via `ui_conversations.py`.  
- Förädlade debugpanelen med feedbacklista, massradering, exportknappar och säkerhetskontroller.  
- Förbättrade MemoryManager för att endast hålla senaste debughändelserna.

**Vecka 7 – Streaming och responsivitet**  
- Migrerade till strömmande svar i `LLMHandler` och visade tokenflödet live i chatten.  
- Implementerade avbryt-knapp, förbättrade felutskrifter och realtidsdebug (modell, svarstid, kostnad).  
- Optimerade UI-upplevelsen och såg till att databaslogiken uppdateras i takt med streamen.

**Vecka 8 – Säkerhet, tester och polish**  
- Gick igenom säkerhet (API-nycklar, inputvalidering), backup-strategier och testidéer.  
- Lade till extra säkerhetskontroller i session state, förbättrade felhantering i feedback och konversationsval.  
- Slutdokumenterade projektresan i loggboken och förberedde leverans med tydlig teknisk översikt.

För att implementera persistent lagring skapade jag flera tabeller i SQLite: `conversations` för att spåra olika konversationer, `messages` för att lagra alla meddelanden i rätt ordning, `saved_prompts` för användarnas sparade prompts, och `feedback` för användarfeedback. Jag byggde funktioner för att spara, läsa och ta bort data, samt exportfunktioner som låter användare exportera data som JSON, CSV eller hela databasfilen. Detta gav användarna kontroll över sina data och möjliggjorde backup.

Jag gick igenom alla filer systematiskt för att hitta och fixa eventuella fel. Jag lade till kompakta rubriker i alla filer för bättre organisation och tog bort onödiga kommentarer. När jag var nöjd med kodkvaliteten började jag arbeta med Git. Jag gjorde flera commits och pushade dem till GitHub, inklusive commits för systemprompt‑hantering, konversationshantering och prompts i databasen. Jag diskuterade också med mig själv om hur commit‑meddelanden skulle formuleras för att vara tydliga men inte för långa.

En stor förbättring kom när jag implementerade strömmande AI‑svar. Jag bytte från synkrona API‑anrop till streaming, vilket innebar att svaret började visas direkt när det genererades, istället för att användaren behövde vänta tills hela svaret var klart. Jag aktiverade `streaming=True` i `LLMHandler` och skapade en ny `stream`‑metod som yieldar tokens löpande. I `handle_llm_request` uppdaterade jag koden för att rendera texten live med hjälp av en placeholder, implementerade en fungerande avbryt‑knapp som kontrolleras i loopen, och säkerställde att debug‑information registreras när svaret är klart eller om ett fel uppstår. Eftersom streaming nu var den enda metoden som användes, tog jag bort den gamla synkrona `invoke`‑metoden och rensade bort oanvända importer och onödig session‑state för debug.

Jag förtydligade också för mig själv vad "persistent" vs "runtime" innebär och hur de samspelar i appen. Runtime‑state i `st.session_state` är snabbt och används för UI‑interaktioner, medan persistent lagring i SQLite säkerställer att data finns kvar även efter att appen stängts. `MemoryManager` förenklades till att endast hantera debughistorik med en rolling window, eftersom all annan data nu hanteras i databasen.

Under projektets gång diskuterade jag också flera viktiga ämnen som tester, säkerhet, sandbox och backup. Jag lärde mig om bas‑unittester med pytest, hur man använder in‑memory databaser för testning, och hur man mockar externa beroenden. Jag gick igenom säkerhetsaspekter som att lagra API‑nycklar i `.env`‑filer istället för i koden, och diskuterade behovet av inputvalidering. Jag lärde mig också om sandbox‑miljöer och Docker, och hur man kan köra appen isolerat för säkerhet. För databasbackup diskuterade jag strategier som periodiska snapshots, rotation av backup‑filer, och möjligheten att lagra backups offsite.

Slutligen dokumenterade jag allt arbete i denna loggbok. Projektet har utvecklats från en grundläggande chattapp till ett mer robust verktyg med strömmande AI‑svar, tydlig state‑modell och persistens i SQLite. Detta har förbättrat användarupplevelsen avsevärt, möjliggjort återladdning av historik, och underlättat felsökning via debugpanelen. Jag är stolt över den resa jag har gjort och de färdigheter jag har utvecklat under projektets gång.

---r

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

