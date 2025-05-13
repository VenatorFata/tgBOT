import logging
from telegram.ext import Application, MessageHandler, filters, ConversationHandler, CommandHandler
from config import BOT_TOKEN
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import db_session
from data.users import User

ADDRESS = 'Школа'
DATA_LIST = ['01.08.25', '02.08.25', '03.08.25']
HOURS_LIST_1 = ['9:00', '10:00', '11:00']
HOURS_LIST_2 = ['12:00', '13:00', '14:00']
HOURS_LIST_3 = ['15:00', '16:00', '17:00']
rec_inf = {'name': '', 'date': '', 'time': ''}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я бот для записи в 10 класс. Напишите ФИО ученика, "
        rf"выберите удобное время и я запишу вас на приём! "
        rf"Вы можете прервать запись, послав команду /stop. "
        rf"Введите ФИО", )
    return 1


async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_text("Я умею записывать на приём документов в 10-ые классы. "
                                    "Вы пишите ФИО ученика, которого нужно записать, "
                                    "я присылаю вам адрес и время во сколько приходить. "
                                    "Приём документов осуществляется 01.08.25 с 9:00 до 13:00. "
                                    "На приём документов даётся 15 минут, "
                                    "за раз могут принять документы у трёх человек.")


async def name(update, context):
    rec_inf['name'] = update.message.text
    # Создаем клавиатуру с датами из DATA_LIST
    reply_keyboard = [DATA_LIST]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите удобную дату", reply_markup=markup)
    return 2


async def date(update, context):
    if update.message.text not in DATA_LIST:
        await update.message.reply_text("Пожалуйста, выберите дату из предложенных вариантов.")
        return 2

    rec_inf['date'] = update.message.text

    # Определяем список времени в зависимости от выбранной даты
    if rec_inf['date'] == DATA_LIST[0]:
        hours_list = HOURS_LIST_1
    elif rec_inf['date'] == DATA_LIST[1]:
        hours_list = HOURS_LIST_2
    else:
        hours_list = HOURS_LIST_3

    # Создаем клавиатуру с временем
    reply_keyboard = [hours_list]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите удобное время", reply_markup=markup)
    return 3


async def time(update, context):
    # Проверяем, что выбранное время соответствует доступным вариантам
    selected_time = update.message.text
    if rec_inf['date'] == DATA_LIST[0] and selected_time not in HOURS_LIST_1:
        await update.message.reply_text("Пожалуйста, выберите время из предложенных вариантов.")
        return 3
    elif rec_inf['date'] == DATA_LIST[1] and selected_time not in HOURS_LIST_2:
        await update.message.reply_text("Пожалуйста, выберите время из предложенных вариантов.")
        return 3
    elif rec_inf['date'] == DATA_LIST[2] and selected_time not in HOURS_LIST_3:
        await update.message.reply_text("Пожалуйста, выберите время из предложенных вариантов.")
        return 3

    rec_inf['time'] = selected_time
    await update.message.reply_text(
        f"Вы записаны на приём!\n"
        f"ФИО: {rec_inf['name']}\n"
        f"Дата: {rec_inf['date']}\n"
        f"Время: {rec_inf['time']}\n"
        f"Адрес: {ADDRESS}\n\n"
        f"Пожалуйста, приходите вовремя. На приём документов отводится 15 минут.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text(
        "Успейте записаться до окончания сроков записи!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)]
        },
        fallbacks=[CommandHandler('stop', stop)])

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    # db_session.global_init("db/recording.db")
    # user = User()
    # user.name = rec_inf['name']
    # user.recording_date = rec_inf['date']
    # user.recording_time = rec_inf['time']
    # db_sess = db_session.create_session()
    # db_sess.merge(user)
    # db_sess.commit()
    application.run_polling()


if __name__ == '__main__':
    main()