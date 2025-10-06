import streamlit as st
import os
import json
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

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("Skriv ditt meddelande här..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        memory.add_message("user", prompt)

        try:
            conversation_history = memory.get_conversation_history()
            response, debug_info = llm_handler.invoke(conversation_history)

            memory.add_message("assistant", response.content)
            memory.add_debug_info(debug_info)

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
        st.write("Debug-data mottagen:")
        st.json(dbg)
    else:
        st.write("Ingen debug-information ännu. Skicka ett meddelande för att se data.")

    if st.button("Rensa chatt"):
        st.session_state.messages.clear()
        st.session_state.debug_info = []
        memory.clear_messages()
        memory.clear_debug_info()
        st.success("Chatt rensad!")

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
