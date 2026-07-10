from groq import Groq
from src.config import settings
from src.services.llm.llm_interface import LLMInterface


class GroqProvider(LLMInterface):
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.model_name

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,   # deterministic, classification task
            max_tokens=512,
        )
        return response.choices[0].message.content