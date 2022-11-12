import telebot

# треба ще лібу цю скачати
# pip install pyTelegramBotAPI

bot = telebot.TeleBot('5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.infinity_polling()
