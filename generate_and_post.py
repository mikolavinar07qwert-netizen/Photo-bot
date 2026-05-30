import os
import sys
import time
import random
import requests
from urllib.parse import quote

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TARGET = os.environ["TELEGRAM_REVIEW_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
IMAGE_API = "https://image.pollinations.ai/prompt/"

TOPICS = [
    "природне світло й робота зі світлотінню",
    "композиція кадру і правило третин",
    "як ловити емоцію та настрій у портреті",
    "психологія погляду глядача: куди веде кадр",
    "робота з моделлю: довіра й розкутість",
    "колір і настрій у фотографії",
    "момент і передчуття: коли натиснути кнопку",
    "мінімалізм і простір у кадрі",
    "як розвивати насмотренність і власний стиль",
    "сторітелінг: як фото розповідає історію",
    "тінь, контраст і драматизм",
    "зйомка в золоту годину та синю годину",
    "деталь і фактура як головний герой",
    "ритм, лінії та геометрія в кадрі",
    "що робить фото 'живим', а не технічно правильним",
    "робота зі страхом чистого аркуша й творчим вигоранням",
    "плівкова естетика й недосконалість як прийом",
    "як бачити незвичайне у звичайному",
]

FORMATS = [
    ("порада", "Дай одну конкретну практичну пораду фотографу на тему «{topic}» і поясни, чому це працює і що це дає кадру."),
    ("розбір прийому", "Розбери один візуальний прийом на тему «{topic}»: як його застосувати на практиці й який ефект він створює."),
    ("вправа", "Запропонуй просту вправу/челендж на тему «{topic}», яку фотограф може зробити сьогодні, покроково."),
    ("насмотренність", "Поясни на тему «{topic}», як це бачать майстри, і як натренувати своє око. Без згадки конкретних знаменитостей."),
    ("психологія кадру", "Поясни психологічний бік теми «{topic}»: що відчуває глядач або автор і як це використати свідомо."),
    ("питання дня", "Напиши живий вступ на 2-3 речення на тему «{topic}» і заверши рефлексивним питанням до фотографа."),
]

IMAGE_STYLES = [
    "cinematic photography, dramatic natural light, shallow depth of field",
    "moody film photography aesthetic, warm grain, soft tones",
    "minimalist fine-art photography, negative space, muted palette",
    "golden hour atmospheric scene, soft backlight",
    "black and white documentary photography, strong contrast",
    "editorial still life, elegant soft lighting",
]


def ask_gemini(prompt, temperature=0.85, timeout=120):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    last = None
    for _ in range(3):
        try:
            r = requests.post(GEMINI_URL, params={"key": GEMINI_API_KEY}, json=body, timeout=timeout)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            last = e
            time.sleep(6)
    raise last


def generate_post(topic, fmt_instruction):
    prompt = (
        "Ти — досвідчений фотограф і викладач, ведеш блог про фотографію та візуальне мистецтво. "
        "Пишеш живою, природною розмовною українською, як до колеги-початківця. "
        + fmt_instruction.format(topic=topic) + " "
        "\n\nЯКІСТЬ:\n"
        "- Одна чітка думка по суті, без води й банальностей.\n"
        "- Конкретика: що саме робити, на що дивитися, який результат.\n"
        "- Один живий приклад або мікросценарій зйомки.\n"
        "- Дія, яку можна спробувати вже сьогодні.\n"
        "- УСІ речення завершені, природні, без кальок і суржику.\n\n"
        "СТИЛЬ: тепло, на «ти», без повчального тону, бездоганна граматика.\n"
        "ЗАБОРОНЕНО: кліше «У сучасному світі», «У нашому стрімкому житті», пафос, гасла, "
        "абстракції без змісту, обірвані речення.\n\n"
        "Обсяг 500-900 символів. Почни з живого, не банального заголовка. "
        "Додай 2-3 доречні хештеги в кінці (про фото). Без markdown, звичайний текст, емодзі помірно. "
        "Поверни ЛИШЕ готовий текст поста, без пояснень."
    )
    return ask_gemini(prompt)


def make_image_prompt(topic):
    style = random.choice(IMAGE_STYLES)
    try:
        scene = ask_gemini(
            "Опиши ОДНУ коротку англійською візуальну сцену (макс 14 слів), що передає тему "
            f"фотографії: «{topic}». Конкретний образ, без тексту. Поверни лише англійський опис сцени.",
            temperature=1.0, timeout=60,
        ).replace("\n", " ").strip()
    except Exception:
        scene = "a beautiful atmospheric photographic scene with expressive light"
    return f"{scene}, {style}, no text, high quality"


def get_image(image_prompt):
    url = IMAGE_API + quote(image_prompt)
    r = requests.get(url, params={"width": 1024, "height": 1024, "nologo": "true",
                                  "model": "flux", "seed": random.randint(1, 999999), "enhance": "true"}, timeout=180)
    r.raise_for_status()
    return r.content


def send_photo(image_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("post.jpg", image_bytes, "image/jpeg")}
    data = {"chat_id": TARGET, "caption": caption[:1024]}
    r = requests.post(url, data=data, files=files, timeout=60)
    r.raise_for_status()
    return r.json()


def send_text(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TARGET, "text": text, "disable_web_page_preview": True}, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    topic = random.choice(TOPICS)
    fmt_name, fmt_instr = random.choice(FORMATS)
    print("Тема:", topic, "| Формат:", fmt_name)
    post = generate_post(topic, fmt_instr)
    print("Пост:\n", post)
    try:
        image = get_image(make_image_prompt(topic))
        send_photo(image, post)
        print("Надіслано з картинкою.")
    except Exception as e:
        print("Без картинки:", e, file=sys.stderr)
        send_text(post)
        print("Надіслано текстом.")


if __name__ == "__main__":
    main()
