
import os
from flask import Flask, request, jsonify, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

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

    if client is None:
        return jsonify({"error": "API anahtarı ayarlanmamış."}), 500

    # İstemciden gelen geçmişi sınırla ve doğrula.
    contents = []
    if isinstance(history, list):
        for item in history[-20:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            text = item.get("content")
            if role not in ("user", "assistant") or not isinstance(text, str):
                continue
            text = text.strip()[:4000]
            if text:
                contents.append(types.Content(
                    role="user" if role == "user" else "model",
                    parts=[types.Part(text=text)]
                ))

    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=message)]
    ))

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Sen Efe Jarvis'sin. Türkçe konuş. Kısa, net ve doğal cevap ver. "
                    "Konuşmanın önceki mesajlarını dikkatle dikkate al. "
                    "Kullanıcı 'GS?', 'peki ya o?' veya benzeri kısa bir takip sorusu "
                    "sorarsa önceki konuşmaya göre ne kastettiğini anlamaya çalış. "
                    "Örneğin Fenerbahçe'nin kuruluş yılı sorulduktan sonra 'GS?' "
                    "derse Galatasaray'ın kuruluş yılını soruyor olabilir; "
                    "Galatasaray 1905 yılında kurulmuştur. "
                    "Güncel bilgi gerektiğinde Google Search kullan. "
                    "Emin olmadığın bilgiyi uydurma."
                ),
                tools=[
                    types.Tool(google_search=types.GoogleSearch())
                ]
            )
        )

        return jsonify({
            "reply": response.text or "Cevap oluşturulamadı."
        })

    except Exception:
        app.logger.exception("AI bağlantı hatası")
        return jsonify({
            "error": "Jarvis cevap veremedi. Render loglarını kontrol et."
        }), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
