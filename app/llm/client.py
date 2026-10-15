from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, MAX_TOKENS

client = OpenAI(api_key=OPENAI_API_KEY)


def chat(messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content
