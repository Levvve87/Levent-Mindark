# IMPORTER
import json
import uuid
from datetime import datetime
import streamlit as st
from feedback_db import get_recent_feedback, export_feedback_json, export_feedback_csv, delete_messages, delete_all_feedback, delete_all_data
from config import Config

# SIDOPANEL - DEBUG PANEL

def render_debug_panel(memory, db_conn) -> None:
    st.subheader("Debug Panel")
    tab1, tab2, tab3 = st.tabs(["📊 Debug Info", "💬 Feedback", "⚙️ Åtgärder"])

    with tab1:
        latest_list = memory.get_latest_debug_info(limit=1)
        if latest_list:
            dbg = latest_list[-1]
            st.caption("Senaste anropsdata")

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
        else:
            st.write("Ingen debug-information ännu. Skicka ett meddelande för att se data.")

    with tab2:
        try:
            feedback_rows = get_recent_feedback(db_conn, limit=10)
            if feedback_rows:
                for row in feedback_rows:
                    ts = row[8] if len(row) > 8 else ""
                    rating_type = row[4] if len(row) > 4 else ""
                    rating_value = row[5] if len(row) > 5 else 0
                    reason = row[6] if len(row) > 6 else ""
                    
                    if rating_type == "thumbs":
                        rating_display = "👍" if rating_value == 1 else "👎"
                    elif rating_type == "stars":
                        rating_display = "⭐" * rating_value
                    else:
                        rating_display = "?"
                    
                    st.markdown(f"{rating_display} `{ts}` — {reason if reason else 'Ingen orsak angiven'}")
            else:
                st.caption("Ingen feedback än.")
        except Exception as e:
            st.caption(f"Kunde inte ladda feedback: {e}")

    with tab3:
        if st.button("Rensa chatt"):
            try:
                delete_messages(db_conn, st.session_state.conversation_id)
                st.session_state.messages.clear()
                memory.clear_debug_info()
                st.success("Chatt rensad!")
            except Exception as e:
                st.error(f"Kunde inte rensa chatt: {e}")

        if st.button("Avbryt pågående anrop"):
            if st.session_state.get("abort_requested", False):
                st.info("Inget pågående anrop att avbryta.")
            else:
                st.session_state.abort_requested = True
                st.warning("Avbryt-signal skickad. Anropet kommer att stoppas vid nästa kontroll.")

        st.divider()
        with st.expander("Avancerat: Rensa databas", expanded=False):
            if not Config.ENABLE_DANGEROUS_ACTIONS:
                st.info("Avancerade rensningsåtgärder är avstängda. Sätt ENABLE_DANGEROUS_ACTIONS=true i .env för att aktivera.")
            else:
                if "confirm_delete_feedback" not in st.session_state:
                    st.session_state.confirm_delete_feedback = False
                if "confirm_delete_all" not in st.session_state:
                    st.session_state.confirm_delete_all = False

                st.markdown("**Rensa all feedback**")
                if not st.session_state.confirm_delete_feedback:
                    if st.button("🗑️ Rensa all feedback", type="secondary"):
                        st.session_state.confirm_delete_feedback = True
                        st.rerun()
                else:
                    st.warning("⚠️ Detta kommer att radera ALL feedback permanent!")
                    confirm_text = st.text_input("Skriv DELETE för att bekräfta", key="confirm_text_feedback")
                    col1, col2 = st.columns(2)
                    with col1:
                        disabled = confirm_text != "DELETE"
                        if st.button("✅ Bekräfta", type="primary", disabled=disabled):
                            try:
                                delete_all_feedback(db_conn)
                                st.session_state.confirm_delete_feedback = False
                                st.success("All feedback har raderats!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Kunde inte radera feedback: {e}")
                    with col2:
                        if st.button("❌ Avbryt"):
                            st.session_state.confirm_delete_feedback = False
                            st.rerun()

                st.markdown("---")
                st.markdown("**Rensa ALL data**")
                if not st.session_state.confirm_delete_all:
                    if st.button("🗑️ Rensa ALL data", type="secondary"):
                        st.session_state.confirm_delete_all = True
                        st.rerun()
                else:
                    st.error("⚠️⚠️⚠️ VARNING: Detta kommer att radera ALLT permanent! ⚠️⚠️⚠️")
                    st.warning("Alla konversationer, meddelanden, feedback och prompts kommer att försvinna!")
                    confirm_text_all = st.text_input("Skriv DELETE för att bekräfta", key="confirm_text_all")
                    col1, col2 = st.columns(2)
                    with col1:
                        disabled = confirm_text_all != "DELETE"
                        if st.button("✅ Bekräfta radering", type="primary", disabled=disabled):
                            try:
                                delete_all_data(db_conn)
                                st.session_state.conversation_id = str(uuid.uuid4())
                                st.session_state.messages = []
                                st.session_state.confirm_delete_all = False
                                memory.clear_debug_info()
                                st.success("All data har raderats!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Kunde inte radera data: {e}")
                    with col2:
                        if st.button("❌ Avbryt"):
                            st.session_state.confirm_delete_all = False
                            st.rerun()

        st.divider()
        st.markdown("**Exportera data:**")

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
            if st.session_state.messages:
                result = []
                for msg in st.session_state.messages:
                    timestamp = msg.get("timestamp", "Okänt tid")
                    role = msg["role"].upper()
                    content = msg["content"]
                    result.append(f"[{timestamp}] {role}: {content}")
                txt_data = "\n".join(result)
                st.download_button(
                    label="Ladda ner chatt som TXT",
                    data=txt_data,
                    file_name=f"chatt_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt",
                )
            else:
                st.warning("Inga meddelanden att exportera.")

        if st.button("Exportera feedback-databas"):
            try:
                json_data = export_feedback_json(db_conn)
                st.download_button(
                    label="Ladda ner feedback som JSON",
                    data=json_data,
                    file_name=f"feedback_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json",
                    mime="application/json"
                )
                csv_data = export_feedback_csv(db_conn)
                st.download_button(
                    label="Ladda ner feedback som CSV",
                    data=csv_data,
                    file_name=f"feedback_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.warning(f"Kunde inte exportera feedback: {e}")

        if st.button("Exportera SQLite-databas"):
            try:
                with open("feedback.db", "rb") as f:
                    db_data = f.read()
                st.download_button(
                    label="Ladda ner feedback.db",
                    data=db_data,
                    file_name=f"feedback_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db",
                    mime="application/x-sqlite3"
                )
            except FileNotFoundError:
                st.warning("Databasfilen hittades inte.")
            except Exception as e:
                st.warning(f"Kunde inte exportera databas: {e}")
