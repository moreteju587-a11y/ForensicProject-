import requests

API_KEY = "AIzaSyAAzxonYDWKdgbSMBfnyLe_ph4JtCfug9A"

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Say hello"
                }
            ]
        }
    ]
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print(response.text)