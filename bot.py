import logging
from aiogram import Bot, Dispatcher, executor, types

print("test")

bot = Bot(token="5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="test1")
async def cmd_test1(message: types.Message):
    await message.reply("Test 1")

executor.start_polling(dp, skip_updates=True)


