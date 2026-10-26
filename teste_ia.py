import requests
from dotenv import load_dotenv
import os

load_dotenv()

url = os.environ["IA_API_URL"]
key = os.environ["IA_API_KEY"]

resp = requests.post(
    url,
    json={
        "model": os.environ.get("IA_MODEL", "gemini-3.6-flash"),
        "messages": [{"role": "user", "content": "Diga apenas: funcionou"}],
        "temperature": 0.3,
        "max_tokens": 50
    },
    headers={"Authorization": f"Bearer {key}"},
    timeout=30
)

print("STATUS:", resp.status_code)
print("RESPOSTA:", resp.text[:500])