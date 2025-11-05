# IMPORTER
import os
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from config import Config
from memory_manager import MemoryManager
from llm_handler import LLMHandler
from feedback_db import init_db, save_feedback, get_feedback_summary, get_recent_feedback, export_feedback_json, export_feedback_csv, save_message, load_messages, create_or_update_conversation, delete_messages, delete_conversation, get_all_conversations, save_prompt, get_all_prompts, delete_prompt
import uuid

# HJÄLPFUNKTIONER - SYSTEMPROMPTS
def build_system_prompt(mode: str, subject: str, difficulty: str) -> str:
    mode = mode or "Lärläge"
    subject = subject or "Allmänt"
    difficulty = difficulty or "Medel"

    base = (
        f"Ämne: {subject}. Nivå: {difficulty}."
        f"Svara på svenska och håll dig konkret och hjälpsam"

    )

    if mode == "Lärläge":
        style = (
            "Du är en pedagogisk handledare."
            "Ge korta, begripliga förklaringar och 1-2 enkla exempel."
            "Belys nyckelgrepp tydligt."
        )

    else:
        style = (
            "Du är en coach."
            "Ge 1-3 konkreta övningar med tydliga steg."
            "Lägg till kort återkopplingstips efter varje övning."
        )

    return f"{base} {style}"

# HJÄLPFUNKTIONER - UI & TEMA
def inject_theme_css(is_dark: bool) -> None:
    if is_dark:
        st.markdown(
            """
            <style>
            .stApp { background-color: #0e1117; color: #e5e7eb; }
            [data-testid="stSidebar"] { background-color: #111827; }
            [data-testid="stHeader"] { background-color: transparent; }
            div.stMarkdown, p, span, label { color: #e5e7eb !important; }
            code, pre { background: #111827 !important; color: #e5e7eb !important; }
            .stButton>button { background-color: #2563eb; color: #ffffff; border: 1px solid #1d4ed8; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .stApp { background-color: #ffffff; color: #111827; }
            [data-testid="stSidebar"] { background-color: #f8fafc; }
            [data-testid="stHeader"] { background-color: transparent; }
            div.stMarkdown, p, span, label { color: #111827 !important; }
            code, pre { background: #f3f4f6 !important; color: #111827 !important; }
            .stButton>button { background-color: #f0f2f6; color: #111827; border: 1px solid #e5e7eb; }
            </style>
            """,
            unsafe_allow_html=True,
        )

# HJÄLPFUNKTIONER - MEDDELANDEN & KONVERSATION
def add_message_to_chat(role, content, timestamp=None):
    if not timestamp:
        timestamp = datetime.now().strftime("%H:%M:%S")
    message = {
        "role": role,
        "content": content,
        "timestamp": timestamp
    }
    st.session_state.messages.append(message)
    if "db_conn" in st.session_state and "conversation_id" in st.session_state:
        try:
            create_or_update_conversation(st.session_state.db_conn, st.session_state.conversation_id)
            save_message(
                st.session_state.db_conn,
                conversation_id=st.session_state.conversation_id,
                role=role,
                content=content,
                timestamp=timestamp
            )
        except Exception as e:
            st.warning(f"Kunde inte spara meddelande i databas: {e}")

def get_conversation_history():
    return [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]

# HJÄLPFUNKTIONER - STATE INITIERING
def init_session_state():
    if "db_conn" not in st.session_state:
        st.session_state.db_conn = init_db("feedback.db")
    
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
        try:
            messages = load_messages(st.session_state.db_conn, st.session_state.conversation_id)
            st.session_state.messages = messages if messages else []
        except Exception:
            st.session_state.messages = []
    else:
        if "messages" not in st.session_state:
            try:
                messages = load_messages(st.session_state.db_conn, st.session_state.conversation_id)
                st.session_state.messages = messages if messages else []
            except Exception:
                st.session_state.messages = []
    
    if "debug_info" not in st.session_state:
        st.session_state.debug_info = []
    
    st.session_state.setdefault("mode", "Lärläge")
    st.session_state.setdefault("subject", "Programmering")
    st.session_state.setdefault("difficulty", "Medel")
    st.session_state.setdefault("dark_mode", False)
    
    if "saved_prompts" not in st.session_state:
        try:
            prompts = get_all_prompts(st.session_state.db_conn)
            st.session_state.saved_prompts = {p["name"]: {"content": p["content"], "description": p["description"]} for p in prompts}
        except Exception:
            st.session_state.saved_prompts = {}

