
import os
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from config import Config
from memory_manager import MemoryManager
from llm_handler import LLMHandler

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("API-nyckel saknas. Lägg till OPENAI_API_KEY i .env och starta om.")
    st.stop()

st.set_page_config(page_title="AI-chat", layout="wide")
st.title("AI-chat med debugpanel")

memory = MemoryManager()
llm_handler = LLMHandler()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_info" not in st.session_state:
    st.session_state.debug_info = []

for message in st.session_state.messages:
    memory.add_message(message["role"], message["content"])

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

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"📅 {message['timestamp']}")

    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_input("Skriv ditt meddelande…", value="")
        submitted = st.form_submit_button("Skicka")

    if submitted and user_text.strip():
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": user_text,
            "timestamp": timestamp
        })
        with st.chat_message("user"):
            st.write(user_text)
        memory.add_message("user", user_text)
        st.session_state.abort_requested = False
        with st.spinner("Tänker..."):
            try:
                llm_handler.update_model_settings(model_name=model, temperature=temp)
                conversation_history = memory.get_conversation_history()
                if st.button("Avbryt anrop", key="abort_button"):
                    st.session_state.abort_requested = True
                    st.warning("Avbryter anrop...")
                    st.stop()
                response, debug_info = llm_handler.invoke(conversation_history)
                if st.session_state.get("abort_requested", False):
                    st.warning("Anrop avbrutet av användaren.")
                    st.stop()
                memory.add_message("assistant", response.content)
                memory.add_debug_info(debug_info)
                ai_timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.content,
                    "timestamp": ai_timestamp
                })
                with st.chat_message("assistant"):
                    st.write(response.content)
            except Exception as e:
                with st.chat_message("assistant"):
                    st.error(f"Fel vid AI-anrop: {str(e)}")

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
    if st.button("Rensa chatt"):
        st.session_state.messages.clear()
        st.session_state.debug_info = []
        memory.clear_messages()
        memory.clear_debug_info()
        st.success("Chatt rensad!")
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
        try:
            txt_data = memory.export_messages(format="txt")
            st.download_button(
                label="Ladda ner chatt som TXT",
                data=txt_data,
                file_name=f"chatt_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt",
            )
        except Exception as e:
            st.warning(f"Kunde inte exportera TXT: {e}")
