import os
import time
from groq import Groq

class GroqLLM:
    def __init__(self, model_names=None):
        if model_names is None:
            # A list of known good, supported models as of June 2026
            model_names = [
                "llama-3.3-70b-versatile",                # Replacement for old 70b
                "meta-llama/llama-4-scout-17b-16e-instruct", # New Llama 4 model
                "llama-3.1-8b-instant"                    # A fast, stable smaller model
            ]
        self.model_names = model_names
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found.")
        self.client = Groq(api_key=api_key)

    def __call__(self, prompt):
        last_error = None

        # Try your predefined list of models first
        for model_name in self.model_names:
            try:
                print(f"Attempting with model: {model_name}") # Optional: for debugging
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_name,
                    temperature=0.7,
                    max_tokens=1024,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                last_error = e
                print(f"Model {model_name} failed: {e}")
                time.sleep(0.5)
                continue

        # NUCLEAR OPTION: If all predefined models fail, get ANY active model
        print("All predefined models failed. Attempting to fetch ANY active model from Groq API...")
        try:
            # Fetch the list of all active models from Groq
            all_models = self.client.models.list()
            if all_models.data:
                # Pick the first available active model
                fallback_model_id = all_models.data[0].id
                print(f"Attempting fallback with ANY active model: {fallback_model_id}")
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=fallback_model_id,
                    temperature=0.7,
                    max_tokens=1024,
                )
                return chat_completion.choices[0].message.content
            else:
                return f"Could not find any active models. Last error: {last_error}"
        except Exception as e:
            return f"Failed to fetch models or generate response. Last error: {last_error} | Fallback error: {e}"