# HJÄLPFUNKTIONER - LLM ANROP
def handle_llm_request(model_name: str, temperature: float, prompt_text: str = None, system_message: str = None):
    st.session_state.abort_requested = False
    try:
        spinner_text = "Tar fram tips..." if prompt_text else "Tänker..."
        with st.spinner(spinner_text):
            llm_handler.update_model_settings(model_name=model_name, temperature=temperature)
            conversation_history = get_conversation_history()
            system_prompt_text = system_message or get_system_prompt()
            response, debug_info = llm_handler.invoke(conversation_history, system_message=system_prompt_text)
            
            if st.session_state.get("abort_requested", False):
                st.warning("Anrop avbrutet av användaren.")
                st.stop()
            
            add_message_to_chat("assistant", response.content)
            memory.add_debug_info(debug_info)
            with st.chat_message("assistant"):
                st.write(response.content)
            return True
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Fel vid AI-anrop: {str(e)}")
        return False

# HJÄLPFUNKTIONER - PROMPTS & EXEMPEL
def get_system_prompt():
    selected_saved_prompt = st.session_state.get("selected_saved_prompt", "Ingen prompt vald")
    
    if selected_saved_prompt != "Ingen prompt vald" and selected_saved_prompt in st.session_state.saved_prompts:
        return st.session_state.saved_prompts[selected_saved_prompt]['content']
    elif st.session_state.get("mode") == "Demo/Exempel":
        return st.session_state.get("demo_example")
    else:
        base = build_system_prompt(
            st.session_state.get("mode", "Lärläge"),
            st.session_state.get("subject", "Programmering"),
            st.session_state.get("difficulty", "Medel")
        )
        try:
            summary = get_feedback_summary(st.session_state.db_conn)
            if summary.get("down", 0) > summary.get("up", 0):
                base += " Var extra tydlig, konkret och undvik vaga formuleringar."
            elif summary.get("up", 0) > 0:
                base += " Behåll den tydliga och hjälpsamma tonen."
        except Exception:
            pass
        return base

