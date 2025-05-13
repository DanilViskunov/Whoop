import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1vF5i6dw0vgViAltPWMEUkqacc4sYi8mOLmZibaUh2JI").sheet1

# Все этапы доставки
all_statuses = [
    "В обработке у Whoop",
    "В пути на транзитный склад",
    "Отправлен в Москву",
    "На складе в Москве",
    "Отправлен клиенту",
    "Получен клиентом"
]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Просто отправь мне номер заказа (например: B44497297), и я покажу его статус."
    )

# /track <номер>
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        order_number = context.args[0].strip()
        await respond_with_status(update, order_number)
    else:
        await update.message.reply_text("Введите номер заказа после команды /track")

# обычное сообщение
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    await respond_with_status(update, order_number)

# логика ответа
async def respond_with_status(update: Update, order_number: str):
    data = sheet.get_all_records()

    for row in data:
        normalized_row = {k.strip().lower(): v for k, v in row.items()}
        if str(normalized_row.get("номер заказа whoop", "")).strip() == order_number:
            status = str(normalized_row.get("статус заказа", "Не указан")).strip()

            if status in all_statuses:
                index = all_statuses.index(status)
                status_lines = [f"📦 Статус заказа *{order_number}*:\n"]

                for i, step in enumerate(all_statuses):
                    safe_step = (
                        step.replace("-", "\\-")
                        .replace(".", "\\.")
                        .replace("(", "\\(")
                        .replace(")", "\\)")
                        .replace(",", "\\,")
                    )
                    if i < index:
                        status_lines.append(f"✅ {i+1}\\. {safe_step}")
                    elif i == index:
                        status_lines.append(f"*{i+1}\\. {safe_step}* ← текущий статус")
                    else:
                        status_lines.append(f"{i+1}\\. {safe_step}")

                await update.message.reply_text(
                    "\n".join(status_lines), parse_mode="MarkdownV2"
                )
            else:
                safe_status = status.replace("-", "\\-").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace(",", "\\,")
                await update.message.reply_text(
                    f"Статус заказа *{order_number}*: {safe_status}", parse_mode="MarkdownV2"
                )
            return

    await update.message.reply_text("Такой заказ не найден.")

# запуск бота
app = ApplicationBuilder().token("8179328604:AAG1v3PRL-V7vcO_x3heyNhiHrJl3eGQ77A").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("track", track))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()