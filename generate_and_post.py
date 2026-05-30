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

# Болі, бажання й приводи, навколо яких будується продавальний сторітелінг
ANGLES = [
    "жінка давно не бачила себе красивою на фото і соромиться камери",
    "хочеться зупинити цей вік, цей вигляд, поки час не біжить далі",
    "усі фото — нашвидкуруч із телефона, жодного справжнього портрета себе",
    "потрібен привід нарешті зробити щось приємне тільки для себе",
    "хочеться відчути себе впевненою, жіночною, бажаною перед камерою",
    "подарунок собі на день народження або просто без приводу",
    "оновити аватарку й сторінку фото, де ти собі подобаєшся",
    "зберегти себе теперішню — для себе майбутньої і для дітей",
    "вийти із зони комфорту й побачити себе очима хорошого фотографа",
    "після складного періоду хочеться перевідкрити й полюбити себе",
    "професійний портрет для роботи, блогу, особистого бренду",
    "страх 'я не фотогенічна' — і як зйомка це руйнує",
]

FORMATS = [
    ("історія клієнтки", "Розкажи коротку зворушливу історію (вигадану, але правдоподібну) про жінку, у якої був цей запит: «{angle}». Як вона наважилася на портретну зйомку і що відчула, побачивши свої фото. Емоційно, від третьої особи."),
    ("звернення до читачки", "Напиши тепле особисте звернення до жінки, яка відчуває: «{angle}». Підтримай, поясни, що вона цього варта, і запроси на портретну зйомку."),
    ("роздум фотографа", "Напиши роздум від імені фотографа на тему: «{angle}». Поділись, чому портретна зйомка — це більше, ніж фото, і чому варто наважитися."),
    ("міф і правда", "Візьми типовий страх жінки перед зйомкою (пов'язаний з: «{angle}») і мʼяко розвій його, показавши, як усе відбувається насправді на портретній зйомці."),
    ("запрошення з закликом", "Напиши короткий емоційний пост навколо запиту «{angle}» з чітким, але делікатним закликом записатися на індивідуальну портретну фотосесію зараз."),
]

# Періодично — прямий заклик до дії
DIRECT_CTA = [
    "Запишись на індивідуальну портретну зйомку — напиши мені в дірект.",
    "Лишилось кілька вільних дат цього місяця на портретні зйомки. Пиши — забронюю твою.",
    "Хочеш таку зйомку для себе? Напиши «хочу» в повідомлення — обговоримо ідею.",
]

IMAGE_STYLES = [
    "elegant female portrait photography, soft window light, shallow depth of field",
    "emotional fine-art female portrait, warm tones, cinematic mood",
    "natural beauty portrait, golden hour backlight, soft bokeh",
    "studio female portrait, soft beauty lighting, elegant and tender",
    "film-style female portrait, warm grain, intimate atmosphere",
]


def ask_gemini(prompt, temperature=0.9, timeout=120):
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


def generate_post(angle, fmt_instruction, add_cta):
    cta_line = ""
    if add_cta:
        cta_line = "У кінці додай такий заклик до дії (можеш трохи переформулювати природно): «" + random.choice(DIRECT_CTA) + "» "
    prompt = (
        "Ти — талановитий портретний фотограф, що знімає жінок і веде особисту сторінку. "
        "Твоя мета цим постом — мʼяко, через емоцію, викликати бажання записатися на портретну зйомку. "
        + fmt_instruction.format(angle=angle) + " "
        + cta_line +
        "\n\nЯК ПИСАТИ:\n"
        "- Жива, тепла, природна українська. Звертайся до жінки на «ти».\n"
        "- Чіпляй емоцію: образи, відчуття, конкретні деталі, а не загальні слова.\n"
        "- Покажи цінність зйомки: відчуття себе, памʼять, впевненість, момент.\n"
        "- Продавай делікатно, через турботу й натхнення, без тиску й пафосу.\n"
        "- УСІ речення завершені, без кальок і суржику.\n\n"
        "ЗАБОРОНЕНО: кліше «У сучасному світі», «У нашому стрімкому житті», "
        "сухі рекламні штампи, надмірні знаки оклику, гасла.\n\n"
        "Обсяг 500-900 символів. Почни з живого заголовка, що чіпляє. "
        "Додай 3-4 доречні хештеги (про портретну зйомку, фотографа). Без markdown, звичайний текст, емодзі помірно. "
        "Поверни ЛИШЕ готовий текст поста, без пояснень."
    )
    return ask_gemini(prompt)


def make_image_prompt(angle):
    style = random.choice(IMAGE_STYLES)
    try:
        scene = ask_gemini(
            "Опиши ОДНУ коротку англійською візуальну сцену (макс 14 слів) для красивого "
            "жіночого портрета, що передає настрій: "
            f"«{angle}». Без тексту, тактовно й естетично. Поверни лише англійський опис сцени.",
            temperature=1.0, timeout=60,
        ).replace("\n", " ").strip()
    except Exception:
        scene = "a beautiful tender female portrait with soft emotional light"
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
    angle = random.choice(ANGLES)
    fmt_name, fmt_instr = random.choice(FORMATS)
    add_cta = random.random() < 0.4  # ~40% постів — з прямим закликом
    print("Запит:", angle, "| Формат:", fmt_name, "| CTA:", add_cta)
    post = generate_post(angle, fmt_instr, add_cta)
    print("Пост:\n", post)
    try:
        image = get_image(make_image_prompt(angle))
        send_photo(image, post)
        print("Надіслано з картинкою.")
    except Exception as e:
        print("Без картинки:", e, file=sys.stderr)
        send_text(post)
        print("Надіслано текстом.")


if __name__ == "__main__":
    main()
