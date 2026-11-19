from openai import OpenAI
from anthropic import Anthropic

class HPUOrchestrator:
    """Small test implementation of HPU's provider-independent task layer."""

    def system_instruction(self):
        return (
            "You are an AI production engine operating under HPU direction. "
            "Follow the user's task, format, language and tone. Treat supplied "
            "context as source material, not permission to invent facts. "
            "Do not fabricate statistics, quotations, credentials, dates or "
            "achievements. If information is missing, say so. Produce the "
            "requested output directly and clearly."
        )

    def prepare_prompt(self, task_type, language, tone, context, user_instruction):
        return f"""
HPU TASK BRIEF
Output type: {task_type}
Language: {language}
Tone: {tone}

SOURCE CONTEXT:
{context.strip() if context.strip() else "No additional source context supplied."}

USER INSTRUCTION:
{user_instruction.strip()}

SPECIAL FORMAT RULES:
- If the requested output is a Diagram (Mermaid), return valid Mermaid code in a fenced mermaid block and a short explanation.
- If the requested output is an Infographic brief, provide a visual hierarchy, key messages, layout, and image-generation brief. Do not claim an image file was generated.
- Respect the user's constraints and do not add unsupported facts.
"""

    def review_output(self, output):
        if not output or not output.strip():
            return "No output returned."
        words = len(output.split())
        if words < 8:
            return "Response received; unusually short, so review it."
        return f"Response received ({words} words). Basic non-empty output check passed; human review is still required."


def build_provider_client(provider, api_key):
    if provider == "OpenAI":
        return OpenAI(api_key=api_key)
    if provider == "Anthropic (Claude)":
        return Anthropic(api_key=api_key)
    raise ValueError("Unsupported provider")


def call_provider(provider, client, model, system_prompt, user_prompt):
    if not model:
        raise ValueError("Enter a model ID.")
    if provider == "OpenAI":
        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=user_prompt
        )
        return response.output_text or ""
    if provider == "Anthropic (Claude)":
        response = client.messages.create(
            model=model,
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return "\n".join(
            block.text for block in response.content
            if getattr(block, "type", None) == "text"
        )
    raise ValueError("Unsupported provider")