def get_demo_examples():
    return {
        "Programmering": {
            "Lätt": [
                "Förklara vad en variabel är i programmering",
                "Vad är skillnaden mellan en lista och en dictionary?",
                "Hur fungerar en if-sats?"
            ],
            "Medel": [
                "Skriv en funktion som räknar antalet ord i en text",
                "Förklara objektorienterad programmering med exempel",
                "Vad är skillnaden mellan en klass och ett objekt?"
            ],
            "Svår": [
                "Implementera en binär sökning i Python",
                "Förklara design patterns med praktiska exempel",
                "Optimera denna algoritm för bättre prestanda"
            ]
        },
        "Matematik": {
            "Lätt": [
                "Lös ekvationen: 2x + 5 = 13",
                "Vad är arean av en cirkel med radie 5?",
                "Förklara vad procent är med exempel"
            ],
            "Medel": [
                "Derivera funktionen f(x) = x² + 3x + 2",
                "Lös andragradsekvationen: x² - 4x + 3 = 0",
                "Förklara trigonometri med praktiska exempel"
            ],
            "Svår": [
                "Lös differentialekvationen: dy/dx = 2y",
                "Beräkna integralen: ∫(x² + 1)dx från 0 till 2",
                "Förklara komplexa tal och deras användning"
            ]
        },
        "Språk": {
            "Lätt": [
                "Förklara skillnaden mellan substantiv och adjektiv",
                "Vad är en mening och hur bygger man en?",
                "Ge exempel på olika typer av pronomen"
            ],
            "Medel": [
                "Analysera stilistiska verktyg i denna text",
                "Förklara skillnaden mellan aktiv och passiv form",
                "Vad är en metafor och ge exempel"
            ],
            "Svår": [
                "Skriv en litterär analys av denna dikt",
                "Förklara postmodernistiska litterära tekniker",
                "Analysera språkets makt i politisk retorik"
            ]
        },
        "Design": {
            "Lätt": [
                "Förklara skillnaden mellan form och funktion i design",
                "Vad är färgteori och hur använder man den?",
                "Ge exempel på god typografi"
            ],
            "Medel": [
                "Skapa en wireframe för en mobilapp",
                "Förklara gestaltprinciperna med exempel",
                "Vad är skillnaden mellan UX och UI?"
            ],
            "Svår": [
                "Designa ett komplett designsystem",
                "Förklara design thinking-processen",
                "Analysera denna designs användarupplevelse"
            ]
        },
        "Dataanalys": {
            "Lätt": [
                "Förklara skillnaden mellan kvalitativ och kvantitativ data",
                "Vad är en korrelation och hur mäter man den?",
                "Ge exempel på olika typer av diagram"
            ],
            "Medel": [
                "Analysera denna dataset och hitta mönster",
                "Förklara skillnaden mellan deskriptiv och inferentiell statistik",
                "Vad är en regressionsanalys?"
            ],
            "Svår": [
                "Utför en djupgående statistisk analys av denna data",
                "Förklara machine learning-algoritmer för prediktiv analys",
                "Skapa en komplett dataanalysrapport"
            ]
        },
        "Projektledning": {
            "Lätt": [
                "Förklara skillnaden mellan en uppgift och ett projekt",
                "Vad är en Gantt-diagram och hur använder man den?",
                "Ge exempel på projektledningsverktyg"
            ],
            "Medel": [
                "Skapa en projektplan för en webbutveckling",
                "Förklara skillnaden mellan vattenfalls- och agil metodik",
                "Vad är riskhantering i projekt?"
            ],
            "Svår": [
                "Led ett komplext mjukvaruprojekt med agil metodik",
                "Förklara avancerade projektledningsstrategier",
                "Analysera och förbättra denna projektprocess"
            ]
        }
    }

# INITIERING - API-KEY & KONFIGURATION
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("API-nyckel saknas. Lägg till OPENAI_API_KEY i .env och starta om.")
    st.stop()

st.set_page_config(page_title="AI-chat", layout="wide")
st.title("AI-chat med debugpanel")

memory = MemoryManager()
llm_handler = LLMHandler()

# INITIERING - DATABAS & STATE
init_session_state()

