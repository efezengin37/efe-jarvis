import os
from flask import Flask, request, jsonify, send_from_directory
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route("/")
def home():
   return send_from_directory(".", "jarvisai.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Bir mesaj yazmalısın."}), 400

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=message,
            config={
                "system_instruction": (
                    "Sen Efe Jarvis'sin. Türkçe konuş. Kısa, net ve doğal cevaplar ver. "
                     "Gereksiz açıklama yapma."
                )
            }
        )
        return jsonify({"reply": response.text or "Cevap oluşturulamadı."})
    except Exception:
        app.logger.exception("AI bağlantı hatası")
        return jsonify({"error": "AI bağlantısı başarısız oldu. Anahtarı ve interneti kontrol et."}), 500

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("API anahtarı ayarlanmamış.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
