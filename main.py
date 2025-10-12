
import os
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from config import Config
from memory_manager import MemoryManager
from llm_handler import LLMHandler

# ===== Miljö & startskydd =====
# Miljö/konfiguration – läs API-nyckel och avbryt snyggt om den saknas
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("API-nyckel saknas. Lägg till OPENAI_API_KEY i .env och starta om.")
    st.stop()

# ===== UI-setup (titel & layout) =====
# Bas-UI – titel och sidlayout
st.set_page_config(page_title="AI-chat", layout="wide")
st.title("AI-chat med debugpanel")

# ===== Init av tjänster =====
# Init – minneshanterare och LLM-klient
memory = MemoryManager()
llm_handler = LLMHandler()

# ===== Session state =====
# Session state – säkerställ strukturer som överlever omritningar
if "messages" not in st.session_state:
    st.session_state.messages = []

if "debug_info" not in st.session_state:
    st.session_state.debug_info = []

# ===== Synkronisering av historik till minneshanterare =====
# Synkronisering – bygg upp minnet från tidigare meddelanden i sessionen
for message in st.session_state.messages:
    memory.add_message(message["role"], message["content"])

# ===== Sidofält (inställningar) =====
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
    

# ===== Layout (chat + debug) =====
# Layout – två kolumner: vänster (chat), höger (debug/kontroller)
col1, col2 = st.columns([2, 1])

with col1:
    # ===== Chat (UI) =====
    # Vänster kolumn – chattgränssnitt
    st.subheader("Chat")
    
    # Rendera historik – visa alla tidigare meddelanden i ordning med tidsstämplar
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # Visa tidsstämpel om den finns (från MemoryManager)
            if "timestamp" in message:
                st.caption(f"📅 {message['timestamp']}")

    # ===== Inmatning (form) =====
    # Inmatning – form med Skicka-knapp och Enter-stöd
    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_input("Skriv ditt meddelande…", value="")
        submitted = st.form_submit_button("Skicka")

    # ===== Sändningskedja (uppdatera historik → anropa LLM → visa svar) =====
    # Hantera skick – uppdatera historik, anropa LLM, visa svar
    if submitted and user_text.strip():
        # Lägg till meddelande med tidsstämpel
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user", 
            "content": user_text,
            "timestamp": timestamp
        })
        with st.chat_message("user"):
            st.write(user_text)

        memory.add_message("user", user_text)

        # Sätt flagga för att spåra om anropet ska avbrytas
        st.session_state.abort_requested = False
        
        # Skapa en container för spinner och avbryt-knapp
        spinner_container = st.empty()
        abort_container = st.empty()
        
        with spinner_container:
            with st.spinner("Tänker..."):
                try:
                    # Uppdatera modellinställningar
                    llm_handler.update_model_settings(
                        model_name=model,
                        temperature=temp
                    )

                    # Hämta konversationshistorik
                    conversation_history = memory.get_conversation_history()
                    
                    # Visa avbryt-knapp under anropet
                    with abort_container:
                        if st.button("Avbryt anrop", key="abort_button"):
                            st.session_state.abort_requested = True
                            st.warning("Avbryter anrop...")
                            st.stop()  # Stoppa execution här
                    
                    # Anropa LLM (detta kan ta tid)
                    response, debug_info = llm_handler.invoke(conversation_history)
                    
                    # Kontrollera om anropet avbröts
                    if st.session_state.get("abort_requested", False):
                        st.warning("Anrop avbrutet av användaren.")
                        st.stop()
                    
                    # Lägg till svar i minnet
                    memory.add_message("assistant", response.content)
                    memory.add_debug_info(debug_info)

                    # Lägg till AI-svar med tidsstämpel i session_state
                    ai_timestamp = datetime.now().strftime("%H:%M:%S")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.content,
                        "timestamp": ai_timestamp
                    })

                    # Visa AI-svaret
                    with st.chat_message("assistant"):
                        st.write(response.content)
                    
                    # Rensa avbryt-knappen efter framgång
                    abort_container.empty()

                except Exception as e:
                    # Rensa avbryt-knappen vid fel
                    abort_container.empty()
                    
                    with st.chat_message("assistant"):
                        st.error(f"Fel vid AI-anrop: {str(e)}")

