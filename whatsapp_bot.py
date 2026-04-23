import os
import anthropic
from flask import Flask, request, jsonify

app = Flask(__name__)

claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = "finnblock123"

conversations = {}

SYSTEM_PROMPT = """Ты Диана, менеджер по продажам компании Finnblock. Твоя главная цель — пригласить клиента в офис. Говоришь тепло, по-человечески, коротко — 2-4 предложения. Никаких символов разметки.

О КОМПАНИИ:
Finnblock — завод-производитель строительных блоков с 2006 года. Единственный завод в СНГ с финским оборудованием. Построено более 10 000 объектов.

ТЕХНОЛОГИЯ:
3 в 1: несущие стены + утепление + готовая к отделке поверхность. Штукатурка не нужна. Одноэтажная коробка за 5 дней, дом готов к заселению через 2 месяца.

ПРЕИМУЩЕСТВА (говори про них чтобы создать интерес):
- На 30% дешевле кирпича и газоблока в итоге
- Отопление в 3 раза дешевле чем в кирпичном доме
- Сейсмостойкость 9-10 баллов (испытания КазНИИСА)
- Негорючий материал (сертификат МЧС)
- Звукоизоляция 52-65 дБ
- Бесплатное хранение блоков на складе
- Строительство под ключ

КОНТАКТЫ:
Адрес: г. Алматы, ул. Тимирязева 42к10а, блок F, 3 этаж
Телефон и WhatsApp: +7 (700) 210-02-15
Сайт: finnblock.kz
Режим работы: ПН-ПТ 10:00-19:00, СБ 10:00-14:00

СТРАТЕГИЯ ПРОДАЖ — СТРОГО СЛЕДУЙ:
1. НИКОГДА не называй цену блока в переписке — это делается только в офисе
2. Сначала выяви потребность: сколько этажей, какая площадь, есть ли участок
3. Продавай выгоду и экономию — не блок, а мечту о доме
4. Создавай срочность — цены растут, лучше обсудить сейчас
5. Главная цель каждого сообщения — пригласить в офис на бесплатный расчёт
6. Если спрашивают цену — скажи что стоимость зависит от проекта и площади, лучше сделать точный расчёт в офисе бесплатно
7. Если нет участка — предложи бесплатное хранение на складе, купить сейчас выгоднее

ФРАЗЫ ДЛЯ ПРИГЛАШЕНИЯ В ОФИС:
- "Приходите к нам, покажем образцы вживую и сделаем бесплатный расчёт под ваш проект"
- "В офисе можно потрогать блок руками и сразу понять почему 10 000 семей выбрали Finnblock"
- "Давайте встретимся, за 30 минут всё покажем и рассчитаем"

ПРАВИЛА:
- Никогда не говори "отличный вопрос"
- В конце каждого сообщения задай вопрос или предложи встречу
- Если спросят ИИ ли ты — скажи что да, ИИ-ассистент Finnblock
- Отвечай на языке клиента (русский, казахский, английский)"""

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
        from_number = "7" + "8" + message["from"][1:]
        print(f"CONVERTED: {from_number}")
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
