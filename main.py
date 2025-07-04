import json
import os
from aiohttp import web
from datetime import datetime
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart, StateFilter
import asyncio
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
router = Router()
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
REVIEWS_CHANNEL = int(os.getenv("REVIEWS_CHANNEL"))
ADMINS_CHANNEL = int(os.getenv("ADMINS_CHANNEL"))
SUPPORT_GROUP_ID = int(os.getenv("SUPPORT_GROUP_ID"))


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- База пользователей ---
USER_DB = "users.json"
def load_users():
    return json.load(open(USER_DB, encoding="utf-8")) if os.path.exists(USER_DB) else {}
def save_users(data):
    json.dump(data, open(USER_DB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
users = load_users()

# --- Состояния ---
class Reg(StatesGroup):
    name = State()
    age = State()

class Feedback(StatesGroup):
    waiting_for_text = State()

class AdminForm(StatesGroup):
    username = State()
    age = State()
    time_commitment = State()
    timezone = State()
    experience = State()
    motivation = State()
    conflict = State()
    ideas = State()
    strengths = State()

class ChatStates(StatesGroup):
    chatting = State()

class AdminChatStates(StatesGroup):
    waiting_user_message_to_admin = State()

user_message_map = {}
# --- Главное меню ---
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Профиль Пользователя")],
            [KeyboardButton(text="📘 Руководство Использования"), KeyboardButton(text="✉️ Раздел Отзывов")],
            [KeyboardButton(text="🎟️ Стать админом"), KeyboardButton(text="🌐 Общаться с Альянсом")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id in users:
        await show_main_menu(message, state)
        return
    await state.clear()
    await message.answer("Привет! Добро пожаловать в Альянс Свободы. Как тебя зовут?")
    await state.set_state(Reg.name)

@dp.message(Reg.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Reg.age)

@dp.message(Reg.age)
async def get_age(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = str(message.from_user.id)
    users[user_id] = {
        "username": message.from_user.username,
        "name": data["name"],
        "age": message.text,
        "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reputation": {"+": 0, "-": 0},
        "messages": 0
    }
    save_users(users)
    try:
        photo = FSInputFile("menu.jpg")
        await message.answer_photo(photo, caption=(
            "🌌 Добро пожаловать в Альянс Свободы. Здесь нет оков, нет давления — только лёгкий воздух и тёплое пространство, где можно просто быть собой. 🕊️\n\n"
            "╭─╴🧩 Здесь можно:\n"
            "• ✦ поговорить на любые темы без масок, без преград, не ища сложных путей\n"
            "• ✦ выдохнуть… и быть услышанным, по-настоящему\n"
            "• ✦ почувствовать: ты не один и это больше, чем просто слова\n"
            "✦ получить что-то важное может, поддержку… а может, просто тёплое, лёгкое общение\n"
            "╰─╴💫 И просто получить то ли поддержку, то ли приятное общение\n\n"
            "💫 Мы рядом. Мягко, бережно, без громких слов. В этом пространстве тебя примут таким, какой ты есть. Ты дома, звёздный странник. ✨"
        ))
    except:
        await message.answer()
    await message.answer("⟡ Жми на кнопочку и шагни в свободу. Мы ждём тебя. ⇣", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Главное меню")]],
        resize_keyboard=True
    ))
    await state.clear()

@dp.message(F.text == "▶️ Главное меню")
async def show_main_menu(message: Message, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("welcome.jpg")
        await message.answer_photo(photo, caption=(
            "🌌 Главное меню — Альянс Свободы\n───────────────\n"
            "𖤐 Профиль Пользователя \n твоя личная точка отсчёта. всё начинается с тебя.\n"
            "𖤐 Руководство Использования \n если что-то запуталось — загляни сюда. всё просто.\n"
            "𖤐 Раздел Отзывов \n скажи, что чувствуешь. нам важно слышать тебя.\n"
            "𖤐 Стать Админом \n открытая дверь для тех, кто хочет делать пространство лучше.\n"
            "𖤐 Активные Админчики \n те, кто сейчас рядом. на связи.\n───────────────\n"
            "⋆⁺₊⋆ ☁️ ⋆⁺₊⋆ \n Спокойно. Ты в Альянсе. Всё работает."
        ))
    except:
        await message.answer()
    await message.answer("Выбери нужный раздел:", reply_markup=get_main_menu())
# --- Профиль ---
@dp.message(F.text == "👥 Профиль Пользователя")
async def profile(message: Message, state: FSMContext):
    await state.clear()
    user_id = str(message.from_user.id)
    user = users.get(user_id)
    if not user:
        return await message.answer("Ты ещё не зарегистрирован.")

    username = f"@{user.get('username') or 'Без ника'}"
    rep = user.get("reputation", {"+": 0, "-": 0})
    joined = user.get("joined", "Неизвестно")
    msg_count = user.get("messages", 0)

    await message.answer(
        "🌫️𖦹 Личное пространство — Альянс Свободы\n"
        "╭──────⋆˚₊❄️⋆──────╮ \n"
        f"⟡ Позывной: {username}\n"
        f"⟡ Всего сообщений: {msg_count}\n"
        f"⟡ С нами с: {joined}\n"
        f"⟡ Репутация: +{rep.get('+',0)} / -{rep.get('-',0)}\n"
        f"⟡ ID: {user_id}\n\n"
        "⟡ Подарки: пока пусто — но это лишь начало \n"
        "╰──────⋆˚₊✧⋆──────╯"
    )

# --- Руководство Использования ---
@dp.message(F.text == "📘 Руководство Использования")
async def user_guide(message: Message, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("guide.jpg")
        await message.answer_photo(
            photo,
            caption=(
                "📖 <b>✦˚₊‧₊🌌 Альянс Свободы приветствует тебя ₊‧₊˚✦</b>\n\n"
                "Ты оказался в пространстве, где шум стихают, а люди остаются настоящими.\n"
                "Здесь можно быть. Не казаться. Не торопиться. Просто — быть. \n \n "
                "╭── ⊹˚₊𖤐 Что здесь важно 𖤐₊˚⊹ ──╮\n"
                "⟡ Спокойное, бережное общение\n"
                "⟡ Искренность без давления\n"
                "⟡ Уважение к себе и другим \n"
                "⟡ Тишина, когда она нужна \n"
                "╰──────────────────────────╯ \n \n"
                "╭── ⊹˚₊⚠️ А это — не наше ⚠️₊˚⊹ ──╮ \n"
                "✗ Резкость, грубость, спам \n"
                "✗ Темы, которые ранят \n"
                "✗ Принуждение к откровенности \n"
                "✗ Игры с чужими чувствами \n"
                "╰──────────────────────────╯ \n \n"
                "☁️ Если ответа нет сразу — не пугайся. \n"
                "Значит, кто-то отдыхает, а кто-то в пути. \n "
                "Ты не один — просто подожди немного. \n \n"
                "𖦹 Ты не должен быть идеальным. \n"
                "Можно быть разным — уставшим, весёлым, молчаливым. \n"
                "Главное — будь собой. \n \n"
                "˗ˏˋ 🕊️ ˎˊ˗ \n"
                "Ты здесь не случайно. \n"
                "Добро пожаловать домой."
            )
        )
    except:
        await message.answer()

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Выйти")]],
        resize_keyboard=True
    )
    await message.answer("Нажми кнопку, чтобы выйти в главное меню.", reply_markup=kb)

@dp.message(F.text == "⬅️ Выйти")
async def exit_to_main(message: Message, state: FSMContext):
    await show_main_menu(message, state)
# --- Раздел Отзывов ---
@dp.message(F.text == "✉️ Раздел Отзывов")
async def review_section(message: Message, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("reviews.jpg")
        await message.answer_photo(
            photo=photo,
            caption="""
🌊 <b>🌙﹒₊˚✧ Уголок Отголосков ✧˚₊﹒🌙 \n
𖦹 пространство тёплых слов и честных чувств 𖦹</b>

╭── ⋆˙⊹˚ ────────────╮
✦ Хочешь поделиться, как тебе здесь?
✦ Оставить несколько строк — для нас это важно.
✦ Или просто почитай, что пишут другие путники.
╰────────────────────╯ \n \n

📖 Отзывы Альянса собраны здесь:
[⟡ открыть пристанище ⟡] \n \n

𓆩♡𓆪 Без спешки. Без ожиданий.
Ты можешь просто почувствовать  или сказать вслух. \n \n

⟡ Выбирай действие ниже и оставь отголосок.
Небольшой шепот, тоже часть легенды.
""",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
                ]
            )
        )
    except:
        await message.answer("(reviews.jpg не найден)")

@dp.callback_query(F.data == "leave_review")
async def ask_review(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Feedback.waiting_for_text)
    await callback.message.answer("📝 Напиши свой тёплый отклик:\n\n— от 20 до 120 символов\n— начинай с #имя_админа")

@dp.message(Feedback.waiting_for_text)
async def receive_review(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 20 or len(text) > 120 or not text.startswith("#"):
        return await message.answer("❌ Отзыв должен быть от 50 до 120 символов и начинаться с #имя_админа.")

    await bot.send_message(
        chat_id=REVIEWS_CHANNEL,
        text=f"💬 <b>Новый отзыв:</b>\n\n{text}\n\n🧾 От: @{message.from_user.username or 'Без ника'}"
    )
    await message.answer("✅ Спасибо! Твой отзыв отправлен.")
    await state.clear()
    await show_main_menu(message, state)

@dp.callback_query(F.data == "back_to_main")
async def back_from_reviews(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await show_main_menu(callback.message, state)
# --- Анкета "Стать админом" ---
@dp.message(F.text == "🎟️ Стать админом")
async def start_admin_form(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AdminForm.username)
    await message.answer("🕊️˚₊‧ ⟡ Заявка в команду Альянса ⟡ ‧₊˚🌌 \n Чувствуешь в себе желание помогать? \n Хочешь быть тем, кто создаёт уют, сохраняет спокойствие и встречает новых участников светом? \n \n 𖦹 Если откликается — просто расскажи немного о себе. \n Без напряжения, без давления — по-настоящему. \n \n Команда Альянса всегда открыта для тех, \n кто хочет быть частью чего-то доброго и настоящего. \n \n  ˗ˏˋ 🤍 ˎˊ˗ \n Ты не обязан быть идеальным. \n Важно — быть искренним.. \n Скажи нам какой у тебя username?", reply_markup=cancel_kb())

@dp.message(AdminForm.username)
async def admin_get_username(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return await cancel_admin_form_msg(message, state)
    await state.update_data(username=message.text)
    await state.set_state(AdminForm.age)
    await message.answer("Сколько тебе лет?", reply_markup=cancel_kb())

@dp.message(AdminForm.age)
async def admin_get_age(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return await cancel_admin_form_msg(message, state)
    await state.update_data(age=message.text)
    await message.answer("⏱️ Сколько времени ты готов уделять?", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1–2 часа", callback_data="time_1_2"),
             InlineKeyboardButton(text="3–4 часа", callback_data="time_3_4")],
            [InlineKeyboardButton(text="5–6 часов", callback_data="time_5_6"),
             InlineKeyboardButton(text="6+ часов", callback_data="time_6_plus")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_form")]
        ]
    ))

@dp.callback_query(F.data == "cancel_admin_form")
async def cancel_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("🚫 Анкета отменена.")
    await show_main_menu(callback.message, state)

async def cancel_admin_form_msg(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Анкета отменена.")
    await show_main_menu(message, state)

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
@dp.callback_query(F.data.startswith("time_"))
async def admin_time(callback: CallbackQuery, state: FSMContext):
    time_map = {
        "time_1_2": "1–2 часа", "time_3_4": "3–4 часа",
        "time_5_6": "5–6 часов", "time_6_plus": "6+ часов"
    }
    await state.update_data(time_commitment=time_map[callback.data])
    await callback.message.answer("🌍 Выбери часовой пояс:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Азия", callback_data="tz_asia"),
             InlineKeyboardButton(text="Россия", callback_data="tz_russia")],
            [InlineKeyboardButton(text="Украина", callback_data="tz_ukraine"),
             InlineKeyboardButton(text="Европа", callback_data="tz_europe")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_form")]
        ]
    ))
    await state.set_state(AdminForm.timezone)

@dp.callback_query(F.data.startswith("tz_"))
async def admin_tz(callback: CallbackQuery, state: FSMContext):
    tz_map = {
        "tz_asia": "Азия", "tz_russia": "Россия",
        "tz_ukraine": "Украина", "tz_europe": "Европа"
    }
    await state.update_data(timezone=tz_map[callback.data])
    await callback.message.delete()
    await state.set_state(AdminForm.experience)
    await callback.message.answer("🧰 Есть ли у тебя админский опыт?", reply_markup=cancel_kb())

@dp.message(AdminForm.experience)
async def step_exp(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return await cancel_admin_form_msg(message, state)
    await state.update_data(experience=message.text)
    await state.set_state(AdminForm.motivation)
    await message.answer("💡 Почему ты хочешь стать админом?", reply_markup=cancel_kb())

@dp.message(AdminForm.motivation)
async def step_mot(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return await cancel_admin_form_msg(message, state)
    await state.update_data(motivation=message.text)
    await state.set_state(AdminForm.conflict)
    await message.answer("🛠 Как ты ответишь на такой текст? Привет… мне сейчас правда очень тяжело. Сегодня утром моя лучшая подруга… она ушла. И это как будто вырвало кусок из меня. Я не понимаю, как такое вообще могло произойти, как она могла оставить меня. Я будто схожу с ума. Прошло всего несколько часов, а я уже слышу её голос, как будто она говорит со мной… просит меня пойти за ней. Это пугает. Я не хочу умирать. Правда не хочу. Но внутри всё как будто кричит, давит, ломает. Я не знаю, как справиться. Я не хочу делать глупостей, но всё будто толкает меня на край. Пожалуйста, просто побудь со мной. Мне очень нужно, чтобы кто-то понял, услышал, просто был рядом.", reply_markup=cancel_kb())

@dp.message(AdminForm.conflict)
async def step_conflict(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return await cancel_admin_form_msg(message, state)
    await state.update_data(conflict=message.text)
    await state.set_state(AdminForm.ideas)
    await message.answer("📈 Какие у тебя идеи для развития проекта?", reply_markup=cancel_kb())

@dp.message(AdminForm.ideas)
async def step_ideas(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return await cancel_admin_form_msg(message, state)
    await state.update_data(ideas=message.text)
    await state.set_state(AdminForm.strengths)
    await message.answer("🏆 Назови свои сильные стороны", reply_markup=cancel_kb())

@dp.message(AdminForm.strengths)
async def step_final(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return await cancel_admin_form_msg(message, state)

    await state.update_data(strengths=message.text)
    data = await state.get_data()

    text = (
        "<b>📨 Новая анкета на админа</b>\n\n"
        f"👤 Username: @{data['username']}\n"
        f"🔢 Возраст: {data['age']}\n"
        f"⏱ Время: {data['time_commitment']}\n"
        f"🌍 Часовой пояс: {data['timezone']}\n"
        f"🧰 Опыт: {data['experience']}\n"
        f"💡 Мотивация: {data['motivation']}\n"
        f"🛠 Конфликты: {data['conflict']}\n"
        f"📈 Идеи: {data['ideas']}\n"
        f"🏆 Сильные стороны: {data['strengths']}"
    )

    try:
        await bot.send_message(ADMINS_CHANNEL, text)
        await message.answer("✅ Спасибо! Мы свяжемся с тобой после рассмотрения.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке анкеты: {e}")

    await state.clear()
    await show_main_menu(message, state)

# --- Состояние чата ---
class ChatStates(StatesGroup):
    chatting = State()

# --- Общение с Альянсом (переписка) ---
@dp.message(F.text == "🌐 Общаться с Альянсом")
async def start_chat(message: Message, state: FSMContext):
    await state.set_state(ChatStates.chatting)
    await message.answer(
        "💬 Можешь просто писать сюда всё, что хочешь передать команде Альянса. Мы обязательно ответим тебе здесь."
        "\n\n❌ Чтобы закончить чат — напиши команду /stop"
    )

@dp.message(StateFilter(ChatStates.chatting))
async def chatting_handler(message: Message, state: FSMContext):
    if message.text.lower() == "/stop":
        await state.clear()
        await message.answer("❌ Чат завершён. Ты всегда можешь начать снова через кнопку 🌐 Общаться с Альянсом.")
        await show_main_menu(message, state)
        return

    user = message.from_user
    text = message.text
    forwarded = await bot.send_message(
        chat_id=SUPPORT_GROUP_ID,
        text=(
            f"📥 Сообщение от <b>@{user.username or user.first_name}</b> (ID: <code>{user.id}</code>):\n\n"
            f"{text}"
        ),
        parse_mode="HTML"
    )
    user_message_map[forwarded.message_id] = user.id
    await message.answer("✅ Твоё сообщение отправлено. Жди ответа.")

# --- Ответ от админа (в группе) ---
@dp.message()
async def admin_reply_handler(message: Message):
    if not message.reply_to_message:
        return

    original_msg_id = message.reply_to_message.message_id
    user_id = user_message_map.get(original_msg_id)

    if not user_id:
        return

    try:
        await bot.send_message(chat_id=user_id, text=f"📩 Ответ от команды Альянса:\n\n{message.text}")
        await message.answer("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")
# --- Запуск бота ---
@dp.message()
async def handle_msg(message: Message):
    await message.answer("Бот работает!")

# "Фейковый" HTTP-сервер для Render
async def handle(request):
    return web.Response(text="Bot is running on Render!")

async def run_web_server():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    print(f"HTTP сервер запущен на порту {PORT}")

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        run_web_server()  # запустить фейковый сервер, чтобы Render не отключил
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Остановлено")
