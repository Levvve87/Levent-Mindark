# Appens huvudfil: sätter upp UI, minne och LLM; visar även debug-info
# Övergripande översikt (SRP och struktur):
# - Start & miljö: Läser .env och validerar OPENAI_API_KEY, stoppar snyggt om den saknas
# - UI-setup: Sätter sidtitel/layout och huvudrubrik
# - Init av tjänster: Skapar MemoryManager (konversation/debug) och LLMHandler (modell/anrop)
# - Session state: Säkerställer messages/debug_info och synkar dem till MemoryManager
# - Sidofält (inställningar): Enkla kontroller för modell och temperatur (påverkar nästa anrop)
# - Chat-kolumn: Visar historik, samlar in nytt meddelande (form), och hanterar skick/anrop/svar
# - Debug-kolumn: Utfällbar panel med senaste debugdata (modell, tider, token, payload, rå-output)
# - Åtgärder: Rensa (nollställer historik/debug) och Exportera (nedladdning av JSON)
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

with st.sidebar:
    st.header("Modellinställningar")
    model = st.selectbox(
        "Modell",
        options=["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="Välj LLM‑modell som ska användas vid nästa anrop."
    )

    temp = st.slider(
        "Temperatur",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Lägre värde = mer fokuserade svar. Högre = mer kreativa svar."

    )
    

# Layout – två kolumner: vänster (chat), höger (debug/kontroller)
col1, col2 = st.columns([2, 1])

with col1:
    # Vänster kolumn – chattgränssnitt
    st.subheader("Chat")
    
    # Rendera historik – visa alla tidigare meddelanden i ordning
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Inmatning – form med Skicka-knapp och Enter-stöd
    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_input("Skriv ditt meddelande…", value="")
        submitted = st.form_submit_button("Skicka")

    # Hantera skick – uppdatera historik, anropa LLM, visa svar
    if submitted and user_text.strip():
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.write(user_text)

        memory.add_message("user", user_text)

        with st.spinner("Tänker..."):
            try:
                llm_handler.update_model_settings(
                    model_name=model,
                    temperature=temp
                )

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
    # Höger kolumn – debugpanel och åtgärdsknappar
    st.subheader("Debug Panel")

    # ---
    latest_list = memory.get_latest_debug_info(limit=1)  # Hämta senaste debugpost (lista, max 1 element)

    if latest_list:
        dbg = latest_list[-1]  # Sista elementet = senaste posten

        # Kort statusrad: förklara att detaljer finns i expander nedan.
        st.caption("Senaste anropsdata (fäll ut för mer detaljer).")

        # Expander minskar visuellt brus; detaljer visas bara vid behov.
        with st.expander("Visa detaljerad debug"):
            # 1) Visa hela debug-datat som JSON (full transparens vid felsökning)
            st.json(dbg)

            # 2) Lyft fram centrala fält separat för snabb översikt
            st.markdown(f"• Modell: `{dbg.get('model', 'okänt')}`")
            st.markdown(f"• Temperatur: `{dbg.get('temperature', 'okänt')}`")
            st.markdown(f"• Meddelanden i payload: `{dbg.get('messages_count', 'okänt')}`")

            # 3) Svarstid om tillgänglig
            if "response_time" in dbg:
                st.markdown(f"• Svarstid (s): `{round(dbg['response_time'], 3)}`")

            # 4) Tokenstatistik (om API rapporterar)
            token_usage = dbg.get("token_usage")
            if isinstance(token_usage, dict):
                st.markdown("• Tokenanvändning:")
                st.markdown(f"  - prompt_tokens: `{token_usage.get('prompt_tokens', 'N/A')}`")
                st.markdown(f"  - completion_tokens: `{token_usage.get('completion_tokens', 'N/A')}`")
                st.markdown(f"  - total_tokens: `{token_usage.get('total_tokens', 'N/A')}`")

            # 5) Payload som skickades (om tillgänglig)
            payload = dbg.get("payload")
            if isinstance(payload, dict):
                st.markdown("• Payload som skickades till LLM:")
                st.json(payload)

            # 6) Rå-output (trunkerad) om tillgänglig
            raw = dbg.get("raw_response") or dbg.get("raw_response_preview") or dbg.get("raw_response_text")
            if raw:
                st.markdown("• Rå-output (trunkerad):")
                st.code(str(raw)[:1200])
    else:
        # Ingen debug ännu – troligen inget anrop gjort eller ingen metadata
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
