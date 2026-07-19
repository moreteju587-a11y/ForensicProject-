import requests

API_KEY = "AIzaSyAAzxonYDWKdgbSMBfnyLe_ph4JtCfug9A"

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={API_KEY}"

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Generate a realistic passport-style portrait of a man with short black hair, brown eyes, oval face."
                }
            ]
        }
    ]
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print(response.text)