import streamlit as st
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI-chat", layout="wide")
st.title("AI-chat med debugpanel")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "debug_infor" not in st.session_state:
    st.session_state.debug_info = []

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
    
    with st.chat_message("assistant"):
        st.write("AI-svar kommer här...")

with col2:
    st.subheader("Debug Panel")
    st.write("Debug-informationen kommer här...")

if st.button("Rensa chatt"):
    st.session_state.messages.clear()
    st.session_state.debug_info = []
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