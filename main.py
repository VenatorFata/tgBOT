import logging
from telegram.ext import Application, MessageHandler, filters, ConversationHandler, CommandHandler
from config import BOT_TOKEN  # Токен бота из файла config.py
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove  # Для создания клавиатур
from data import db_session  # Для работы с базой данных
from data.users import User  # Модель пользователя из базы данных

# Константы с адресом, датами и временем записи
ADDRESS = 'Школа'
DATA_LIST = ['01.08.25', '02.08.25', '03.08.25']
HOURS_LIST_1 = ['9:00', '10:00', '11:00']
HOURS_LIST_2 = ['12:00', '13:00', '14:00']
HOURS_LIST_3 = ['15:00', '16:00', '17:00']

# Словарь для хранения временных данных о записи
rec_inf = {'name': '', 'date': '', 'time': ''}

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Отправляет сообщение когда получена команда /start
async def start(update, context):
    user = update.effective_user  # Получаем информацию о пользователе
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я бот для записи в 10 класс. Напишите ФИО ученика, "
        rf"выберите удобное время и я запишу вас на приём! "
        rf"Вы можете прервать запись, послав команду /stop. "
        rf"Введите ФИО", )
    return 1  # Переход к следующему ожиданию ФИО


# Отправляет сообщение когда получена команда /help
async def help_command(update, context):
    await update.message.reply_text("Я умею записывать на приём документов в 10-ые классы. "
                                    "Вы пишите своё ФИО, "
                                    "я присылаю вам адрес и время во сколько приходить. "
                                    "Приём документов осуществляется 01.08.25 с 9:00 до 13:00. "
                                    "На приём документов даётся 15 минут, "
                                    "за раз могут принять документы у трёх человек.")


# Обрабатывает введенное ФИО и предлагает выбрать дату
async def name(update, context):
    rec_inf['name'] = update.message.text  # Сохраняем ФИО
    # Создаем клавиатуру с датами
    reply_keyboard = [DATA_LIST]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите удобную дату", reply_markup=markup)
    return 2  # Переход к выбору даты


# Обрабатывает выбранную дату и предлагает время
async def date(update, context):
    if update.message.text not in DATA_LIST:  # Проверка корректности даты
        await update.message.reply_text("Пожалуйста, выберите дату из предложенных.")
        return 2  # Выбираем дату заново

    rec_inf['date'] = update.message.text  # Сохраняем дату

    # Выбираем список времени в зависимости от даты
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
    return 3  # Переход к выбору времени


# Обрабатывает выбранное время и завершает запись
async def time(update, context):
    selected_time = update.message.text
    # Проверка корректности времени для выбранной даты
    if rec_inf['date'] == DATA_LIST[0] and selected_time not in HOURS_LIST_1:
        await update.message.reply_text("Пожалуйста, выберите время из предложенных.")
        return 3
    # Проверки для других дат

    rec_inf['time'] = selected_time  # Сохраняем время

    # Отправляем подтверждение записи
    await update.message.reply_text(
        f"Вы записаны на приём!\n"
        f"ФИО: {rec_inf['name']}\n"
        f"Дата: {rec_inf['date']}\n"
        f"Время: {rec_inf['time']}\n"
        f"Адрес: {ADDRESS}\n\n"
        f"Пожалуйста, приходите вовремя. На приём документов отводится 15 минут.",
        reply_markup=ReplyKeyboardRemove()
    )
    # Сохраняем запись в БД
    dbsession(rec_inf['name'], rec_inf['date'], rec_inf['time'])
    return ConversationHandler.END  # Завершаем диалог


# Обработчик команды /stop - прерывает процесс записи
async def stop(update, context):
    await update.message.reply_text(
        "Успейте записаться до окончания сроков записи!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# Сохраняет запись в базу данных
def dbsession(cur_name, cur_date, cur_time):
    db_session.global_init("db/recording.db")
    user = User()  # Создаем объект пользователя
    user.name = cur_name
    user.recording_date = cur_date
    user.recording_time = cur_time
    db_sess = db_session.create_session()  # Создаем сессию
    db_sess.merge(user)  # Сохраняем или обновляем запись
    db_sess.commit()  # Фиксируем изменения


# Запуск бота
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    # Настройка обработчика диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],  # команда /start
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],  # Ожидание ФИО
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],  # Ожидание даты
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)]  # Ожидание времени
        },
        fallbacks=[CommandHandler('stop', stop)]  # Прерывание по команде /stop
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))  # Обработчик инструкции
    application.run_polling()  # Запуск бота


if __name__ == '__main__':
    main()
