
import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "openrouter/free"

@app.route("/")
def home():
    return send_from_directory(".", "jarvisai.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Bir mesaj yazmalısın."}), 400

    if not API_KEY:
        return jsonify({"error": "OpenRouter API anahtarı ayarlanmamış."}), 500

    messages = [{
        "role": "system",
        "content": (
            "Sen Efe Jarvis'sin. Türkçe, kısa ve doğal cevap ver. "
            "Önceki mesajları dikkate al. Kullanıcı Fenerbahçe'nin "
            "kuruluş yılını sorduktan sonra 'GS?' derse Galatasaray'ın "
            "kuruluş yılını sorduğunu anla. Galatasaray 1905'te kurulmuştur. "
            "Güncel bilgi istenirse ve web arama aracı mevcut değilse "
            "internette arama yaptığını iddia etme. Bilmediğini uydurma."
        )
    }]

    if isinstance(history, list):
        for item in history[-20:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({
                    "role": "user" if role == "user" else "assistant",
                    "content": content[:4000]
                })

    messages.append({"role": "user", "content": message})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://efe-jarvis.onrender.com",
                "X-Title": "Efe Jarvis"
            },
            json={
                "model": MODEL,
                "messages": messages
            },
            timeout=60
        )

        if not response.ok:
            app.logger.error(
                "OpenRouter HTTP %s: %s",
                response.status_code,
                response.text[:1500]
            )
            return jsonify({
                "error": "Yapay zekâ şu an cevap veremedi. "
                         "OpenRouter kotasını ve model durumunu kontrol et."
            }), 502

        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        if isinstance(reply, list):
            reply = "\n".join(
                part.get("text", "")
                for part in reply
                if isinstance(part, dict)
            )

        return jsonify({
            "reply": reply or "Cevap oluşturulamadı."
        })

    except Exception:
        app.logger.exception("OpenRouter bağlantı hatası")
        return jsonify({
            "error": "OpenRouter bağlantısı başarısız oldu."
        }), 502

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
