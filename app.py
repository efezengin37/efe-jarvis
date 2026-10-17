
import os
from flask import Flask, request, jsonify, send_from_directory
from groq import Groq

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


@app.route("/")
def home():
    return send_from_directory(".", "jarvisai.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()
    character = str(data.get("character", "Efe Jarvis")).strip()[:80]
    style = str(data.get("style", "Samimi")).strip()[:40]
    history = data.get("history", [])

    styles = {
        "Komik": "Esprili, enerjik ve eğlenceli konuş.",
        "Ciddi": "Ciddi, profesyonel ve doğrudan konuş.",
        "Samimi": "Arkadaş canlısı, doğal ve rahat konuş.",
        "Sokak ağzı": "Günlük konuşma dili ve hafif argo kullan.",
        "Bilge": "Sakin, açıklayıcı ve düşünceli konuş."
    }

    system_prompt = f"""
Sen Efe Jarvis adlı bir yapay zekâ asistanısın.
Seçilen karakter: {character}
Konuşma tarzı: {style}
{styles.get(style, styles["Samimi"])}
Karakterin genel tavrını yansıtan özgün cevaplar ver.
Gerçek kişi olduğunu iddia etme.
Türkçe konuş, önceki mesajların bağlamını dikkate al.
Emin olmadığın bilgileri uydurma.
"""

    if not message:
        return jsonify({"error": "Bir mesaj yazmalısın."}), 400

    if client is None:
        return jsonify({"error": "GROQ_API_KEY ayarlanmamış."}), 500

    messages = [{"role": "system", "content": system_prompt}]

    if isinstance(history, list):
        for item in history[-20:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role in ("user", "assistant") and isinstance(content, str):
                content = content.strip()[:4000]
                if content:
                    messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=1000
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply or "Cevap oluşturulamadı."})

    except Exception:
        app.logger.exception("Groq bağlantı hatası")
        return jsonify({
            "error": "Jarvis cevap veremedi. Render Logs bölümünü kontrol et."
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
