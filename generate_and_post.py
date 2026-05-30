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
IMAGE_MODEL = "seedream"

THEMES = [
    "прийняття себе теперішньої, без бажання бути молодшою чи іншою",
    "жіночність як стан, а не як зовнішність",
    "самоцінність: побачити доказ власної вартості",
    "внутрішня свобода й дозвіл бути собою перед камерою",
    "сексуальність як природна частина особистості, без демонстрації тіла",
    "памʼять і час: зберегти себе теперішню",
    "краса поза стандартами й чужими уявленнями про ідеал",
    "страх камери і відчуття я не фотогенічна",
    "повернення до себе після складного періоду",
    "як жінка бачить себе у дзеркалі і якою вона є насправді",
    "тиша, задумливість і сила спокою в портреті",
    "стосунки людини з власним відображенням",
]

FORMATS = [
    ("історія спостереження", "Почни з короткої живої життєвої сцени, яка приводить до несподіваного висновку про красу, памʼять або самоцінність, повʼязаного з темою: «{theme}»."),
    ("історія клієнтки", "Розкажи правдоподібну історію клієнтки навколо теми «{theme}». Акцент не на тому, як вона змінилася зовні, а на тому, що вона зрозуміла про себе."),
    ("філософський роздум", "Напиши особистий роздум фотографа про тему «{theme}» — красу, час, жіночність, справжність."),
    ("закулісся", "Опиши атмосферу й момент зі зйомки, повʼязаний з темою «{theme}»: робота зі світлом, образом, відчуття безпеки. Без технічних інструкцій."),
    ("авторська позиція", "Поділись особистою думкою фотографа про тему «{theme}» так, щоб це будувало довіру й експертність."),
]

SOFT_CTA = [
    "Якщо вам близька ця історія — напишіть мені.",
    "Розповім, як проходить така зйомка.",
    "Можливо, настав час побачити себе по-новому.",
    "Запитайте про найближчі дати.",
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


def generate_post(theme, fmt_instruction, add_cta):
    cta_line = ""
    if add_cta:
        cta_line = "Наприкінці зроби мʼякий ненавʼязливий перехід до можливості персональної зйомки, у дусі: «" + random.choice(SOFT_CTA) + "» "
    prompt = (
        "Ти — Микола Вінар, портретний фотограф. Твоя робота на перетині фотографії, психології, "
        "мистецтва й особистої історії людини. Ти продаєш не послугу, а досвід побачити себе по-новому. "
        "Пишеш сам, від себе, як жива інтелігентна людина.\n\n"
        + fmt_instruction.format(theme=theme) + " "
        + cta_line +
        "\n\nФОРМУЛА ПОСТА: 1) живе спостереження або історія; 2) несподівана думка; "
        "3) емоційне усвідомлення; 4) мʼякий перехід до фотографії; 5) ненавʼязливий заклик написати. "
        "Якщо прибрати згадку про зйомку, текст усе одно має бути цікавим сам по собі.\n\n"
        "ТОН: спостережливий, глибокий, людяний, інтелігентний, емоційний без пафосу, "
        "впевнений без агресивних продажів.\n\n"
        "СУВОРО ЗАБОРОНЕНО (інакше текст буде зіпсовано):\n"
        "- фрази: «Це не про…, це про…», «Ти не зобовʼязана…», «Уявіть собі…», «Дозвольте розповісти…», "
        "«Кожен із нас…», «У сучасному світі…», «Фотографія — це більше ніж…», «Кожна жінка прекрасна», «Будь собою»;\n"
        "- мотиваційні штампи, коучингова риторика, надмірний позитив, банальні цитати, шаблонні заклики;\n"
        "- ланцюжки коротких речень через крапку для штучної драматизації;\n"
        "- будь-який стиль, що впізнається як ChatGPT.\n\n"
        "Сексуальність, якщо доречна, лише як природна частина особистості, без еротики й провокацій.\n\n"
        "Обсяг 500-900 символів. Живий нешаблонний перший рядок. "
        "Додай 3-4 органічні хештеги. Без markdown, звичайний текст, емодзі дуже помірно або без них. "
        "Поверни ЛИШЕ готовий текст поста."
    )
    return ask_gemini(prompt)


def make_image_prompt(theme):
    try:
        scene = ask_gemini(
            "Опиши ОДНУ коротку англійською кінематографічну сцену (макс 16 слів) — жіночий "
            f"портрет у стилі авторського європейського кіно, настрій теми: «{theme}». "
            "Момент із життя, не постановка. Поверни лише англійський опис сцени.",
            temperature=1.0, timeout=60,
        ).replace("\n", " ").strip()
    except Exception:
        scene = "a woman by a window in soft daylight, quiet thoughtful mood, candid moment"
    realism = ("photorealistic, real photograph, shot on full-frame camera, 85mm lens, "
               "natural soft window light, realistic skin texture with pores and imperfections, "
               "natural film color grading, cinematic European film still, candid, "
               "shallow depth of field, no plastic skin, no CGI, not AI, no oversharpening")
    return f"{scene}, {realism}, vertical portrait orientation, no text"


def get_image(image_prompt):
    url = IMAGE_API + quote(image_prompt)
    r = requests.get(url, params={"width": 896, "height": 1152, "nologo": "true",
                                  "model": IMAGE_MODEL, "seed": random.randint(1, 999999),
                                  "enhance": "true"}, timeout=180)
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
    theme = random.choice(THEMES)
    fmt_name, fmt_instr = random.choice(FORMATS)
    add_cta = random.random() < 0.5
    print("Тема:", theme, "| Формат:", fmt_name, "| CTA:", add_cta)
    post = generate_post(theme, fmt_instr, add_cta)
    print("Пост:\n", post)
    try:
        image = get_image(make_image_prompt(theme))
        send_photo(image, post)
        print("Надіслано з картинкою.")
    except Exception as e:
        print("Без картинки:", e, file=sys.stderr)
        send_text(post)
