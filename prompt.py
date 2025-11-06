# IMPORTER
from typing import Dict, Optional

# PROMPT-BUILDER - SYSTEMPROMPTS
def build_system_prompt(mode: str, subject: str, difficulty: str) -> str:
    mode = mode or "Lärläge"
    subject = subject or "Allmänt"
    difficulty = difficulty or "Medel"

    base = (
        f"Ämne: {subject}. Nivå: {difficulty}."
        f"Svara på svenska och håll dig konkret och hjälpsam"

    )

    if mode == "Lärläge":
        style = (
            "Du är en pedagogisk handledare."
            "Ge korta, begripliga förklaringar och 1-2 enkla exempel."
            "Belys nyckelgrepp tydligt."
        )

    else:
        style = (
            "Du är en coach."
            "Ge 1-3 konkreta övningar med tydliga steg."
            "Lägg till kort återkopplingstips efter varje övning."
        )

    return f"{base} {style}"

# PROMPT-SELECTOR - SYSTEMPROMPT MED FEEDBACK
def get_system_prompt(
    selected_saved_prompt: str = "Ingen prompt vald",
    saved_prompts: Dict = None,
    subject: str = "Programmering",
    difficulty: str = "Medel",
    feedback_summary: Optional[Dict] = None
) -> str:
    saved_prompts = saved_prompts or {}
    
    if selected_saved_prompt != "Ingen prompt vald" and selected_saved_prompt in saved_prompts:
        return saved_prompts[selected_saved_prompt]['content']
    else:
        base = build_system_prompt(mode="Lärläge", subject=subject, difficulty=difficulty)
        if feedback_summary:
            if feedback_summary.get("down", 0) > feedback_summary.get("up", 0):
                base += " Var extra tydlig, konkret och undvik vaga formuleringar."
            elif feedback_summary.get("up", 0) > 0:
                base += " Behåll den tydliga och hjälpsamma tonen."
        return base

