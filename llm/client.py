import os
from typing import List, Dict, Any, Optional

from anthropic import Anthropic
from groq import Groq

from core.logging_config import setup_logging

logger = setup_logging()


class LLMProvider:
    def generate_answer(self, query: str, context: str) -> str:
        raise NotImplementedError

class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_answer(self, query: str, context: str) -> str:
        prompt = f"""
You are a helpful assistant. Use the following pieces of retrieved context to answer the user's question.
1. If the context contains the answer, use three sentences maximum and keep it concise.
2. If the context DOES NOT contain the answer or is irrelevant, you MUST strictly answer: "There is no file found containing information on this topic."
3. Do not use your own knowledge outside of the context provided.

Context:
{context}

Question: {query}

Answer:
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        return response.choices[0].message.content

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate_answer(self, query: str, context: str) -> str:
        prompt = f"""
You are a helpful assistant. Use the following pieces of retrieved context to answer the user's question.
1. If the context contains the answer, use three sentences maximum and keep it concise.
2. If the context DOES NOT contain the answer or is irrelevant, you MUST strictly answer: "There is no file found containing information on this topic."
3. Do not use your own knowledge outside of the context provided.

Context:
{context}

Question: {query}

Answer:
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        return response.content[0].text

def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "groq").lower()

    logger.info(f"Using LLM provider: {provider_name}")

    if provider_name == "groq":
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not set")

        return GroqProvider(api_key)

    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")

        return AnthropicProvider(api_key)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")