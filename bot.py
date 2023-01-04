from datetime import datetime
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import db

API_TOKEN = '5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

my_cursor = db.mydb.cursor()


class Form(StatesGroup):
    subject = State()
    teacher = State()

    create_queue_st = State()
    clear_queue_st = State()
    delete_queue_st = State()


@dp.message_handler(commands="start")
async def start(message: types.Message):
    chat_name = "user"
    # chat_name = message["chat"]["first_name"]
    # how to get chat_name in chat and use it in answer?
    await message.answer(f"hello, {chat_name}")


@dp.message_handler(commands="help")
async def help(message: types.Message):
    text = "all commands definitions will be here soon"
    await message.answer(text)


@dp.message_handler(commands="end")
async def end(message: types.Message):
    print("Start deletind DB...")
    sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Teachers` ;"""
    my_cursor.execute(sql_command)
    sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Sign_ups` ;"""
    my_cursor.execute(sql_command)
    sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Queues` ;"""
    my_cursor.execute(sql_command)
    sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Students` ;"""
    my_cursor.execute(sql_command)
    sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Subjects` ;"""
    my_cursor.execute(sql_command)
    print("All tables are deleted")
    text = "All tables are deleted"
    await message.answer(text)


@dp.message_handler(commands='add_subject')
async def insert_workmate(message: types.Message):
    try:
        await Form.subject.set()
        await message.answer("""WRITE\nsubject title""")

    except Exception as e:
        print(e)
        await message.answer("Conversation Terminated✔")
        return


@dp.message_handler(state=Form.subject)
async def insert_workmate(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    try:
        title = data[0].title()
        teacher_id = data[1]
    except ValueError:
        await state.finish()
        await message.answer("sorry, you input wrong data type. please, try again")
        return

    if isinstance(title, str) and isinstance(teacher_id, int):
        new_subject = (title, teacher_id)
        sql = "INSERT INTO Subjects (subject_id, title, id_teacher) VALUES (NULL, %s, %s);"
        my_cursor.execute(sql, new_subject)
        db.mydb.commit()

    await state.finish()
    # maybe should add some errors handle
    if my_cursor.rowcount < 1:
        await message.answer("Something went wrong, please try again")
    else:
        await message.answer(title, " correctly inserted")


@dp.message_handler(commands='add_teacher')
async def insert_workmate(message: types.Message):
    try:
        await Form.teacher.set()
        await message.answer("""WRITE\nusername_telegram, phone_number, email, additional info""")

    except Exception as e:
        print(e)
        await message.answer("Conversation Terminated✔")
        return


@dp.message_handler(state=Form.teacher)
async def insert_workmate(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    try:
        nusername_telegram = data[0].title()
        # how to set NULL to fields
        phone_number = data[1]  # may contain nothing
        email = data[2]  # may contain nothing
        info = data[3]  # may contain nothing
    except ValueError:
        await state.finish()
        await message.answer("sorry, you input wrong data type. please, try again")
        return

    if isinstance(nusername_telegram, str):
        new_teacher = (nusername_telegram, phone_number, email, info)
        sql = "INSERT INTO Teachers (id_teacher, username_telegram, phone_number, email, info) VALUES (NULL, %s, %s, %s, %s);"
        my_cursor.execute(sql, new_teacher)
        db.mydb.commit()

    await state.finish()
    # maybe should add some errors handle
    if my_cursor.rowcount < 1:
        await message.answer("Something went wrong, please try again")
    else:
        await message.answer(nusername_telegram, " correctly inserted")


def get_subjects():
    my_cursor.execute("SELECT DISTINCT title FROM subjects;")
    result = my_cursor.fetchall()

    subjects = []
    for subject in result:
        subjects.append(subject[0])

    return subjects


def get_subjects_with_queues():
    my_cursor.execute("""SELECT DISTINCT title FROM subjects
                      WHERE subject_id IN
                      (SELECT subject_id FROM queues);""")
    result = my_cursor.fetchall()

    subjects_with_queues = []
    for subject in result:
        subjects_with_queues.append(subject[0])

    return subjects_with_queues


@dp.message_handler(commands='create_queue')
async def create_queue(message: types.Message):
    await Form.create_queue_st.set()
    subjects = get_subjects()
    if subjects:
        str = "Select one lesson from list:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{i + 1}. {subject}\n"
        str += "If wanted lesson not in list, add it by command /add_lesson"
    else:
        str = "Oups! Lesson list is empty. You can add lesson by /add_lesson"
    await message.answer(str)


@dp.message_handler(state=Form.create_queue_st)
async def create_queue(message: types.Message, state: FSMContext):
    subjects = get_subjects()
    subjects_with_queues = get_subjects_with_queues()

    data = message.values["text"]

    #  Вибір предмету відбувається написання назвою або номером
    try:  # Спроба конвертації користувацького вводу як інтове число. Якщо не виходить - сприймаємо як назву
        if 0 < int(data) <= len(subjects):
            subject = subjects[int(data) - 1]
        else:
            await message.answer(f"Subject by number {data} is unknown. You can add lesson by /add_lesson")
            await state.finish()
            return

    except ValueError:
        subject = data

    if subject in subjects_with_queues:
        await message.answer(f"Queue by lesson {subject} already exist")
        await state.finish()
        return
    else:
        get_subject_id = """SELECT subject_id
                            FROM subjects
                            WHERE title = %s;"""
        my_cursor.execute(get_subject_id, (subject,))
        subject_id = my_cursor.fetchone()

        if subject_id:
            my_cursor.execute("INSERT INTO queues (id_queue, subject_id) VALUES(DEFAULT, %s)", subject_id)
            db.mydb.commit()
            await message.answer(f"Queue by lesson {subject} was created")
        else:
            await message.answer(f"Lesson {subject} not in list")

    await state.finish()
    return


@dp.message_handler(commands='clear_queue')
async def clear_queue(message: types.Message):
    await Form.clear_queue_st.set()
    subjects = get_subjects()
    if subjects:
        str = "Чергу на який предмет ви хочетете очистити?:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{i + 1}. {subject}\n"
    await message.answer(str)


@dp.message_handler(state=Form.clear_queue_st)
async def clear_queue(message: types.Message, state: FSMContext):
    subjects = get_subjects()
    subjects_with_queues = get_subjects_with_queues()

    data = message.values["text"]

    try:
        if 0 < int(data) <= len(subjects):
            subject = subjects[int(data) - 1]
        else:
            await message.answer(f"Subject by number {data} is unknown. You can add lesson by /add_lesson")
            await state.finish()
            return

    except ValueError:
        subject = data

    if subject in subjects:
        if subject in subjects_with_queues:
            delete_users = """DELETE sign_ups FROM sign_ups
                              JOIN queues
                                     USING(id_queue)
                              JOIN subjects sb
                                     USING(subject_id)
                              WHERE sb.title = %s;
                              """

            my_cursor.execute(delete_users, (subject,))
            db.mydb.commit()
            await message.answer(f"Черга на предмет {subject} була очищена")
        else:
            await message.answer(f"Черга на предмет {subject} ще не створення."
                                 f" Ви можете сторити її командую /create_queue")
    else:
        await message.answer(f"Subject {data} is unknown. You can add lesson by /add_lesson")
    await state.finish()
    return


@dp.message_handler(commands='delete_queue')
async def delete_queue(message: types.Message):
    await Form.delete_queue_st.set()
    subjects = get_subjects()
    if subjects:
        str = "Select one lesson from list:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{i + 1}. {subject}\n"
        str += "If wanted lesson not in list, add it by command /add_lesson"
    else:
        str = "Oups! Lesson list is empty. You can add lesson by /add_lesson"
    await message.answer(str)


@dp.message_handler(state=Form.delete_queue_st)
async def delete_queue(message: types.Message, state: FSMContext):
    subjects = get_subjects()
    subjects_with_queues = get_subjects_with_queues()

    data = message.values["text"]

    try:
        if 0 < int(data) <= len(subjects):
            subject = subjects[int(data) - 1]
        else:
            await message.answer(f"Subject by number {data} is unknown. You can add lesson by /add_lesson")
            await state.finish()
            return
    except ValueError:
        subject = data
    if subject in subjects:
        if subject in subjects_with_queues:
            delete_users = """DELETE queues FROM queues
                              JOIN subjects sb
                                     USING(subject_id)
                              WHERE sb.title = %s;
                              """
            my_cursor.execute(delete_users, (subject,))
            db.mydb.commit()
            await message.answer(f"Черга на предмет {subject} була видалена")
        else:
            await message.answer(f"Черга на предмет {subject} ще не створення."
                                 f" Ви можете сторити її командую /create_queue")
    else:
        await message.answer(f"Subject {data} is unknown. You can add lesson by /add_lesson")
    await state.finish()
    return


if __name__ == '__main__':
    try:
        print("Initializing Database...")
        print("Connected to the database")

        # Command that creates the "oders" table
        sql_command = """CREATE DATABASE IF NOT EXISTS `queue-bot-kpi` DEFAULT CHARACTER SET utf8 ;"""
        my_cursor.execute(sql_command)
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Subjects` (
  `subject_id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(100) NOT NULL,
  `id_teacher` INT NOT NULL,
  PRIMARY KEY (`subject_id`),
  UNIQUE INDEX `title_UNIQUE` (`title` ASC) VISIBLE,
  UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
  UNIQUE INDEX `id_teacher_UNIQUE` (`id_teacher` ASC) VISIBLE);"""
        my_cursor.execute(sql_command)
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Students` (
  `telegram_user_id` INT NOT NULL,
  `username` VARCHAR(45) NULL,
  `firstname` VARCHAR(45) NULL,
  PRIMARY KEY (`telegram_user_id`),
  UNIQUE INDEX `telegram_user_id_UNIQUE` (`telegram_user_id` ASC) VISIBLE,
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE);"""
        my_cursor.execute(sql_command)
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Queues` (
  `id_queue` INT NOT NULL AUTO_INCREMENT,
  `subject_id` INT NOT NULL,
  PRIMARY KEY (`id_queue`),
  UNIQUE INDEX `id_queue_UNIQUE` (`id_queue` ASC) VISIBLE,
  UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
  CONSTRAINT `subject_id fk from Queue to Subjects`
    FOREIGN KEY (`subject_id`)
    REFERENCES `queue-bot-kpi`.`Subjects` (`subject_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE);"""
        my_cursor.execute(sql_command)
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Sign_ups`
(
    `id_sign_up`       INT NOT NULL AUTO_INCREMENT,
    `id_queue`         INT NOT NULL,
    `telegram_user_id` INT NOT NULL,
    `position`         INT NOT NULL,
    PRIMARY KEY (`id_sign_up`),
    UNIQUE INDEX `telegram_user_id_UNIQUE` (`telegram_user_id` ASC) VISIBLE,
    CONSTRAINT `id_queue fk from Sign_ups to Queue`
        FOREIGN KEY (`id_queue`)
            REFERENCES `queue-bot-kpi`.`Queues` (`id_queue`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `telegram_user_id fk from Sign_ups to Students`
        FOREIGN KEY (`telegram_user_id`)
            REFERENCES `queue-bot-kpi`.`Students` (`telegram_user_id`)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION);"""
        my_cursor.execute(sql_command)
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Teachers` (
  `id_teacher` INT NOT NULL AUTO_INCREMENT,
  `username_telegram` VARCHAR(45) NULL,
  `phone_number` CHAR(13) NULL,
  `email` VARCHAR(60) NULL,
  `info` TEXT(1000) NULL,
  PRIMARY KEY (`id_teacher`),
  UNIQUE INDEX `id_teacher_UNIQUE` (`id_teacher` ASC) VISIBLE,
  UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  CONSTRAINT `id_teacher fk from Teachers to Subjects`
    FOREIGN KEY (`id_teacher`)
    REFERENCES `queue-bot-kpi`.`Subjects` (`id_teacher`)
    ON DELETE NO ACTION
    ON UPDATE CASCADE);"""
        my_cursor.execute(sql_command)
        print("All tables are ready")
        print("Bot Started")
        executor.start_polling(dp, skip_updates=True)

    except Exception as error:
        print('Cause: {}'.format(error))
