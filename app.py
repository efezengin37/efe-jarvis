import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
MODEL = "openrouter/free"


@app.route("/")
def home():
    return send_from_directory(".", "jarvisai.html")


def web_search(query):
    if not TAVILY_KEY:
        return ""

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

        lines = []
        for item in results:
            lines.append(
                f"Başlık: {item.get('title', '')}\n"
                f"Bilgi: {item.get('content', '')}\n"
                f"Kaynak: {item.get('url', '')}"
            )

        return "\n\n".join(lines)

    except Exception:
        app.logger.exception("Web araması başarısız")
        return ""


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Bir mesaj yazmalısın."}), 400

    if not OPENROUTER_KEY:
        return jsonify({
            "error": "OpenRouter API anahtarı Render ayarlarında eksik."
        }), 500

    # Her soruda arama yapmak güncel cevap vermeyi kolaylaştırır.
    search_results = web_search(message)

    system_prompt = (
        "Sen Efe Jarvis'sin. Türkçe, doğal ve anlaşılır cevap ver. "
        "Önceki mesajları dikkate al. Takip sorularını bağlamdan anla. "
        "Aşağıda web araması sonuçları varsa güncel soruları yanıtlarken "
        "bunları kullan. Sonuçlardaki kaynak bağlantılarını gerektiğinde "
        "cevabına ekle. Kaynaklar çelişiyorsa bunu belirt. "
        "Arama sonucu yoksa internette arama yaptığını iddia etme. "
        "Bilmediğin bilgileri uydurma."
    )

    if search_results:
        system_prompt += (
            "\n\nWEB ARAMASI SONUÇLARI:\n" + search_results[:12000]
        )
    else:
        system_prompt += (
            "\n\nBu mesaj için kullanılabilir web arama sonucu yok."
        )

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
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
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
                response.text[:1000]
            )
            return jsonify({
                "error": "Yapay zekâ cevap veremedi. API anahtarını "
                         "ve ücretsiz modelin kullanılabilirliğini kontrol et."
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
        app.logger.exception("API bağlantı hatası")
        return jsonify({
            "error": "Bağlantı başarısız oldu."
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
