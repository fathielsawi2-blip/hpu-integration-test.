import os
import sqlite3
from datetime import datetime
import streamlit as st

from hpu_core import HPUOrchestrator, build_provider_client, call_provider

st.set_page_config(page_title="HPU Integration Manager Test", page_icon="🧠", layout="wide")

DB_PATH = "hpu_integration_test.db"

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                instruction TEXT NOT NULL,
                output TEXT NOT NULL
            )
        """)

def save_generation(provider, model, instruction, output):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO generations (created_at, provider, model, instruction, output) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), provider, model, instruction, output)
        )

def get_history():
    with sqlite3.connect(DB_PATH) as con:
        return con.execute(
            "SELECT created_at, provider, model, instruction, output FROM generations ORDER BY id DESC LIMIT 30"
        ).fetchall()

init_db()

st.title("🧠 HPU — Native AI Integration Test")
st.caption("A separate test environment for connecting AI providers directly to HPU through their APIs.")

with st.sidebar:
    st.header("HPU Provider Gateway")
    provider = st.selectbox("AI provider", ["OpenAI", "Anthropic (Claude)"])
    if provider == "OpenAI":
        api_key = st.text_input(
            "OpenAI API key",
            value=st.session_state.get("openai_key", ""),
            type="password",
            help="Use an API key from platform.openai.com. This is separate from a ChatGPT subscription."
        )
        st.session_state["openai_key"] = api_key
        model = st.text_input("Model ID", value=st.session_state.get("openai_model", "gpt-4.1-mini"))
        st.session_state["openai_model"] = model
    else:
        api_key = st.text_input(
            "Anthropic API key",
            value=st.session_state.get("anthropic_key", ""),
            type="password",
            help="Use an API key from console.anthropic.com. This is separate from a Claude subscription."
        )
        st.session_state["anthropic_key"] = api_key
        model = st.text_input("Model ID", value=st.session_state.get("anthropic_model", "claude-sonnet-4-5"))
        st.session_state["anthropic_model"] = model

    st.caption("Keys entered here stay in this Streamlit session's memory. They are not written to the app database. For a permanent deployment, use Streamlit Secrets.")
    test_connection = st.button("Test API connection", use_container_width=True)

if test_connection:
    if not api_key.strip():
        st.error("Enter the provider API key first.")
    else:
        try:
            client = build_provider_client(provider, api_key.strip())
            with st.spinner(f"Testing {provider} connection..."):
                answer = call_provider(
                    provider=provider,
                    client=client,
                    model=model.strip(),
                    system_prompt="You are an API connection test. Reply with exactly: HPU connection successful.",
                    user_prompt="Confirm the connection."
                )
            st.success(f"{provider} API responded successfully.")
            st.code(answer)
        except Exception as exc:
            st.error("The API connection failed. Check the key, model ID, provider account billing and API access.")
            st.exception(exc)

tab_generate, tab_history, tab_arch = st.tabs(["Generator", "Generation history", "How HPU works"])

with tab_generate:
    st.subheader("Natural-language production")
    st.write("Give HPU an instruction. HPU prepares the request, sends it to the selected AI provider, then checks that a response was returned.")
    task_type = st.selectbox(
        "What are you creating?",
        ["LinkedIn post", "Professional article", "Diagram (Mermaid)", "Infographic brief", "Video script", "Custom"]
    )
    language = st.selectbox("Language", ["English", "Arabic", "Arabic and English"])
    tone = st.selectbox("Tone", ["Executive", "Analytical", "Educational", "Conversational", "Persuasive", "Custom"])
    context = st.text_area(
        "Context or source information (optional)",
        placeholder="Add facts, experience, notes or source material. HPU will pass this to the selected AI."
    )
    instruction = st.text_area(
        "Your instruction",
        height=160,
        placeholder="Example: Write a LinkedIn post explaining why communication performance should be measured by behavioural change, not impressions alone. Use an executive tone. Do not invent statistics."
    )
    col1, col2 = st.columns([1, 3])
    with col1:
        generate = st.button("Generate with HPU", type="primary", use_container_width=True)
    with col2:
        st.caption(f"Selected provider: {provider} · Model: {model}")

    if generate:
        if not api_key.strip():
            st.error("Add the selected provider's API key in the sidebar first.")
        elif not instruction.strip():
            st.warning("Write an instruction first.")
        else:
            hpu = HPUOrchestrator()
            prepared_prompt = hpu.prepare_prompt(
                task_type=task_type,
                language=language,
                tone=tone,
                context=context,
                user_instruction=instruction
            )
            try:
                client = build_provider_client(provider, api_key.strip())
                with st.spinner(f"HPU is directing {provider}..."):
                    output = call_provider(
                        provider=provider,
                        client=client,
                        model=model.strip(),
                        system_prompt=hpu.system_instruction(),
                        user_prompt=prepared_prompt
                    )
                review = hpu.review_output(output)
                st.session_state["latest_output"] = output
                st.session_state["latest_review"] = review
                st.session_state["latest_instruction"] = instruction
                st.session_state["latest_provider"] = provider
                st.session_state["latest_model"] = model
                save_generation(provider, model, instruction, output)
                st.success("Generation completed.")
            except Exception as exc:
                st.error("Generation failed. Check your API key, model ID, account billing and provider access.")
                st.exception(exc)

    if st.session_state.get("latest_output"):
        st.divider()
        st.subheader("Generated result")
        st.markdown(st.session_state["latest_output"])
        st.caption("HPU output check: " + st.session_state.get("latest_review", ""))
        st.download_button(
            "Download result as Markdown",
            data=st.session_state["latest_output"],
            file_name="hpu_generated_output.md",
            mime="text/markdown"
        )
        st.subheader("Direct revision")
        revision = st.text_area(
            "Tell HPU what to change",
            placeholder="Example: Make the opening sharper, remove generic wording and use a more specific professional argument."
        )
        if st.button("Revise using HPU"):
            if not revision.strip():
                st.warning("Enter your revision instruction.")
            else:
                revision_prompt = (
                    "Revise the previous output according to the user's new instruction.\n\n"
                    f"PREVIOUS OUTPUT:\n{st.session_state['latest_output']}\n\n"
                    f"REVISION INSTRUCTION:\n{revision}\n\n"
                    "Return the revised output only. Do not invent facts."
                )
                try:
                    client = build_provider_client(provider, api_key.strip())
                    with st.spinner("HPU is directing the revision..."):
                        revised = call_provider(
                            provider=provider,
                            client=client,
                            model=model.strip(),
                            system_prompt=HPUOrchestrator().system_instruction(),
                            user_prompt=revision_prompt
                        )
                    st.session_state["latest_output"] = revised
                    st.session_state["latest_review"] = HPUOrchestrator().review_output(revised)
                    save_generation(provider, model, revision, revised)
                    st.success("Revision completed.")
                    st.rerun()
                except Exception as exc:
                    st.error("Revision failed. Check the selected provider and API key.")
                    st.exception(exc)

with tab_history:
    st.subheader("Recent generations")
    rows = get_history()
    if not rows:
        st.info("No generations saved yet.")
    else:
        for created_at, saved_provider, saved_model, saved_instruction, saved_output in rows:
            with st.expander(f"{created_at} · {saved_provider} · {saved_model}"):
                st.markdown("**Instruction**")
                st.write(saved_instruction)
                st.markdown("**Output**")
                st.markdown(saved_output)

with tab_arch:
    st.subheader("The test architecture")
    st.markdown("""
**HPU Core**
- Receives your natural-language instruction.
- Structures the task with format, language, tone and supplied context.
- Directs the selected provider through its official API.
- Checks that a non-empty response was returned.
- Stores the request and output in the test history.

**Provider adapters**
- OpenAI: direct API call using the OpenAI Python SDK and Responses API.
- Anthropic: direct API call using the Anthropic Python SDK and Messages API.

**Important boundaries**
- This test proves direct AI-provider API access; it does not yet connect social accounts or third-party business applications.
- It does not install connectors inside ChatGPT or Claude.
- HPU's current output review is a basic technical check, not a validated quality-scoring methodology.
- API use is billed by the provider separately from ChatGPT or Claude subscriptions.
- API keys entered in the sidebar are held in Streamlit session memory. Use Streamlit Secrets for a persistent deployment, and never commit keys to GitHub.
""")
