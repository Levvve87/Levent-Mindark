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