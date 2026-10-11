import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

GROQ_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
MODEL = "openai/gpt-oss-120b"
@app.route("/")
def home():
    return send_from_directory(".", "jarvisai.html")

def web_search(query):
if not TAVILY_KEY:
return ""

```
try:
    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 5
        },
        timeout=15
    )
    response.raise_for_status()
    results = response.json().get("results", [])

    return "\n\n".join(
        f"Başlık: {item.get('title', '')}\n"
        f"Bilgi: {item.get('content', '')}\n"
        f"Kaynak: {item.get('url', '')}"
        for item in results
    )[:12000]

except Exception:
    app.logger.exception("Web araması başarısız")
    return ""
```

@app.route("/chat", methods=["POST"])
def chat():
data = request.get_json(silent=True) or {}
message = str(data.get("message", "")).strip()
history = data.get("history", [])

```
if not message:
    return jsonify({"error": "Bir mesaj yazmalısın."}), 400

if not GROQ_KEY:
    return jsonify({
        "error": "GROQ_API_KEY Render ayarlarında eksik."
    }), 500

search_results = web_search(message)

system_prompt = (
    "Sen Efe Jarvis'sin. Türkçe, doğal ve anlaşılır cevap ver. "
    "Önceki mesajları dikkate al ve takip sorularını bağlamdan anla. "
    "Güncel sorularda web arama sonuçlarını kullan. "
    "Uygun olduğunda kaynak bağlantılarını belirt. "
    "Arama sonucu yoksa internette arama yaptığını iddia etme. "
    "Bilmediğin bilgileri uydurma."
)

if search_results:
    system_prompt += "\n\nWEB ARAMA SONUÇLARI:\n" + search_results
else:
    system_prompt += "\n\nBu soruya ait web arama sonucu alınamadı."

messages = [{"role": "system", "content": system_prompt}]

if isinstance(history, list):
    for item in history[-20:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({
                "role": role,
                "content": content[:4000]
            })

messages.append({"role": "user", "content": message})

try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": messages,
            "temperature": 0.5
        },
        timeout=60
    )

    if not response.ok:
        app.logger.error(
            "Groq HTTP %s: %s",
            response.status_code,
            response.text[:1000]
        )

        try:
            error_data = response.json()
            error_info = error_data.get("error", {})
            detail = (
                error_info.get("message", "Ayrıntı alınamadı.")
                if isinstance(error_info, dict)
                else str(error_info)
            )
        except (ValueError, AttributeError):
            detail = "Groq yanıtı okunamadı."

        return jsonify({
            "error": f"Groq HTTP {response.status_code}: {detail}"
        }), 502

    result = response.json()
    reply = result["choices"][0]["message"]["content"]

    return jsonify({
        "reply": reply or "Cevap oluşturulamadı."
    })

except Exception:
    app.logger.exception("Groq bağlantı hatası")
    return jsonify({
        "error": "Yapay zekâ bağlantısı başarısız oldu."
    }), 502
```

if **name** == "**main**":
app.run(
host="0.0.0.0",
port=int(os.environ.get("PORT", 5000)),
debug=False
)
