# IMPORTER
import uuid
import streamlit as st
from feedback_db import get_all_conversations, load_messages, delete_conversation

# SIDOPANEL - KONVERSATIONER

def render_conversations_sidebar(db_conn) -> None:
    st.subheader("Konversationer")
    try:
        conversations = get_all_conversations(db_conn)
        if conversations:
            conv_options = [f"{conv['id'][:8]}... ({conv['updated_at'][:10]})" for conv in conversations]
            conv_options.insert(0, "Ny konversation")
            selected_conv = st.selectbox("Välj konversation:", conv_options, key="conv_selector")

            if selected_conv != "Ny konversation":
                selected_id = conversations[conv_options.index(selected_conv) - 1]["id"]
                if st.button("Ladda konversation", key="load_conv"):
                    st.session_state.conversation_id = selected_id
                    messages = load_messages(db_conn, selected_id)
                    st.session_state.messages = messages if messages else []
                    st.rerun()
                if st.button("Ta bort konversation", key="delete_conv"):
                    delete_conversation(db_conn, selected_id)
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
