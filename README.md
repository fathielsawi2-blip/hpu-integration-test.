# HPU Native AI Integration — Test App

A separate Streamlit test app for direct API connections from HPU to OpenAI and Anthropic Claude.

## Run locally
1. Install Python 3.10 or newer.
2. Run `pip install -r requirements.txt`.
3. Run `streamlit run app.py`.
4. Enter an API key in the sidebar, select a model ID, and click **Test API connection**.
5. Open Generator, enter an instruction, and click **Generate with HPU**.

## Deploy on Streamlit Community Cloud
1. Create a NEW GitHub repository for this test (recommended, so the existing Dr. Alaa app is untouched).
2. Upload `app.py`, `hpu_core.py`, and `requirements.txt`.
3. Deploy `app.py` on Streamlit Community Cloud.
4. Enter API keys in the sidebar for this temporary test.

## API keys
- OpenAI API keys: https://platform.openai.com/api-keys
- Anthropic API keys: https://console.anthropic.com/

API billing is separate from ChatGPT and Claude subscriptions. The app does not include API credits.

## Security
The sidebar key fields use password inputs and keep values in Streamlit session state. For longer-term use, configure keys in Streamlit Secrets. Never put API keys in source code, GitHub commits, screenshots, or shared files.

Example Streamlit Secrets:
```toml
OPENAI_API_KEY = "your-openai-key"
ANTHROPIC_API_KEY = "your-anthropic-key"
```

This is a test integration layer, not the complete commercial HPU platform. The output review is a basic technical check, not a validated HPU measurement methodology. Social-media integrations, OAuth account connections, image generation, and publishing are not included in this test build.