with col2:
    # ===== Debugpanel & åtgärder =====
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
            # 1) Snabb översikt - viktigaste info först (modell, temp, tider, status)
            st.markdown("### 📊 Snabb översikt")
            st.markdown(f"• **Modell:** `{dbg.get('model', 'okänt')}`")
            st.markdown(f"• **Temperatur:** `{dbg.get('temperature', 'okänt')}`")
            st.markdown(f"• **Meddelanden:** `{dbg.get('messages_count', 'okänt')}`")
            
            # Svarstid med färgkodning (grön = snabb, röd = långsam)
            if "response_time" in dbg:
                response_time = dbg['response_time']
                if response_time < 2.0:
                    color = "🟢"
                elif response_time < 5.0:
                    color = "🟡"
                else:
                    color = "🔴"
                st.markdown(f"• **Svarstid:** {color} `{round(response_time, 3)}s`")
            
            # Status-indikator (framgång/misslyckande)
            if dbg.get("success", False):
                st.markdown("• **Status:** ✅ Framgång")
            else:
                st.markdown("• **Status:** ❌ Misslyckande")
                if "error" in dbg:
                    st.markdown(f"• **Fel:** `{dbg['error']}`")

            # 2) Token-statistik (om tillgänglig) - viktigt för kostnadskontroll
            token_usage = dbg.get("token_usage")
            if isinstance(token_usage, dict) and any(v != "N/A" for v in token_usage.values()):
                st.markdown("### 🔢 Token-användning")
                st.markdown(f"• **Prompt-tokens:** `{token_usage.get('prompt_tokens', 'N/A')}`")
                st.markdown(f"• **Completion-tokens:** `{token_usage.get('completion_tokens', 'N/A')}`")
                st.markdown(f"• **Totalt:** `{token_usage.get('total_tokens', 'N/A')}`")
                
                # Beräkna ungefärlig kostnad (ungefärliga siffror för GPT-4o-mini)
                if token_usage.get('total_tokens') != "N/A":
                    total = token_usage.get('total_tokens', 0)
                    if isinstance(total, int):
                        # Ungefärlig kostnad: $0.00015 per 1K tokens för GPT-4o-mini
                        cost = (total / 1000) * 0.00015
                        st.markdown(f"• **Uppskattad kostnad:** ~${cost:.6f}")

            # 3) Payload - vad som faktiskt skickades till LLM (kritiskt för debugging)
            payload = dbg.get("payload")
            if isinstance(payload, dict):
                st.markdown("### 📤 Payload (vad som skickades till LLM)")
                st.markdown("**Meddelanden som skickades:**")
                for i, msg in enumerate(payload.get("messages", []), 1):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    # Trunkera långa meddelanden för läsbarhet
                    if len(content) > 200:
                        content = content[:200] + "..."
                    st.markdown(f"  **{i}.** `{role}`: {content}")
                
                # Visa full payload som JSON för teknisk detalj
                with st.expander("Visa fullständig payload (JSON)"):
                    st.json(payload)

            # 4) Rå output - vad som kom tillbaka från LLM innan efterbearbetning
            raw_response = dbg.get("raw_response")
            if raw_response:
                st.markdown("### 📥 Rå output från LLM")
                st.markdown("**Innan efterbearbetning:**")
                # Trunkera för att undvika jättelånga rutor
                raw_text = str(raw_response)
                if len(raw_text) > 1000:
                    st.code(raw_text[:1000] + "\n... (trunkerad)")
                    st.caption("💡 Output trunkerad för läsbarhet. Full output finns i JSON nedan.")
                else:
                    st.code(raw_text)
                
                # Visa full rå output som JSON
                with st.expander("Visa fullständig rå output (JSON)"):
                    st.json({"raw_response": raw_response})

            # 5) Fullständig debug-data (för avancerad felsökning)
            with st.expander("Visa all debug-data (JSON)"):
                st.json(dbg)
    else:
        # Ingen debug ännu – troligen inget anrop gjort eller ingen metadata
        st.write("Ingen debug-information ännu. Skicka ett meddelande för att se data.")

    # ===== Åtgärder =====
    # Åtgärder – rensa session/minne och visa kvittens
    if st.button("Rensa chatt"):
        st.session_state.messages.clear()
        st.session_state.debug_info = []
        memory.clear_messages()
        memory.clear_debug_info()
        st.success("Chatt rensad!")
    
    # Avbryt-knapp (för pågående anrop)
    if st.button("Avbryt pågående anrop"):
        if st.session_state.get("abort_requested", False):
            st.info("Inget pågående anrop att avbryta.")
        else:
            st.session_state.abort_requested = True
            st.warning("Avbryt-signal skickad. Anropet kommer att stoppas vid nästa kontroll.")

    # ===== Export (JSON) =====
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

    # ===== Export (TXT) =====
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
