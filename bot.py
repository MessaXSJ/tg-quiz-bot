import json
from os import getenv
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

with open('questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
Q = data['questions']
A = data['archetypes']

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data.clear()
    kb = [[InlineKeyboardButton("Начать тест 🎭", callback_data="start")]]
    welcome = (
        "🎭 Кто ты из школьных типажей?\n\n"
        "20 вопросов, которые раскроют твою истинную сущность:\n"
        "Альтушка, Задрот, Тиктокер, Ботан, Популярный, "
        "Творец, Качок, Мизантроп, Мемлорд или Меломан?\n\n"
        "Честно отвечай на вопросы — результат тебя удивит! 😎"
    )
    await u.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(kb))

async def restart(u: Update, c: ContextTypes.DEFAULT_TYPE):
    c.user_data.clear()
    kb = [[InlineKeyboardButton("Начать тест", callback_data="start")]]
    await u.message.reply_text("Начинаем заново! 🔄", reply_markup=InlineKeyboardMarkup(kb))

async def btn(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    d = q.data

    if d == "start" or d == "restart":
        c.user_data['sc'] = {k: 0 for k in A}
        c.user_data['qi'] = 0
        c.user_data['history'] = []
        await send_q(q, c)
        return

    if d == "back":
        qi = c.user_data.get('qi', 0)
        if qi > 0 and c.user_data.get('history'):
            last_scores = c.user_data['history'].pop()
            for k, v in last_scores.items():
                c.user_data['sc'][k] -= v
            c.user_data['qi'] = qi - 1
        await send_q(q, c)
        return

    qi = c.user_data.get('qi', 0)
    ai = int(d)
    scores = Q[qi]['answers'][ai]['scores']

    if 'history' not in c.user_data:
        c.user_data['history'] = []
    c.user_data['history'].append(scores)

    for k, v in scores.items():
        c.user_data['sc'][k] += v

    c.user_data['qi'] = qi + 1

    if c.user_data['qi'] >= len(Q):
        await show_result(q, c)
    else:
        await send_q(q, c)

async def send_q(q, c: ContextTypes.DEFAULT_TYPE):
    qi = c.user_data['qi']
    qd = Q[qi]
    kb = [[InlineKeyboardButton(a['text'], callback_data=str(i))] for i, a in enumerate(qd['answers'])]
    if qi > 0:
        kb.append([InlineKeyboardButton("← Назад", callback_data="back")])
    txt = f"Вопрос {qi+1}/{len(Q)}\n\n{qd['text']}"
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def show_result(q, c: ContextTypes.DEFAULT_TYPE):
    sc = c.user_data['sc']
    win = max(sc, key=sc.get)
    r = A[win]
    txt = f"{r['emoji']} {r['name']}\n\n{r['description']}"
    kb = [[InlineKeyboardButton("Пройти заново", callback_data="restart")]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def setup_commands(app: Application):
    commands = [
        BotCommand("start", "Начать тест"),
        BotCommand("restart", "Начать заново")
    ]
    await app.bot.set_my_commands(commands)

app = Application.builder().token(getenv('BOT_TOKEN')).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("restart", restart))
app.add_handler(CallbackQueryHandler(btn))

app.post_init = setup_commands
app.run_polling()
