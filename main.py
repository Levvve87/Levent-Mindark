# IMPORTER
import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from memory_manager import MemoryManager
from llm_handler import LLMHandler
from ui_conversations import render_conversations_sidebar
from debugpanel import render_debug_panel
from feedback_db import init_db, save_feedback, get_feedback_summary, save_message, load_messages, create_or_update_conversation, delete_messages, get_all_prompts
from prompt import get_system_prompt as get_system_prompt_from_prompt
import uuid

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

    st.session_state.setdefault("subject", "Programmering")
    st.session_state.setdefault("difficulty", "Medel")
    
    if "saved_prompts" not in st.session_state:
        try:
            prompts = get_all_prompts(st.session_state.db_conn)
            st.session_state.saved_prompts = {p["name"]: {"content": p["content"], "description": p["description"]} for p in prompts}
        except Exception:
            st.session_state.saved_prompts = {}

# HJÄLPFUNKTIONER - LLM ANROP
def handle_llm_request(model_name: str, temperature: float, system_message: str = None):
    st.session_state.abort_requested = False
    try:
        conversation_history = get_conversation_history()
        system_prompt_text = system_message or get_system_prompt()

        with st.chat_message("assistant"):
            placeholder = st.empty()
            accumulated = ""
            for event in llm_handler.stream_with_settings(
                model_name=model_name,
                temperature=temperature,
                messages=conversation_history,
                system_message=system_prompt_text,
            ):
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
def get_system_prompt():
    selected_saved_prompt = st.session_state.get("selected_saved_prompt", "Ingen prompt vald")
    saved_prompts = st.session_state.get("saved_prompts", {})
    subject = st.session_state.get("subject", "Programmering")
    difficulty = st.session_state.get("difficulty", "Medel")
    
    feedback_summary = None
    try:
        feedback_summary = get_feedback_summary(st.session_state.db_conn)
    except Exception:
        pass
    
    return get_system_prompt_from_prompt(
        selected_saved_prompt=selected_saved_prompt,
        saved_prompts=saved_prompts,
        subject=subject,
        difficulty=difficulty,
        feedback_summary=feedback_summary
    )

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
    render_conversations_sidebar(st.session_state.db_conn)
    st.markdown("---")
    render_debug_panel(memory, st.session_state.db_conn)

# HUVUDINNEHÅLL - CHATT
st.title("Levent's AI Lärare")

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
                col1, col2 = st.columns([1, 5])
                with col1:
                    thumbs = st.feedback("thumbs", key=f"fb_thumbs_{idx}")
                with col2:
                    stars = st.feedback("stars", key=f"fb_stars_{idx}")

                if thumbs is not None and not st.session_state.get(f"fb_thumbs_saved_{idx}", False):
                    save_feedback(
                        st.session_state.db_conn,
                        conversation_id=st.session_state.conversation_id,
                        message_index=idx,
                        role=message.get("role", "assistant"),
                        rating_type="thumbs",
                        rating_value=1 if thumbs == 1 else -1,
                        reason="",
                        message_content=message.get("content", "")
                    )
                    st.session_state[f"fb_thumbs_saved_{idx}"] = True
                    st.toast("✅ Tack för din feedback!")

                if stars is not None and not st.session_state.get(f"fb_stars_saved_{idx}", False):
                    save_feedback(
                        st.session_state.db_conn,
                        conversation_id=st.session_state.conversation_id,
                        message_index=idx,
                        role=message.get("role", "assistant"),
                        rating_type="stars",
                        rating_value=stars + 1,
                        reason="",
                        message_content=message.get("content", "")
                    )
                    st.session_state[f"fb_stars_saved_{idx}"] = True
                    st.toast(f"✅ {stars+1} stjärnor!")

    if user_text:
        handle_llm_request(model, temp)