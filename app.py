# Importera nödvändiga bibliotek
import streamlit as st
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Importera våra egna moduler
from config import Config
from memory_manager import MemoryManager
from llm_handler import LLMHandler

# Ladda miljövariabler och konfiguration
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Konfigurera Streamlit-appen
st.set_page_config(page_title="AI-chat", layout="wide")
st.title("AI-chat med debugpanel")

# Initiera minneshanteraren och LLM-hanteraren
memory = MemoryManager()
llm_handler = LLMHandler()

# Synkronisera minneshanteraren med session state
if "messages" not in st.session_state:
    st.session_state.messages = memory.messages

if "debug_info" not in st.session_state:
    st.session_state.debug_info = memory.debug_info

# Skapa layout med två kolumner
col1, col2 = st.columns([2, 1])

# Vänster kolumn - Chattgränssnitt
with col1:
    st.subheader("Chat")
    
    # Visa befintliga meddelanden
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Inputfält för användaren
    if prompt := st.chat_input("Skriv ditt meddelande här..."):
        # Lägg till användarmeddelande i session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Lägg till användarmeddelande i minneshanteraren
        memory.add_message("user", prompt)
        
        # Hämta AI-svar
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

# Höger kolumn - Debug-panel och kontroller
with col2:
    st.subheader("Debug Panel")
    st.write("Debug-informationen kommer här...")
    
    # Knappar för att hantera chatten
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
            st.warning("Inga meddelanden att exportera")