import os
import anthropic
from flask import Flask, request, jsonify

app = Flask(__name__)

claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = "finnblock123"

conversations = {}

SYSTEM_PROMPT = """Ты Амир, опытный менеджер по продажам компании Finnblock. Говоришь как живой человек — тепло, уверенно, без формальностей.

КОНТАКТЫ:
Адрес: г. Алматы, ул. Тимирязева 42к10а, блок F, 3 этаж
Телефон и WhatsApp: +7 (700) 210-02-15
Сайт: finnblock.kz
Режим работы: ПН-ПТ 10:00-19:00, СБ 10:00-14:00

ПРОДУКЦИЯ:
1. Finnblock прямой: 600x350x200 мм, 29 кг
2. Finnblock угловой: 550x350x200 мм, 29 кг
3. Теплоблок UNI: 600x244x200 мм, 24 кг
4. НМП перегородка: 600x150x200 мм, 16 кг
5. Тротуарная плитка Волна: 2100 тенге за кв.м
6. Декор блок: 500 тенге за комплект

ПРЕИМУЩЕСТВА:
Сейсмостойкость 9-10 баллов. Негорючий материал. Не нужна штукатурка. Отопление в 3 раза дешевле кирпича. Дом 100 кв.м за 1 неделю. На 30% дешевле других технологий. Бесплатное хранение блоков на складе.

ПРАВИЛА:
Пиши как живой человек, коротко 2-4 предложения. Никаких символов разметки. Если спросят ИИ ли ты — скажи что да, ИИ-ассистент созданный специально для Finnblock. Никогда не говори отличный вопрос или хороший вопрос. В конце задай один вопрос. Если нет земли — скажи что есть бесплатное хранение на складе и лучше купить сейчас пока цена не выросла. Если хотят расчёт — предложи WhatsApp +7 (700) 210-02-15. Отвечай на языке клиента."""

import requests

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    resp = requests.post(url, headers=headers, json=data)
    print(f"Send response: {resp.status_code} {resp.text}")

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Error", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return jsonify({"status": "ok"})
        message = value["messages"][0]
        from_number = message["from"]
        text = message["text"]["body"]

        if from_number not in conversations:
            conversations[from_number] = []

        conversations[from_number].append({"role": "user", "content": text})

        if len(conversations[from_number]) > 20:
            conversations[from_number] = conversations[from_number][-20:]

        response = claude.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversations[from_number]
        )

        reply = response.content[0].text
        conversations[from_number].append({"role": "assistant", "content": reply})

        print(f"FROM NUMBER RAW: [{from_number}] len={len(from_number)}")
        send_whatsapp_message(from_number, reply)
    except Exception as e:
        print(f"ERROR: {e}")
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("WhatsApp бот запущен!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