# SIDOPANEL - INSTÄLLNINGAR & KONFIGURATION
with st.sidebar:
    st.header("Modellinställningar")
    st.toggle(
        "Mörkt läge",
        key="dark_mode",
        help="Växla mellan ljust och mörkt tema"
    )
    model = st.selectbox(
        "Modell",
        options=["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="Välj modell för nästa anrop."

    )
    temp = st.slider(
        "Temperatur",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Lägre = mer fokuserat, högre = mer kreativt."
    )
    st.radio(
        "Läge",
        ["Lärläge", "Övningsläge", "Demo/Exempel"],
        key="mode",
        help="Välj hur tipsen ska utformas"
    )
    st.selectbox(
        "Ämne",
        ["Programmering", "Språk", "Matematik", "Design", "Dataanalys", "Projektledning"],
        key="subject",
        help="Välj område för tipsen"
    )
    st.select_slider(
        "Svårighetsgrad",
        options=["Lätt", "Medel", "Svår"],
        key="difficulty",
        help="Välj nivå: Lätt för introduktion, Medel för fördjupning, Svår för avancerat."
    )

    if st.session_state.get("mode") == "Demo/Exempel":
        st.markdown("---")
        st.subheader("Demo-exempel")
        
        demo_examples = get_demo_examples()
        current_subject = st.session_state.get("subject", "Programmering")
        current_difficulty = st.session_state.get("difficulty", "Medel")
        
        if current_subject in demo_examples and current_difficulty in demo_examples[current_subject]:
            examples = demo_examples[current_subject][current_difficulty]
            selected_example = st.selectbox(
                "Välj exempel:",
                examples,
                key="demo_example",
                help="Välj ett exempel att testa"
            )
        else:
            st.warning("Inga exempel tillgängliga för detta ämne/nivå")
            selected_example = None

    st.markdown("---")
    st.subheader("Konversationer")
    
    try:
        conversations = get_all_conversations(st.session_state.db_conn)
        if conversations:
            conv_options = [f"{conv['id'][:8]}... ({conv['updated_at'][:10]})" for conv in conversations]
            conv_options.insert(0, "Ny konversation")
            selected_conv = st.selectbox("Välj konversation:", conv_options, key="conv_selector")
            
            if selected_conv != "Ny konversation":
                selected_id = conversations[conv_options.index(selected_conv) - 1]["id"]
                if st.button("Ladda konversation", key="load_conv"):
                    st.session_state.conversation_id = selected_id
                    messages = load_messages(st.session_state.db_conn, selected_id)
                    st.session_state.messages = messages if messages else []
                    st.rerun()
                if st.button("Ta bort konversation", key="delete_conv"):
                    delete_conversation(st.session_state.db_conn, selected_id)
                    if st.session_state.conversation_id == selected_id:
                        st.session_state.conversation_id = str(uuid.uuid4())
                        st.session_state.messages = []
                    st.rerun()
            else:
                if st.button("Starta ny konversation", key="new_conv"):
                    st.session_state.conversation_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    st.rerun()
        else:
            st.info("Inga konversationer än. Starta en ny chatt!")
    except Exception as e:
        st.caption(f"Kunde inte ladda konversationer: {e}")

    st.markdown("---")
    st.subheader("Prompt Builder")
    
    st.caption("Spara och hantera dina egna prompts")

    with st.expander("Spara ny prompt", expanded=False):
        with st.form("save_prompt_form", clear_on_submit=True):
            prompt_name = st.text_input(
                "Namn på prompt:",
                placeholder="t.ex. 'Kodgranskning'",
                help="Ge din prompt ett beskrivande namn"
            )
            prompt_content = st.text_area(
                "Prompt-innehåll:",
                placeholder="Skriv din prompt här...",
                height=100,
                help="Detta är själva prompten som ska användas"
            )
            prompt_description = st.text_input(
                "Beskrivning (valfritt):",
                placeholder="t.ex. 'För att granska kodkvalitet'",
                help="Kort beskrivning av vad prompten gör"
            )
            save_button = st.form_submit_button("Spara prompt")
            
            if save_button:
                if prompt_name and prompt_content:
                    try:
                        save_prompt(st.session_state.db_conn, prompt_name, prompt_content, prompt_description or "")
                        st.session_state.saved_prompts[prompt_name] = {
                            "content": prompt_content,
                            "description": prompt_description or ""
                        }
                        st.success(f"Prompt '{prompt_name}' sparad!")
                    except Exception as e:
                        st.error(f"Kunde inte spara prompt: {e}")
                else:
                    st.error("Namn och innehåll krävs!")

    if st.session_state.saved_prompts:
        st.markdown("### Sparade prompts")
        
        prompt_names = list(st.session_state.saved_prompts.keys())
        selected_prompt = st.selectbox(
            "Välj en sparad prompt:",
            ["Ingen prompt vald"] + prompt_names,
            key="selected_saved_prompt",
            help="Välj en sparad prompt att använda"
        )
        
        if selected_prompt != "Ingen prompt vald":
            prompt_data = st.session_state.saved_prompts[selected_prompt]
            st.info(f"**{selected_prompt}**")
            if prompt_data["description"]:
                st.caption(f"{prompt_data['description']}")
            with st.expander("Visa prompt-innehåll"):
                st.code(prompt_data["content"], language="text")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Redigera", key=f"edit_{selected_prompt}"):
                    st.session_state[f"editing_{selected_prompt}"] = True
            
            with col2:
                if st.button("Ta bort", key=f"delete_{selected_prompt}"):
                    st.session_state[f"confirm_delete_{selected_prompt}"] = True
            
            if st.session_state.get(f"confirm_delete_{selected_prompt}", False):
                st.warning("Är du säker på att du vill ta bort denna prompt?")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Ja, ta bort", key=f"confirm_yes_{selected_prompt}"):
                        try:
                            delete_prompt(st.session_state.db_conn, selected_prompt)
                            del st.session_state.saved_prompts[selected_prompt]
                            st.session_state[f"confirm_delete_{selected_prompt}"] = False
                            st.session_state.selected_saved_prompt = "Ingen prompt vald"
                            st.success(f"Prompt '{selected_prompt}' borttagen!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kunde inte ta bort prompt: {e}")
                with col2:
                    if st.button("Avbryt", key=f"confirm_no_{selected_prompt}"):
                        st.session_state[f"confirm_delete_{selected_prompt}"] = False
                        st.rerun()
            
            if st.session_state.get(f"editing_{selected_prompt}", False):
                st.markdown("#### Redigera prompt")
                with st.form(f"edit_form_{selected_prompt}", clear_on_submit=False):
                    new_name = st.text_input(
                        "Nytt namn:",
                        value=selected_prompt,
                        key=f"new_name_{selected_prompt}"
                    )
                    new_content = st.text_area(
                        "Nytt innehåll:",
                        value=prompt_data["content"],
                        height=100,
                        key=f"new_content_{selected_prompt}"
                    )
                    new_description = st.text_input(
                        "Ny beskrivning:",
                        value=prompt_data["description"],
                        key=f"new_description_{selected_prompt}"
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        save_edit = st.form_submit_button("Spara ändringar")
                    with col2:
                        cancel_edit = st.form_submit_button("Avbryt")
                    
                    if save_edit:
                        if new_name and new_content:
                            try:
                                if new_name != selected_prompt:
                                    delete_prompt(st.session_state.db_conn, selected_prompt)
                                    del st.session_state.saved_prompts[selected_prompt]
                                save_prompt(st.session_state.db_conn, new_name, new_content, new_description or "")
                                st.session_state.saved_prompts[new_name] = {
                                    "content": new_content,
                                    "description": new_description or ""
                                }
                                st.session_state[f"editing_{selected_prompt}"] = False
                                st.session_state.selected_saved_prompt = new_name
                                st.success(f"Prompt uppdaterad som '{new_name}'!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Kunde inte uppdatera prompt: {e}")
                        else:
                            st.error("Namn och innehåll krävs!")
                    
                    if cancel_edit:
                        st.session_state[f"editing_{selected_prompt}"] = False
                        st.rerun()
    else:
        st.info("Inga sparade prompts än. Spara din första prompt ovan!")

# HUVUDINNEHÅLL - CHATT & DEBUG
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat")
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"{message['timestamp']}")
            if message["role"] == "assistant":
                c1, c2 = st.columns([1,1])
                with c1:
                    up_clicked = st.button("👍", key=f"fb_up_{idx}")
                with c2:
                    down_clicked = st.button("👎", key=f"fb_down_{idx}")
                if up_clicked or down_clicked:
                    st.session_state[f"fb_choice_{idx}"] = "up" if up_clicked else "down"
                choice = st.session_state.get(f"fb_choice_{idx}")
                if choice and not st.session_state.get(f"fb_saved_{idx}", False):
                    with st.expander("Lägg till orsak (valfritt)"):
                        reason = st.text_area("Varför?", key=f"fb_reason_{idx}", height=80)
                        if st.button("Spara feedback", key=f"fb_save_{idx}"):
                            save_feedback(
                                st.session_state.db_conn,
                                conversation_id=st.session_state.conversation_id,
                                message_index=idx,
                                role=message.get("role", "assistant"),
                                rating=choice,
                                reason=reason or "",
                                message_content=message.get("content", "")
                            )
                            st.session_state[f"fb_saved_{idx}"] = True
                            st.success("Tack! Feedback sparad.")

    disable_get_tips = False
    if st.session_state.get("mode") == "Demo/Exempel":
        disable_get_tips = not bool(st.session_state.get("demo_example"))

    if st.button("Få tips", disabled=disable_get_tips):
        system_prompt = get_system_prompt()
        if not system_prompt:
            st.warning("Välj ett exempel först!")
            st.stop()
        
        user_trigger = system_prompt
        add_message_to_chat("system", f"Du är en hjälpsam AI-assistent. Svara på svenska och håll dig konkret och pedagogisk. Användaren har frågat: {system_prompt}")
        add_message_to_chat("user", user_trigger)
        
        handle_llm_request(model, temp, prompt_text=user_trigger, system_message=system_prompt)

    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_input("Skriv ditt meddelande…", value="")
        submitted = st.form_submit_button("Skicka")

    if submitted and user_text.strip():
        add_message_to_chat("user", user_text)
        with st.chat_message("user"):
            st.write(user_text)
        handle_llm_request(model, temp)

# DEBUGPANEL - DEBUG-INFO & EXPORTER
with col2:
    st.subheader("Debug Panel")
    latest_list = memory.get_latest_debug_info(limit=1)
    if latest_list:
        dbg = latest_list[-1]
        st.caption("Senaste anropsdata (fäll ut för mer detaljer).")
        with st.expander("Visa detaljerad debug"):
            st.markdown("### 📊 Snabb översikt")
            st.markdown(f"• **Modell:** `{dbg.get('model', 'okänt')}`")
            st.markdown(f"• **Temperatur:** `{dbg.get('temperature', 'okänt')}`")
            st.markdown(f"• **Meddelanden:** `{dbg.get('messages_count', 'okänt')}`")
            if "response_time" in dbg:
                response_time = dbg['response_time']
                color = "🟢" if response_time < 2.0 else "🟡" if response_time < 5.0 else "🔴"
                st.markdown(f"• **Svarstid:** {color} `{round(response_time, 3)}s`")
            if dbg.get("success", False):
                st.markdown("• **Status:** ✅ Framgång")
            else:
                st.markdown("• **Status:** ❌ Misslyckande")
                if "error" in dbg:
                    st.markdown(f"• **Fel:** `{dbg['error']}`")
            token_usage = dbg.get("token_usage")
            if isinstance(token_usage, dict) and any(v != "N/A" for v in token_usage.values()):
                st.markdown("### 🔢 Token-användning")
                st.markdown(f"• **Prompt:** `{token_usage.get('prompt_tokens', 'N/A')}`")
                st.markdown(f"• **Completion:** `{token_usage.get('completion_tokens', 'N/A')}`")
                st.markdown(f"• **Totalt:** `{token_usage.get('total_tokens', 'N/A')}`")
                if token_usage.get('total_tokens') != "N/A":
                    total = token_usage.get('total_tokens', 0)
                    if isinstance(total, int):
                        cost = (total / 1000) * 0.00015
                        st.markdown(f"• **Kostnad:** ~${cost:.6f}")
            payload = dbg.get("payload")
            if isinstance(payload, dict):
                st.markdown("### 📤 Payload")
                for i, msg in enumerate(payload.get("messages", []), 1):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if len(content) > 200:
                        content = content[:200] + "..."
                    st.markdown(f"  **{i}.** `{role}`: {content}")
            raw_response = dbg.get("raw_response")
            if raw_response:
                st.markdown("### 📥 Rå output")
                raw_text = str(raw_response)
                if len(raw_text) > 1000:
                    st.code(raw_text[:1000] + "\n... (trunkerad)")
                else:
                    st.code(raw_text)
            with st.expander("Visa all debug-data (JSON)"):
                st.json(dbg)
    else:
        st.write("Ingen debug-information ännu. Skicka ett meddelande för att se data.")
    with st.expander("Feedback-logg"):
        try:
            feedback_rows = get_recent_feedback(st.session_state.db_conn, limit=10)
            if feedback_rows:
                for row in feedback_rows:
                    ts = row[7] if len(row) > 7 else ""
                    rating = "👍" if row[4] == "up" else "👎"
                    reason = row[5] if len(row) > 5 else ""
                    st.markdown(f"{rating} `{ts}` — {reason if reason else 'Ingen orsak angiven'}")
            else:
                st.caption("Ingen feedback än.")
        except Exception as e:
            st.caption(f"Kunde inte ladda feedback: {e}")
    if st.button("Rensa chatt"):
        try:
            delete_messages(st.session_state.db_conn, st.session_state.conversation_id)
            st.session_state.messages.clear()
            st.session_state.debug_info = []
            memory.clear_debug_info()
            st.success("Chatt rensad!")
        except Exception as e:
            st.error(f"Kunde inte rensa chatt: {e}")
    if st.button("Avbryt pågående anrop"):
        if st.session_state.get("abort_requested", False):
            st.info("Inget pågående anrop att avbryta.")
        else:
            st.session_state.abort_requested = True
            st.warning("Avbryt-signal skickad. Anropet kommer att stoppas vid nästa kontroll.")
    if st.button("Exportera chatt"):
        if st.session_state.messages:
            json_data = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
            st.download_button(
                label="Ladda ner chatt som JSON",
                data=json_data,
                file_name=f"chatt_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json",
            )
        else:
            st.warning("Inga meddelanden att exportera.")
    if st.button("Exportera TXT"):
        if st.session_state.messages:
            result = []
            for msg in st.session_state.messages:
                timestamp = msg.get("timestamp", "Okänt tid")
                role = msg["role"].upper()
                content = msg["content"]
                result.append(f"[{timestamp}] {role}: {content}")
            txt_data = "\n".join(result)
            st.download_button(
                label="Ladda ner chatt som TXT",
                data=txt_data,
                file_name=f"chatt_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt",
            )
        else:
            st.warning("Inga meddelanden att exportera.")
    if st.button("Exportera feedback-databas"):
        try:
            json_data = export_feedback_json(st.session_state.db_conn)
            st.download_button(
                label="Ladda ner feedback som JSON",
                data=json_data,
                file_name=f"feedback_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json",
                mime="application/json"
            )
            csv_data = export_feedback_csv(st.session_state.db_conn)
            st.download_button(
                label="Ladda ner feedback som CSV",
                data=csv_data,
                file_name=f"feedback_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.warning(f"Kunde inte exportera feedback: {e}")
    if st.button("Exportera SQLite-databas"):
        try:
            with open("feedback.db", "rb") as f:
                db_data = f.read()
            st.download_button(
                label="Ladda ner feedback.db",
                data=db_data,
                file_name=f"feedback_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db",
                mime="application/x-sqlite3"
            )
        except FileNotFoundError:
            st.warning("Databasfilen hittades inte.")
        except Exception as e:
            st.warning(f"Kunde inte exportera databas: {e}")

# TEMA - APPLICERA CSS
inject_theme_css(st.session_state.get("dark_mode", False))
