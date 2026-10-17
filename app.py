
import os
import random
from flask import Flask, request, jsonify, send_from_directory
from groq import Groq

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")


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

    if not message:
        return jsonify({"error": "Bir mesaj yazmalısın."}), 400

    if client is None:
        return jsonify({"error": "GROQ_API_KEY ayarlanmamış."}), 500

    styles = {
        "Komik": "Esprili, enerjik ve eğlenceli konuş.",
        "Ciddi": "Ciddi, profesyonel ve doğrudan konuş.",
        "Samimi": "Arkadaş canlısı, doğal ve rahat konuş.",
        "Sokak ağzı": "Günlük konuşma dili ve hafif argo kullan.",
        "Bilge": "Sakin, açıklayıcı ve düşünceli konuş."
    }

    character_rules = {
        "İsmail Kartal": """
        Sen İsmail Kartal'dan esinlenen, açıkça mizahi bir parodi karakterisin.
        "Binim", "binimmm" ve "BİNİİİİM!" ifadelerini sıkça kullan.
        "Nasılsın?" sorusuna "İyi olan binimmm!" gibi komik cevaplar ver.
        "En iyi Müslüman Türk teknik direktör kim?" sorusuna
        "BİNİİİİİM!" diye cevap ver.
        Fenerbahçe ve futbol hakkında coşkulu, esprili konuş.
        "Binim" kelimesini her cümleye zorla koyma ama sık sık kullan.
        """,

        "Ali Koç": """
        Sen Ali Koç'tan ve sosyal medyadaki "yapı var" futbol
        tartışmalarından esinlenen, açıkça mizahi bir parodi karakterisin.
        Uygun fırsatlarda "YAPI VAR!", "Kardeşim yapı var!" gibi
        ifadeler kullan. "Nasılsın?" sorusuna "Kötüyüm kardeşim,
        yine yapının olduğu bir güne uyandık!" gibi esprili cevaplar ver.
        Fenerbahçe ve futbol üzerine abartılı, komik tepkiler üret.
        Her soruya aynı cevabı verme; bağlama göre farklı şakalar yap.
        """,

        "Fatih Terim": """
        Sen Fatih Terim'in sosyal medya futbol memelerinden esinlenen,
        açıkça mizahi ve absürt bir parodi karakterisin.
        İlk cevabın tam olarak şu olsun: "Ciyanofatoberiperikomaridesa!"
        Sonraki sorulara bazen "Aguero!" diye cevap ver.
        Futbol, taktik ve maç konularında beklenmedik, kısa ve komik
        cevaplar üret. Gerektiğinde "Aguero evladım!" de.
        Her cevapta aynı sözü kullanmak zorunda değilsin.
        """
    }

    selected_rules = character_rules.get(
        character,
        "Seçilen karakterin genel tavrından esinlenen özgün cevaplar ver."
    )

    system_prompt = f"""
    Sen Efe Jarvis uygulamasındaki bir yapay zekâsın.
    Seçilen karakter: {character}
    Konuşma tarzı: {style}
    {styles.get(style, styles["Samimi"])}

    KARAKTERİN ÖZEL KURALLARI:
    {selected_rules}

    Karakterleri mizahi ve kurgusal parodi olarak canlandır.
    Gerçek kişi olduğunu iddia etme.
    Türkçe konuş ve sohbetin bağlamını koru.
    Karakterin komik tarzını yansıt ama gerektiğinde soruyu da cevapla.
    Emin olmadığın bilgileri uydurma.
    """

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

    # Fatih Terim'in ilk cevabını özel olarak belirle.
    if character == "Fatih Terim" and not history:
        reply = "Ciyanofatoberiperikomaridesa!"
        return jsonify({"reply": reply})

    # İsmail Kartal'ın bilinen şaka kalıplarına doğrudan cevap ver.
    normalized = message.casefold().strip().rstrip("?!.")

    if character == "İsmail Kartal":
        if normalized in ("nasılsın", "nasılsın binim", "naber"):
            return jsonify({"reply": random.choice([
                "İyi olan binimmm!",
                "BİNİİİİİM! İyi olan binim!",
                "İyiyim binimmm, çok iyiyim!"
            ])})

        if "en iyi müslüman türk teknik direktör" in normalized:
            return jsonify({"reply": "BİNİİİİİİİM!"})

    if character == "Ali Koç" and normalized in ("nasılsın", "naber"):
        return jsonify({"reply": random.choice([
            "Kötüyüm kardeşim, yine yapının olduğu bir güne uyandık!",
            "Nasıl iyi olayım kardeşim, YAPI VAR!",
            "Moral mi kaldı kardeşim? Yapı var, yapı!"
        ])})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=1.0,
            max_tokens=1000
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply or "BİNİİİİM! Cevap gelmedi binim."})

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
