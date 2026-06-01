import os
import sys
import time
import random
import requests
from urllib.parse import quote

print(">>> СКРИПТ СТАРТУВАВ", flush=True)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TARGET = os.environ["TELEGRAM_REVIEW_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

print(">>> СЕКРЕТИ ПРОЧИТАНО", flush=True)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
IMAGE_API = "https://image.pollinations.ai/prompt/"
IMAGE_MODEL = "gptimage"

# >>> ТВОЇ ДАНІ <<<
CITY = "Мукачево"
CONTACTS = "Запис і приклади робіт — в Instagram і Facebook. Мукачево."

# Тематичні тижні-парасольки (широкі емоційні теми). Бот тримає одну ~7 днів.
UMBRELLAS = [
    "прийняття себе теперішньої",
    "памʼять і час, бажання зберегти себе сьогоднішню",
    "жіночність як внутрішній стан",
    "самоцінність і дозвіл подобатись собі",
    "повернення до себе після складного періоду",
    "краса поза стандартами й чужими очікуваннями",
]

# Воронка: розподіл типів контенту (мʼякий продаж)
# 40% залучення, 30% довіра/експертність, 20% бажання, 10% продаж
FUNNEL = (
    ["залучення"] * 4 +
    ["довіра"] * 3 +
    ["бажання"] * 2 +
    ["продаж"] * 1
)

STAGE_INSTRUCTIONS = {
    "залучення": (
        "Тип: ЗАЛУЧЕННЯ. Напиши живу історію-спостереження або роздум навколо теми «{theme}». "
        "Мета — зачепити емоцію, щоб захотілось читати й зберегти. Про зйомку прямо не говори, "
        "максимум натяк наприкінці."
    ),
    "довіра": (
        "Тип: ДОВІРА/ЕКСПЕРТНІСТЬ. Розкрий тему «{theme}» через те, як ти працюєш: атмосфера зйомки, "
        "відчуття безпеки, як ти допомагаєш людині розкритись, твоя авторська позиція. "
        "Зніми типовий страх «я не фотогенічна» — покажи, що поруч із тобою комфортно."
    ),
    "бажання": (
        "Тип: БАЖАННЯ. Розкажи правдоподібну живу історію клієнтки навколо теми «{theme}» — "
        "не про те, як вона змінилась зовні, а що вона зрозуміла чи відчула про себе. "
        "Щоб у читачки виникло тихе «я теж так хочу»."
    ),
    "продаж": (
        "Тип: МʼЯКИЙ ПРОДАЖ. Навколо теми «{theme}» делікатно запроси на індивідуальну портретну зйомку. "
        "Дуже мʼяко, через турботу й натхнення, без тиску. Наприкінці природний заклик у дусі: "
        "«якщо відгукнулось — напишіть мені», «приклади робіт і запис в Instagram та Facebook», "
        "«запитайте про найближчі дати». Згадай, що ти у Мукачеві."
    ),
}

# Відео-ідеї без бекстейджів — формати, які реально зняти з готових фото
VIDEO_FORMATS = [
    "слайдшоу з 5-7 готових портретів під атмосферну музику з плавними переходами",
    "один сильний портрет на весь екран із повільним зумом і коротким текстом-роздумом поверх",
    "до/після або кілька кадрів однієї клієнтки, де видно, як вона розкривається",
    "текстовий роздум на атмосферному фоні (кадр природи/світла) з текстом на екрані й музикою",
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


ANTISHABLON = (
    "\n\nСУВОРО ЗАБОРОНЕНО (це вбиває живість і викриває ШІ):\n"
    "- звороти-шаблони: «Вона думала… а виявилось…», «Це не про…, це про…», «Уявіть собі…», "
    "«Дозвольте розповісти…», «У світі, де…», «У сучасному світі…», «І ось тут починається найцікавіше», "
    "«Спойлер:», «Кожна жінка прекрасна», «Будь собою», «Фотографія — це більше ніж…»;\n"
    "- драматичні обриви короткими реченнями через крапку для ефекту;\n"
    "- мотиваційні гасла, пафос, штучний захват, коучингова риторика;\n"
    "- будь-який стиль, що впізнається як ChatGPT.\n"
    "ЗАМІСТЬ ШАБЛОНІВ: пиши конкретними живими деталями й сценками — що людина сказала, зробила, "
    "відчула; як говорить реальна людина, а не реклама.\n"
)


def generate_post(theme, stage):
    instr = STAGE_INSTRUCTIONS[stage].format(theme=theme)
    prompt = (
        "Ти — Микола Вінар, портретний фотограф із Мукачева. Знімаєш переважно жінок. "
        "Твоя робота на перетині фотографії, психології, мистецтва й особистої історії людини. "
        "Продаєш не послугу, а досвід побачити себе по-новому. Пишеш сам, від себе, "
        "як жива інтелігентна людина.\n\n"
        + instr +
        "\n\nТОН: спостережливий, глибокий, людяний, теплий, емоційний без пафосу, "
        "впевнений без агресивних продажів.\n"
        "ФОРМА: живий нешаблонний перший рядок; конкретні образи й деталі замість загальних слів; "
        "усі речення завершені; бездоганна українська."
        + ANTISHABLON +
        "\nОбсяг 500-900 символів. Додай 3-4 органічні хештеги (портретна зйомка, фотограф Мукачево). "
        "Без markdown, звичайний текст, емодзі дуже помірно або без них. Поверни ЛИШЕ готовий текст поста."
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


def generate_video_idea(theme):
    fmt = random.choice(VIDEO_FORMATS)
    prompt = (
        "Ти — портретний фотограф із Мукачева, знімаєш жінок. Веди особисту сторінку. "
        f"Тема тижня: «{theme}». Формат відео БЕЗ зйомки процесу (бекстейджу нема): {fmt}.\n\n"
        "Запропонуй ідею короткого ВЕРТИКАЛЬНОГО відео (Reels, 9:16, 15-40 сек), яке можна зробити "
        "з готових фотографій, без обличчя автора в кадрі й без зйомки процесу. Гачок у перші 3 секунди.\n\n"
        "Формат відповіді (звичайний текст, без markdown):\n"
        "🎬 ІДЕЯ: (коротка назва)\n"
        "🎞 Які кадри/фото взяти: (опис, скільки)\n"
        "📝 Текст на екран по кадрах: (живі короткі фрази українською — БЕЗ шаблонів)\n"
        "🎵 Музика: (настрій + нагадай брати з бібліотеки Instagram/Facebook)\n"
        "📲 Підпис до публікації: (1-2 живі речення + 3-4 хештеги, мʼякий заклик писати в дірект)\n"
        + ANTISHABLON +
        "\nПиши живою людською українською, тепло й конкретно."
    )
    return ask_gemini(prompt)


def get_image(image_prompt):
    url = IMAGE_API + quote(image_prompt)
    r = requests.get(url, params={"width": 896, "height": 1152, "nologo": "true",
                                  "model": IMAGE_MODEL, "seed": random.randint(1, 999999),
                                  "enhance": "true"}, timeout=180)
    r.raise_for_status()
    return r.content


def split_text(text, limit=4000):
    text = text.strip()
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        chunk = text[:limit]
        cut = chunk.rfind("\n\n")
        if cut < limit * 0.5:
            cut = chunk.rfind("\n")
        if cut < limit * 0.5:
            cut = chunk.rfind(". ")
            if cut != -1:
                cut += 1
        if cut < limit * 0.5:
            cut = limit
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        parts.append(text)
    return parts


def send_photo(image_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    if len(caption) <= 1024:
        files = {"photo": ("post.jpg", image_bytes, "image/jpeg")}
        data = {"chat_id": TARGET, "caption": caption}
        r = requests.post(url, data=data, files=files, timeout=60)
        r.raise_for_status()
        return r.json()
    files = {"photo": ("post.jpg", image_bytes, "image/jpeg")}
    data = {"chat_id": TARGET}
    r = requests.post(url, data=data, files=files, timeout=60)
    r.raise_for_status()
    send_text(caption)
    return r.json()


def send_text(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    last = None
    for part in split_text(text, 4000):
        r = requests.post(url, json={"chat_id": TARGET, "text": part,
                                     "disable_web_page_preview": True}, timeout=30)
        r.raise_for_status()
        last = r.json()
    return last


def pick_theme_and_stage():
    """Тема-парасолька тримається ~7 днів, формат щодня змінюється за воронкою."""
    day = int(time.time() // 86400)          # номер доби
    umbrella = UMBRELLAS[(day // 7) % len(UMBRELLAS)]   # парасолька змінюється раз на тиждень
    stage = FUNNEL[day % len(FUNNEL)]        # стадія воронки ротується щодня
    return umbrella, stage


def main():
    print(">>> MAIN ПОЧАВСЯ", flush=True)
    theme, stage = pick_theme_and_stage()
    print("Парасолька:", theme, "| Стадія воронки:", stage, flush=True)

    # Основний пост за воронкою
    post = generate_post(theme, stage)
    print("Пост:\n", post, flush=True)
    try:
        send_photo(get_image(make_image_prompt(theme)), post)
        print(">>> Надіслано пост.", flush=True)
    except Exception as e:
        print(">>> Без картинки:", e, file=sys.stderr, flush=True)
        send_text(post)

    # Окремо — відео-ідея дня (без бекстейджів)
    time.sleep(2)
    try:
        idea = generate_video_idea(theme)
        send_text("💡 ВІДЕО-ІДЕЯ ДНЯ (без бекстейджу, вертикальне)\n\n" + idea)
        print(">>> Надіслано відео-ідею.", flush=True)
    except Exception as e:
        print(">>> Відео-ідея не вдалася:", e, file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
