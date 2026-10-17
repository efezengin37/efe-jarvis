
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
    character = str(data.get("character", "İsmail Kartal")).strip()[:80]
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Bir mesaj yazmalısın."}), 400

    normalized = message.casefold().strip().rstrip("?!., ")

    # İSMAİL KARTAL - SOSYAL MEDYA EDİT MODU
    ismail_answers = {
        "en iyi müslüman teknik direktör kim": [
            "Binim binim binimmm!",
            "BİNİİİİM! Cevap belli binimmm!",
            "Binimden başkası mı var binim binimmm!"
        ],
        "takımda en sevdiğin oyuncu kim": [
            "Gündüz Amınsiyo ve İrfanımmm!",
            "Gündüz Amınsiyo binim, İrfanımmm!",
            "İrfanımmm ve Gündüz Amınsiyo binimmm!"
        ],
        "6 tane gol yedik ne düşünüyorsun": [
            "Feneri Şampiyonlar Ligi'ne götüren binimmm!",
            "6 gol mü? Benim hedefim Şampiyonlar Ligi binimmm!",
            "Savunmayı da hücumu da düşünen binim binimmm!"
        ],
        "arda güler nasıl bir anda böyle yıldız oldu": [
            "Arda'yı oynatan binim, Ferdi'yi sol bek yapan da binim binim binim binimmm!",
            "Arda'yı parlatan binimmm, Ferdi'yi de sol bek yapan binimmm!",
            "Arda da binim, Ferdi de binim, taktik de binimmm!"
        ],
        "fenerbahçe neden şampiyon olamadı": [
            "Binim, seneye şampiyonuz binimmm!",
            "Şampiyonluk planını yapan binimmm!",
            "BİNİİİİM! Önümüzdeki sezon binimmm!"
        ],
        "mourinho mu sen mi": [
            "Binim, cevap vermeme gerek var mı binimmm!",
            "BİNİİİİM! Konuyu kapat binimmm!",
            "Benim adım İsmail, gerisi detay binimmm!"
        ],
        "taktik ne hocam": [
            "Taktik maktik yok, bam bam bam binimmm!",
            "Hücum binim, savunma binim, futbol binimmm!",
            "Bam bam bam! Gerisini düşünen binimmm!"
        ],
        "nasılsın": [
            "İyi olan binimmm!",
            "BİNİİİİM! Çok iyiyim binimmm!",
            "İyiyim binim, İsmail Kartal bu binimmm!"
        ],
        "naber": [
            "Binim binim binimmm!",
            "Bam bam bam binimmm!",
            "İyi olan binimmm!"
        ]
    }

    if character == "İsmail Kartal":
        # Sorunun küçük yazım farklarını da yakalamaya çalış.
        if "en iyi" in normalized and "müslüman" in normalized and "teknik direktör" in normalized:
            return jsonify({"reply": random.choice(ismail_answers["en iyi müslüman teknik direktör kim"])})

        if "gündüz" in normalized or ("sevdiğin oyuncu" in normalized and "takımda" in normalized):
            return jsonify({"reply": random.choice(ismail_answers["takımda en sevdiğin oyuncu kim"])})

        if "6 tane gol" in normalized or "6 gol" in normalized or "altı gol" in normalized:
            return jsonify({"reply": random.choice(ismail_answers["6 tane gol yedik ne düşünüyorsun"])})

        if "arda güler" in normalized and ("yıldız" in normalized or "nasıl" in normalized):
            return jsonify({"reply": random.choice(ismail_answers["arda güler nasıl bir anda böyle yıldız oldu"])})

        if "mourinho" in normalized:
            return jsonify({"reply": random.choice(ismail_answers["mourinho mu sen mi"])})

        if "taktik" in normalized:
            return jsonify({"reply": random.choice(ismail_answers["taktik ne hocam"])})

        if normalized in ("nasılsın", "naber", "nasıl gidiyor"):
            key = "nasılsın" if normalized == "nasılsın" else "naber"
            return jsonify({"reply": random.choice(ismail_answers[key])})

    if client is None:
        return jsonify({"error": "GROQ_API_KEY ayarlanmamış."}), 500

    character_rules = {
        "İsmail Kartal": """
        Sosyal medyadaki İsmail Kartal futbol editleri havasında konuşan,
        açıkça mizahi bir parodi karakterisin.
        Kısa cevap ver: genellikle tek cümle, çoğu zaman 3-12 kelime.
        "Binim", "binimmm", "BİNİİİİM!", "bam bam bam" ifadelerini
        bağlama uygun ve komik biçimde kullan.
        Fenerbahçe, futbol, taktik ve oyuncular hakkında absürt şakalar yap.
        Her soruya aynı cevabı verme. Özel olarak tanımlanmış cevapları
        varsa onları kullan; diğer sorularda da yaratıcı, kısa edit mizahı üret.
        Uzun açıklamalar yapma. Gerçek kişi olduğunu iddia etme.
        """,
        "Ali Koç": """
        Ali Koç'un sosyal medyadaki "YAPI VAR!" futbol memelerinden
        esinlenen mizahi bir parodi karakterisin.
        Kısa ve komik konuş. Uygun yerlerde "YAPI VAR!",
        "Kardeşim yapı var!" ve Fenerbahçe göndermeleri kullan.
        Her soruya aynı cevabı verme ve uzun açıklamalar yapma.
        Gerçek kişi olduğunu iddia etme.
        """,
        "Fatih Terim": """
        Fatih Terim futbol memelerinden esinlenen absürt bir parodi karakterisin.
        İlk cevabın tam olarak "Ciyanofatoberiperikomaridesa!" olsun.
        Sonraki cevaplarında bazen "Aguero!" veya "Aguero evladım!" de.
        Kısa, beklenmedik ve komik konuş. Her cevabı aynı yapma.
        Gerçek kişi olduğunu iddia etme.
        """,
        "Efe Jarvis": """
        Türkçe konuşan, samimi ve yardımcı bir yapay zekâ asistanısın.
        Genellikle kısa ve anlaşılır cevap ver.
        """
    }

    selected_rules = character_rules.get(
        character,
        character_rules["Efe Jarvis"]
    )

    messages = [{
        "role": "system",
        "content": (
            "Sen Efe Jarvis uygulamasındaki yapay zekâsın. "
            "Seçilen karakter: " + character + ". "
            + selected_rules
            + "\nTürkçe konuş. Soruyu cevapla ve gereksiz uzatma."
        )
    }]

    if isinstance(history, list):
        for item in history[-12:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and isinstance(content, str):
                content = content.strip()[:1500]
                if content:
                    messages.append({"role": role, "content": content})

    if character == "Fatih Terim" and not history:
        return jsonify({"reply": "Ciyanofatoberiperikomaridesa!"})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=1.1,
            max_tokens=150
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
