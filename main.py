# IMPORTER
import os
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from memory_manager import MemoryManager
from llm_handler import LLMHandler
from feedback_db import init_db, save_feedback, get_feedback_summary, get_recent_feedback, export_feedback_json, export_feedback_csv, save_message, load_messages, create_or_update_conversation, delete_messages, delete_conversation, get_all_conversations, save_prompt, get_all_prompts, delete_prompt
import uuid

# HJÄLPFUNKTIONER - SYSTEMPROMPTS
#TODO - flytta ut detta till prompt.py
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
    
    # debug_info i sessionen används inte längre

    st.session_state.setdefault("subject", "Programmering")
    st.session_state.setdefault("difficulty", "Medel")
    st.session_state.setdefault("dark_mode", True)
    
    if "saved_prompts" not in st.session_state:
        try:
            prompts = get_all_prompts(st.session_state.db_conn)
            st.session_state.saved_prompts = {p["name"]: {"content": p["content"], "description": p["description"]} for p in prompts}
        except Exception:
            st.session_state.saved_prompts = {}

# HJÄLPFUNKTIONER - LLM ANROP
#TODO - flytta ut detta till llm_handler.py
def handle_llm_request(model_name: str, temperature: float, prompt_text: str = None, system_message: str = None):
    st.session_state.abort_requested = False
    try:
        llm_handler.update_model_settings(model_name=model_name, temperature=temperature)
        conversation_history = get_conversation_history()
        system_prompt_text = system_message or get_system_prompt()

        with st.chat_message("assistant"):
            placeholder = st.empty()
            accumulated = ""
            for event in llm_handler.stream(conversation_history, system_message=system_prompt_text):
                if st.session_state.get("abort_requested", False):
                    st.warning("Anrop avbrutet av användaren.")
                    break
                if event.get("type") == "token":
                    accumulated += event.get("text", "")
                    placeholder.write(accumulated)
                elif event.get("type") == "done":
                    accumulated = event.get("text", accumulated)
                    placeholder.write(accumulated)
                    debug_info = event.get("debug", {})
                    memory.add_debug_info(debug_info)
                elif event.get("type") == "error":
                    debug_info = event.get("debug", {})
                    memory.add_debug_info(debug_info)
                    st.error(f"Fel vid AI-anrop: {event.get('error')}")
                    return False

        if accumulated:
            add_message_to_chat("assistant", accumulated)
            return True
        return False
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Fel vid AI-anrop: {str(e)}")
        return False

# HJÄLPFUNKTIONER - PROMPTS & EXEMPEL
#TODO - flytta ut prompt grejer till en egen prompt.py och här ska vi bara anropa funktionen från prompt.py
def get_system_prompt():
    selected_saved_prompt = st.session_state.get("selected_saved_prompt", "Ingen prompt vald")
    
    if selected_saved_prompt != "Ingen prompt vald" and selected_saved_prompt in st.session_state.saved_prompts:
        return st.session_state.saved_prompts[selected_saved_prompt]['content']
    else:
        base = build_system_prompt(
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

# INITIERING - API-KEY & KONFIGURATION
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("API-nyckel saknas. Lägg till OPENAI_API_KEY i .env och starta om.")
    st.stop()

st.set_page_config(page_title="AI-chat", layout="wide")


memory = MemoryManager()
llm_handler = LLMHandler()

# INITIERING - DATABAS & STATE
init_session_state()

# SIDOPANEL - INSTÄLLNINGAR & KONFIGURATION
with st.sidebar:    
    st.header("Modellinställningar")
    st.toggle(
        "Mörkt läge",
        value=st.session_state.get("dark_mode", True),
        key='dark_mode',
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

    st.markdown("---")
    st.subheader("Konversationer")
    
    # ------------------------------------------------------------------------------------------------
    #TODO - spara undan sånt här till funktioner i en annan fil eller klass
    #TODO - skapa en debugpanel.py och flytta ut alla debug-funktioner från main.py till denna fil istället
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
    st.subheader("Debug Panel")

    tab1, tab2, tab3 = st.tabs(["📊 Debug Info", "💬 Feedback", "⚙️ Åtgärder"])

    with tab1:
        latest_list = memory.get_latest_debug_info(limit=1)
        if latest_list:
            dbg = latest_list[-1]
            st.caption("Senaste anropsdata")

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
        else:
            st.write("Ingen debug-information ännu. Skicka ett meddelande för att se data.")

    with tab2:
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

    with tab3:
        if st.button("Rensa chatt"):
            try:
                delete_messages(st.session_state.db_conn, st.session_state.conversation_id)
                st.session_state.messages.clear()
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

        st.divider()
        st.markdown("**Exportera data:**")

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

# HUVUDINNEHÅLL - CHATT
st.title("Levent's AI Lärare", )
disable_get_tips = False

user_text = st.chat_input("Skriv ditt meddelande...")
if user_text:
    add_message_to_chat("user", user_text)

# Container som håller chattmeddelandena
with st.container():
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"{message['timestamp']}")
            if message["role"] == "assistant":
                # TODO - använd tummar eller stjärnor från streamlit med st.feedback - Spara ned till databasen (funkar ej just nu)
                col1, col2 = st.columns([1, 5])
                with col1:
                    thumbs = st.feedback("thumbs", key=f"fb_thumbs_{idx}")
                with col2:
                    stars = st.feedback("stars", key=f"fb_stars_{idx}")

                # TODO - Spara ned till databasen (funkar ej just nu)
                if thumbs is not None and not st.session_state.get(f"fb_thumbs_saved_{idx}", False):
                    rating = "up" if thumbs == 1 else "down"
                    save_feedback(
                        st.session_state.db_conn,
                        conversation_id=st.session_state.conversation_id,
                        message_index=idx,
                        role=message.get("role", "assistant"),
                        rating=rating,
                        reason="",
                        message_content=message.get("content", "")
                    )
                    st.session_state[f"fb_thumbs_saved_{idx}"] = True
                    st.toast("✅ Tack för din feedback!")

                # TODO - Spara ned till databasen (funkar ej just nu)
                if stars is not None and not st.session_state.get(f"fb_stars_saved_{idx}", False):
                    save_feedback(
                        st.session_state.db_conn,
                        conversation_id=st.session_state.conversation_id,
                        message_index=idx,
                        role=message.get("role", "assistant"),
                        rating=f"{stars+1}_stars",
                        reason="",
                        message_content=message.get("content", "")
                    )
                    st.session_state[f"fb_stars_saved_{idx}"] = True
                    st.toast(f"✅ {stars+1} stjärnor!")

    if user_text:
        handle_llm_request(model, temp)