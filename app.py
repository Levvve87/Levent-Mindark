# Appens huvudfil: sätter upp UI, minne och LLM; visar även debug-info
import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from config import Config
from memory_manager import MemoryManager
from llm_handler import LLMHandler

# Miljö/konfiguration – läs API-nyckel och avbryt snyggt om den saknas
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("API-nyckel saknas. Lägg till OPENAI_API_KEY i .env och starta om.")
    st.stop()

# Bas-UI – titel och sidlayout
st.set_page_config(page_title="AI-chat", layout="wide")
st.title("AI-chat med debugpanel")

# Init – minneshanterare och LLM-klient
memory = MemoryManager()
llm_handler = LLMHandler()

# Session state – säkerställ strukturer som överlever omritningar
if "messages" not in st.session_state:
    st.session_state.messages = []

if "debug_info" not in st.session_state:
    st.session_state.debug_info = []

# Synkronisering – bygg upp minnet från tidigare meddelanden i sessionen
for message in st.session_state.messages:
    memory.add_message(message["role"], message["content"])

# Layout – två kolumner: vänster (chat), höger (debug/kontroller)
col1, col2 = st.columns([2, 1])

with col1:
    # Vänster kolumn – chattgränssnitt
    st.subheader("Chat")
    
    # Rendera historik – visa alla tidigare meddelanden i ordning
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Inmatning – hantera nytt meddelande och hämta svar från LLM
    if prompt := st.chat_input("Skriv ditt meddelande här..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        memory.add_message("user", prompt)

        # Visa laddningsindikator under AI-anropet
        with st.spinner("Tänker..."):
            try:
                # Hämta historik och anropa LLM
                conversation_history = memory.get_conversation_history()
                response, debug_info = llm_handler.invoke(conversation_history)

                # Spara AI-svar och debug
                memory.add_message("assistant", response.content)
                memory.add_debug_info(debug_info)

                # Visa AI-svaret
                with st.chat_message("assistant"):
                    st.write(response.content)

            except Exception as e:
                # Visa fel i chatten
                with st.chat_message("assistant"):
                    st.error(f"Fel vid AI-anrop: {str(e)}")

with col2:
    # Höger kolumn – debugpanel och åtgärdsknappar
    st.subheader("Debug Panel")

    latest_list = memory.get_latest_debug_info(limit=1)
    if latest_list:
        dbg = latest_list[-1]
        st.write("Debug-data mottagen:")
        st.json(dbg)
    else:
        st.write("Ingen debug-information ännu. Skicka ett meddelande för att se data.")

    # Åtgärder – rensa session/minne och visa kvittens
    if st.button("Rensa chatt"):
        st.session_state.messages.clear()
        st.session_state.debug_info = []
        memory.clear_messages()
        memory.clear_debug_info()
        st.success("Chatt rensad!")

    # Export – ladda ner historiken som JSON för analys/testning
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
