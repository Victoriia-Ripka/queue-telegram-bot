import logging
from aiogram import Bot, Dispatcher, executor, types

# Объект бота
bot = Bot(token="5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k")
# Диспетчер для бота
dp = Dispatcher(bot)
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)


# Хэндлер на команду /test1
@dp.message_handler(commands="test1")
async def cmd_test1(message: types.Message):
    await message.reply("Test 1")

executor.start_polling(dp, skip_updates=True)
