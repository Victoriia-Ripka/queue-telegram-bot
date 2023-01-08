from datetime import datetime
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import db

API_TOKEN = '5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k'

bot = Bot(token=API_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

my_cursor = db.mydb.cursor()

active_subject = ''
active_student = 0


class Form(StatesGroup):
    subject = State()
    teacher = State()
    info = State()
    update_subject = State()
    update_teacher = State()
    delete_subject = State()
    delete_teacher = State()

    create_queue_st = State()
    clear_queue_st = State()
    delete_queue_st = State()

    show_queue_st = State()
    start_queue_st = State()


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


# @dp.message_handler(commands="end")
# async def end(message: types.Message):
#     print("Start deletind DB...")
#     sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Teachers` ;"""
#     my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Sign_ups` ;"""
#     my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Queues` ;"""
#     my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Students` ;"""
#     my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `queue-bot-kpi`.`Subjects` ;"""
#     my_cursor.execute(sql_command)
#     print("All tables are deleted")
#     text = "All tables are deleted"
#     await message.answer(text)


@dp.message_handler(commands='add_subject')
async def add_subject_start(message: types.Message):
    subjects = get_subjects()
    str = ""
    if subjects:
        str = "Список предметів:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{i + 1}. {subject}\n"
    else:
        str = "Список предметів пустий.\nВпишіть назву нового предмета та id викладача"
    
    teachers = get_teachers_with_id()
    if teachers:
        await Form.subject.set()
        str += "Список викладачів:\n"
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f"{teacher[0]}: {teacher[1]}\n"
        str += "Впишіть назву предмета та id викладача"
    else:
        str = "Список викладачів пустий.\nСпочатку створіть список викладачів /add_teacher"
        # await FSMContext.finish()
    await message.answer(str)
    return 


@dp.message_handler(state=Form.subject)
async def add_subject(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    if len(data) >= 2:
        teacher_id = int(data[len(data)-1])
        separator = "_"
        data.pop()
        title = separator.join(data)
        if not isinstance(teacher_id, int) or not isinstance(title, str):
            await state.finish()
            await message.answer(f"Ви ввели непривильні дані. Спробуйте ще раз /add_subject 2")
            return
    else:
        await state.finish()
        await message.answer("Ви ввели непривильні дані. Спробуйте ще раз /add_subject 1")
        return
    
    new_subject = (title, teacher_id)
    sql = "INSERT INTO Subjects (subject_id, title, id_teacher) VALUES (NULL, %s, %s);"
    my_cursor.execute(sql, new_subject)
    db.mydb.commit() 
    
    # maybe should add some errors handle
    if my_cursor.rowcount < 1:
        await message.answer("Щось пішло не так. Спробуйте ще раз /add_subject 3")
    else:
        await message.answer(f"{title} додан до списку")
    await state.finish()
    return       
    

@dp.message_handler(commands='add_teacher')
async def add_teacher_start(message: types.Message):
    await Form.teacher.set()
    teachers = get_teachers()
    if teachers:
        str = "Список викладачів:\n"
        for subject, i in zip(teachers, range(len(teachers))):
            str += f"{i + 1}. {subject}\n"
        str += "Впишіть ім'я викладача.\nЗа бажанням можете вписати телеграм-тег, номер телефону, email"
    else:
        str = "Список викладачів пустий.\nВпишіть ім'я викладача.\nЗа бажанням можете вписати телеграм-тег, номер телефону, email"
    await message.answer(str)


@dp.message_handler(state=Form.teacher)
async def add_teacher(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    if len(data) == 1:
        name = data[0]
        if not name.isalpha():
            await state.finish()
            await message.answer("Щось пішло не так. Спробуйте ще раз /add_teacher")
            return
        new_teacher = (name, )
        sql = "INSERT INTO Teachers (id_teacher, name) VALUES (NULL, %s);"
        my_cursor.execute(sql, new_teacher)  
        db.mydb.commit() 
    elif len(data) == 4:
        name = data[0]
        username_telegram = data[1]
        phone_number = data[2]
        email = data[3] 
        if not name.isalpha() or not isinstance(email, str) or not isinstance(username_telegram, str):
            await state.finish()
            await message.answer("Щось пішло не так. Спробуйте ще раз /add_teacher")
            return
        new_teacher = (name, username_telegram, phone_number, email)
        sql = "INSERT INTO Teachers (id_teacher, name, username_telegram, phone_number, email) VALUES (NULL, %s, %s, %s, %s);"
        my_cursor.execute(sql, new_teacher)  
        db.mydb.commit() 
    else:
        await state.finish()
        await message.answer("Щось пішло не так. Спробуйте ще раз /add_teacher")
        return
    
    if my_cursor.rowcount < 1:
        await message.answer("Щось пішло не так. Спробуйте ще раз /add_teacher")
    else:
        await message.answer(f"{name} додан до списку")
    await state.finish()


@dp.message_handler(commands='add_teacher_info')
async def add_teacher_info_start(message: types.Message):
    await Form.info.set()
    teachers = get_teachers_with_id()
    if teachers:
        str = "Список викладачів:\n"
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f"{teacher[0]}. {teacher[1]}\n"
        str += "Впишіть id викладача.\nПісля цього додайте всю необхідну інформацію"
    else:
        str = "Список викладачів пустий.\nСпочатку додайте викладача /add_teacher"
    await message.answer(str)


@dp.message_handler(state=Form.info)
async def add_teacher_info(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    if len(data) >= 2:
        try:
            id = int(data[0])
        except:
            await state.finish()
            await message.answer("Першим повинен бути id і це число. Спробуйте ще раз /add_teacher_info")
            return
        separator = " "
        del data[0]
        info = separator.join(data)
        if not isinstance(info, str) or not isinstance(id, int):
            await state.finish()
            await message.answer("Щось пішло не так. Спробуйте ще раз /add_teacher_info 1")
            return
        new_info = (info, id)
        sql = "UPDATE Teachers SET info = %s WHERE id_teacher = %s;"
        my_cursor.execute(sql, new_info)  
        db.mydb.commit() 
    else:
        await state.finish()
        await message.answer("Щось пішло не так. Спробуйте ще раз /add_teacher_info 2")
        return
    
    if my_cursor.rowcount < 1:
        await message.answer("Щось пішло не так. Спробуйте ще раз /add_teacher_info 3")
    else:
        await message.answer(f"Інформація додана")
    await state.finish()


@dp.message_handler(commands='update_subject')
async def update_subject_start(message: types.Message):
    await Form.update_subject.set()
    subjects = get_subjects_with_teachers()
    if subjects:
        str = "Список предметів:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{subject[0]}. {subject[1]} - {subject[2]}\n"
        
        teachers = get_teachers_with_id()
        str += "Список викладачів:\n"
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f"{teacher[0]}: {teacher[1]}\n"
        str += "Напишіть id предмета, нову назву предмета та id викладача"
    else:
        str = "Список предметів пустий. Додайте предмет /add_subject\n"
    await message.answer(str)
    return 


@dp.message_handler(state=Form.update_subject)
async def update_subject(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    if len(data) > 2:
        id = data[0]
        teacher_id = data[len(data)-1]
        separator = "_"
        del data[0]
        del data[len(data)-1]
        title = separator.join(data)
        if not isinstance(title, str):
            await message.answer("Ви ввели непривильні дані. Спробуйте ще раз. Напишіть id предмета, нову назву предмета та id викладача /update_subject")
    else:
        await message.answer("Ви ввели непривильні дані. Спробуйте ще раз. Напишіть id предмета, нову назву предмета та id викладача /update_subject")

    try: 
        new_subject = (title, int(teacher_id), int(id))
        sql = "UPDATE Subjects SET title = %s, id_teacher = %s WHERE subject_id = %s;"
        my_cursor.execute(sql, new_subject)
        db.mydb.commit() 
    except:
        await state.finish()
        await message.answer("Щось пішло не так. Спробуйте ще раз /update_subject")
        return
    
    if my_cursor.rowcount < 1:
        await message.answer("Щось пішло не так. Спробуйте ще раз /update_subject")
    else:
        await message.answer(f"{title} успішно оновлен")
    await state.finish()
    return


@dp.message_handler(commands='update_teacher')
async def update_teacher_start(message: types.Message):
    await Form.update_teacher.set()
    teachers = get_teachers_with_all_info()
    if teachers:
        str = "Список викладачів:\n"
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f"{teacher[0]}. {teacher[1]} - {teacher[4]} {teacher[2]} {teacher[3]}\n"
        str += "Впишіть id викладача. Після цього ім'я, нік в телеграмі, номер телефону та email\n(Якщо якоїсь інформації нема поставте -)"
    else:
        str = "Список викладачів пустий.\nДодайте викладачів до списку /add_teacher"
    await message.answer(str)


@dp.message_handler(state=Form.update_teacher)
async def update_teacher(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    if len(data) == 5:
        id = data[0]
        name = data[1]
        username_telegram = data[2]
        phone_number = data[3]  
        email = data[4]  
        if not isinstance(id, int) and not isinstance(username_telegram, str):
            await message.answer("Щось пішло не так. Спробуйте ще раз /update_teacher")
    else:
        await message.answer("Щось пішло не так. Спробуйте ще раз /update_teacher")

    try:
        new_teacher = (name, username_telegram, phone_number, email, id)
        sql = "UPDATE Teachers SET name = %s, username_telegram = %s, phone_number = %s, email = %s WHERE id_teacher = %s"
        my_cursor.execute(sql, new_teacher)  
        db.mydb.commit() 
        await state.finish()
    except:
        await state.finish()
        await message.answer("Щось пішло не так. Спробуйте ще раз /update_teacher")
        return
    
    if my_cursor.rowcount < 1:
        await message.answer("Щось пішло не так. Спробуйте ще раз /update_teacher")
    else:
        await message.answer(f"{username_telegram} оновлен")
    await state.finish()
    return    


@dp.message_handler(commands='delete_subject')
async def delete_subject_start(message: types.Message):
    await Form.delete_subject.set()
    subjects = get_subjects_with_id()
    str = "Список предметів:\n"
    for subject, i in zip(subjects, range(len(subjects))):
        str += f"{subject[0]}: {subject[1]}\n"
    str += "Напишіть id предмета, що потрібно видалити"
    await message.answer(str)
    return 


@dp.message_handler(state=Form.delete_subject)
async def delete_subject(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    if len(data) == 1:
        try:
            id = int(data[0])
        except:
            await state.finish()
            await message.answer("Id це число, йолопе. Спробуй ще раз /delete_subject")
            return
    else: 
        await state.finish()
        await message.answer("Введи ОДНЕ ЧИСЛО - id. Спробуй ще раз /delete_subject")
        return
        
    sql = "DELETE FROM Subjects WHERE subject_id = %s;"
    my_cursor.execute(sql, (id,)) 
    db.mydb.commit() 
    
    if my_cursor.rowcount < 1:
        await message.answer("Такого Id немає в списку. Спробуй ще раз /delete_subject")
    else:
        await message.answer(f"Предмет видален")
    await state.finish()
    return


@dp.message_handler(commands='delete_teacher')
async def delete_teacher_start(message: types.Message):
    await Form.delete_teacher.set()
    teachers = get_teachers_with_id()
    str = "Список викладачів:\n"
    for teacher, i in zip(teachers, range(len(teachers))):
        str += f"{teacher[0]}: {teacher[1]}\n"
    str += "Напишіть id викладача, що потрібно видалити\nЯкщо викладач викладає якийсь предмет - його видалити неможливо"
    await message.answer(str)
    return     


@dp.message_handler(state=Form.delete_teacher)
async def delete_teacher(message: types.Message, state: FSMContext):
    data = message.values["text"].split(" ")
    if len(data) == 1:
        try: 
            id = int(data[0])
            sql = "DELETE FROM Teachers WHERE id_teacher = %s;"
            my_cursor.execute(sql, (id,))  
            db.mydb.commit()
        except:
            await state.finish()
            await message.answer("Id це число, йолопе (або викладач викладає предмет). Спробуй ще раз /delete_teacher")
            return
    else: 
        await state.finish()
        await message.answer("Введи ОДНЕ ЧИСЛО - id. Спробуй ще раз /delete_teacher")
        return
    
    if my_cursor.rowcount < 1:
        await message.answer("Такого Id немає в списку. Спробу ще раз /delete_teacher")
    else:
        await message.answer(f"Вчитель видален")
    await state.finish()
    return




def get_teachers():
    my_cursor.execute("SELECT DISTINCT name FROM teachers;")
    result = my_cursor.fetchall()

    teachers = []
    for teacher in result:
        teachers.append(teacher[0])

    return teachers

def get_teachers_with_id():
    my_cursor.execute("SELECT DISTINCT id_teacher, name FROM teachers;")
    result = my_cursor.fetchall()

    teachers = []
    for teacher in result:
        teachers.append((teacher[0], teacher[1]))

    return teachers

def get_teachers_with_all_info():
    my_cursor.execute("SELECT * FROM teachers;")
    result = my_cursor.fetchall()

    teachers = []
    for teacher in result:
        teachers.append((teacher[0], teacher[1], teacher[2], teacher[3], teacher[4], teacher[5]))

    return teachers

def get_subjects():
    my_cursor.execute("SELECT DISTINCT title FROM subjects;")
    result = my_cursor.fetchall()

    subjects = []
    for subject in result:
        subjects.append(subject[0])

    return subjects

def get_subjects_with_id():
    my_cursor.execute("SELECT DISTINCT subject_id, title FROM subjects;")
    result = my_cursor.fetchall()

    subjects = []
    for subject in result:
        subjects.append((subject[0], subject[1]))

    return subjects

def get_subjects_with_teachers():
    my_cursor.execute("""SELECT subject_id, title, name
        FROM `queue-bot-kpi`.`Subjects`
        INNER JOIN `queue-bot-kpi`.`Teachers` ON Subjects.id_teacher = Teachers.id_teacher;""")
    result = my_cursor.fetchall()

    subjects = []
    for subject in result:
        subjects.append((subject[0], subject[1], subject[2]))

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


def get_subject_id(subject=None):
    act_sb = subject if subject else active_subject

    query = f"""SELECT subject_id
                FROM subjects
                WHERE title = '{act_sb}';"""
    my_cursor.execute(query)

    temp = my_cursor.fetchone()

    if temp:
        subject_id = temp[0]
        return subject_id
    else:
        return 0


@dp.message_handler(commands='create_queue')
async def create_queue(message: types.Message):
    await Form.create_queue_st.set()
    subjects = get_subjects()
    if subjects:
        str = "Список предметів:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{i + 1}. {subject}\n"
        str += "Ви можете додати предмет командою /add_lesson"
    else:
        str = "Список предметів пустий. Ви можете додати предмет командою /add_lesson"
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
            await message.answer(f"Предмет за номером {data} невідомий. Ви можете додати предмет командою /add_lesson")
            await state.finish()
            return

    except ValueError:
        subject = data

    if subject in subjects_with_queues:
        await message.answer(f"Черга на {subject} вже існує")
        await state.finish()
        return
    else:
        subject_id = get_subject_id(subject)

        if subject_id:
            my_cursor.execute("INSERT INTO queues (id_queue, subject_id) VALUES(DEFAULT, %s)", (subject_id,))
            db.mydb.commit()
            await message.answer(f"Чергу на предмет {subject} створено")
        else:
            await message.answer(f"Предмета {subject} немає у списку."
                                 f" Ви можете додати новий предмет командою /add_lesson")

    await state.finish()
    return


@dp.message_handler(commands='clear_queue')
async def clear_queue(message: types.Message):
    await Form.clear_queue_st.set()
    subjects = get_subjects()
    if subjects:
        str = "Чергу на який предмет Ви хочетете очистити?:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{i + 1}. {subject}\n"
    else:
        str = "Список предметів пустий. Ви можете додати предмет командою /add_lesson"
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
            await message.answer(f"Предмет за номером {data} невідомий. Ви можете додати предмет командою /add_lesson")
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
        await message.answer(f"Предмета {subject} немає у списку."
                             f" Ви можете додати новий предмет командою /add_lesson")
    await state.finish()
    return


@dp.message_handler(commands='delete_queue')
async def delete_queue(message: types.Message):
    await Form.delete_queue_st.set()
    subjects = get_subjects()
    if subjects:
        str = "Список предметів:\n"
        for subject, i in zip(subjects, range(len(subjects))):
            str += f"{i + 1}. {subject}\n"
        str += "Ви можете додати предмет командою /add_lesson"
    else:
        str = "Список предметів пустий. Ви можете додати предмет командою /add_lesson"
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
            await message.answer(f"Предмет за номером {data} невідомий. Ви можете додати предмет командою /add_lesson")
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
            await message.answer(f"Черга на предмет {subject} ще не створена."
                                 f" Ви можете сторити її командую /create_queue")
    else:
        await message.answer(f"Предмет за {subject} невідомий. Ви можете додати предмет командою /add_lesson")
    await state.finish()
    return


@dp.message_handler(commands='show_needed_queue')
async def show_needed_queue(message: types.Message):
    await Form.show_queue_st.set()
    subjects_with_queues = get_subjects_with_queues()

    if subjects_with_queues:
        str = "Виберіть предмет, на який шукаєте чергу:\n"
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            str += f"{i + 1}. {subject}\n"
        str += "\nЯкщо на ваш предмет ще немає черги, ви можете створити її командою /create_queue\n"
    else:
        str = "Ще не створено жодної черги.\n\n"
        str += "Створити чергу: /create_queue\n"

    str += "Отримати всі предмети: /get_subjects\n"
    str += "Додати предмет: /add_subject"

    await message.answer(str)


@dp.message_handler(state=Form.show_queue_st)
async def show_needed_queue(message: types.Message, state: FSMContext):
    subjects_with_queues = get_subjects_with_queues()

    data = message.values["text"]
    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects_with_queues):
            subject = subjects_with_queues[data - 1]
        else:
            await message.answer(f"Немає черги на предмет під номером {data}.\n"
                                 f"Ви можете створити чергу (/create_queue) або додати предмет (/add_subject).")
            await state.finish()
            return

    queue_str = queue_to_str(fetch_queue(get_subject_id(subject)))

    await message.answer(queue_str)

    print(active_subject)

    await state.finish()

    return


def fetch_queue(subject_id):
    query = f"""SELECT position, username, firstname
                FROM sign_ups
                INNER JOIN students
                ON sign_ups.telegram_user_id = students.telegram_user_id
                AND id_queue = (SELECT id_queue FROM queues
                                WHERE subject_id = {subject_id})
                ORDER BY position;"""
    my_cursor.execute(query)
    queue = my_cursor.fetchall()

    return queue


def get_sign_up(subject=None, student=None):
    act_sb = subject if subject else active_subject
    act_st = student if student else active_student

    queue = fetch_queue(get_subject_id(act_sb))

    sign_up_str = ''
    if queue:
        positions = tuple(map(lambda x: x[0], queue))

        if act_st is not positions[-1] + 1:
            while act_st not in positions:
                act_st += 1

            next_st = act_st + 1
            if act_st is not positions[-1]:
                while next_st not in positions:
                    next_st += 1

            for i, username, firstname in queue:
                if i == act_st:
                    if username:
                        sign_up_str += f"🟢 Зараз здає <b>{firstname} ({username})</b>\nМісце в черзі: {i}\n"
                    else:
                        sign_up_str += f"🟢 Зараз здає <b>{firstname}</b>\nМісце в черзі: {i}\n"
                if i == next_st:
                    if username:
                        sign_up_str += f"\nНаступним здаватиме <i>{firstname} ({username})</i>\n"
                    else:
                        sign_up_str += f"\nНаступним здаватиме <i>{firstname}</i>\n"
        else:
            sign_up_str += 'Запис відсутній'
    else:
        sign_up_str += 'Черга порожня або її не існує.\n'
    sign_up_str += '\nЗаписатися в чергу: /sign_in <i>{номер або назва предмету} {місце в черзі (за бажанням)}</i>' \
                   '\nВиписатися з черги: /sign_out <i>{номер або назва предмету}</i>' \
                   '\nВсі предмети: /all_subjects'

    return sign_up_str


def queue_to_str(queue):
    queue_str = ''
    if queue:
        for i, username, firstname in queue:
            if username:
                queue_str += f"{i}. {firstname} ({username})\n"
            else:
                queue_str += f"{i}. {firstname}\n"
    else:
        queue_str += 'Черга порожня або її не існує.\n'
    queue_str += '\nЗаписатися в чергу: /sign_in <i>{номер або назва предмету} {місце в черзі (за бажанням)}</i>' \
                 '\nВиписатися з черги: /sign_out <i>{номер або назва предмету}</i>' \
                 '\nВсі предмети: /all_subjects'

    return queue_str


def active_queue_to_str(queue):
    global active_student

    queue_str = ''
    if queue:
        positions = tuple(map(lambda x: x[0], queue))

        if active_student is not positions[-1] + 1:
            while active_student not in positions:
                active_student += 1

            next_student = active_student + 1
            if active_student is not positions[-1]:
                while next_student not in positions:
                    next_student += 1

            for i, username, firstname in queue:
                if i is active_student:
                    if username:
                        queue_str += f"{i}. <b>{firstname} (@{username})</b> 🟢\n"
                    else:
                        queue_str += f"{i}. <b>{firstname}</b> 🟢\n"
                elif i is next_student:
                    if username:
                        queue_str += f"{i}. <i>{firstname} (@{username}) — приготуватися</i>\n"
                    else:
                        queue_str += f"{i}. <i>{firstname} — приготуватися</i>\n"
                elif i < active_student:
                    if username:
                        queue_str += f"<del>{i}. {firstname} ({username})</del>\n"
                    else:
                        queue_str += f"<del>{i}. {firstname}</del>\n"
                else:
                    if username:
                        queue_str += f"{i}. {firstname} ({username})\n"
                    else:
                        queue_str += f"{i}. {firstname}\n"
            queue_str += '\nЧерга активна ☑\n'
        else:
            for i, username, firstname in queue:
                if username:
                    queue_str += f"<del>{i}. {firstname} ({username})</del>\n"
                else:
                    queue_str += f"<del>{i}. {firstname}</del>\n"
            queue_str += '\nЧерга закінчена 🔚\n'

            global active_subject
            active_subject = ''
    else:
        queue_str += 'Черга порожня\n'
    queue_str += '\nЗаписатися в чергу: /sign_in <i>{номер або назва предмету} {місце в черзі (за бажанням)}</i>' \
                 '\nВиписатися з черги: /sign_out <i>{номер або назва предмету}</i>' \
                 '\nВидалити чергу: /delete_queue' \
                 '\nВсі предмети: /all_subjects'

    return queue_str


def add_user(user):
    user_id = user.id
    name = user.first_name
    username = user.username if user.username else None

    # Записуємо користувача в базу, якщо його немає
    get_user = "SELECT * FROM students WHERE telegram_user_id = %s"
    my_cursor.execute(get_user, (user_id,))
    exists = my_cursor.fetchone()

    if not exists:
        put_user = "INSERT INTO students VALUES(%s, %s, %s)"
        my_cursor.execute(put_user, (user_id, username, name))
        db.mydb.commit()
    return


@dp.message_handler(commands='start_queue')
async def start_queue(message: types.Message):
    await Form.start_queue_st.set()

    subjects_with_queues = get_subjects_with_queues()

    if subjects_with_queues:
        str = "Виберіть предмет для запуску черги:\n"
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            str += f"{i + 1}. {subject}\n"
        str += "\nЯкщо на ваш предмет ще немає черги, ви можете створити її командою /create_queue\n"
    else:
        str = "Ще не створено жодної черги.\n\n"
        str += "Створити чергу: /create_queue\n"

    await message.answer(str)


@dp.message_handler(state=Form.start_queue_st)
async def start_queue(message: types.Message, state: FSMContext):
    subjects_with_queues = get_subjects_with_queues()
    global active_subject
    global active_student
    active_student = 1

    data = message.values["text"]
    try:
        data = int(data)
    except ValueError:
        active_subject = data

    else:
        if 0 < data <= len(subjects_with_queues):
            active_subject = subjects_with_queues[data - 1]
        else:
            await message.answer(f"Немає черги на предмет під номером {data}.\n"
                                 f"Ви можете створити чергу (/create_queue) або додати предмет (/add_subject).")
            await state.finish()
            return

    queue_str = active_queue_to_str(fetch_queue(get_subject_id()))

    await message.answer(queue_str)

    await state.finish()

    return


@dp.message_handler(commands='next')
async def next(message: types.Message):

    global active_student
    if not active_student or not active_subject:
        await message.answer('Жодна черга не активна\n\nСпочатку розпочніть якусь чергу командою /start_queue')
        return
    else:
        active_student += 1

    queue_str = active_queue_to_str(fetch_queue(get_subject_id()))

    await message.answer(queue_str)


@dp.message_handler(commands='show_current_student')
async def show_current_student(message: types.Message):
    await message.answer(get_sign_up())


@dp.message_handler(commands='all_teachers')
async def all_teachers(message: types.Message):
    query = """SELECT teachers.id_teacher, teachers.username_telegram, teachers.phone_number,
               teachers.email, teachers.info, subjects.title
               FROM teachers
               LEFT OUTER JOIN subjects
                 USING (id_teacher);"""
    my_cursor.execute(query)
    teachers = my_cursor.fetchall()

    all_teachers_str = 'Список усіх викладачів:\n'
    if teachers:
        for i, username, phone, email, info, subject in teachers:
            all_teachers_str += f"\n{i}. ТГ: {username}\nНомер телефону: {phone}\n" \
                                f"Ел. пошта: {email}\nІнформація: {info}\nВикладає: {subject}\n"
    else:
        all_teachers_str += 'Викладачів ще немає.\n'
    all_teachers_str += '\nДодати викладача: /add_teacher'

    await message.answer(all_teachers_str)
    return


@dp.message_handler(commands='all_subjects')
async def all_subjects(message: types.Message):
    query = """SELECT subjects.subject_id, subjects.title, teachers.username_telegram
               FROM subjects
               LEFT OUTER JOIN teachers
                 USING (id_teacher);"""
    my_cursor.execute(query)
    subjects = my_cursor.fetchall()

    all_subjects_str = 'Список усіх предметів:\n'
    if subjects:
        for i, title, teacher in subjects:
            all_subjects_str += f"\n{i}. {title}\nВикладає: {teacher}\n"
    else:
        all_subjects_str += 'Предметів ще немає.\n'
    all_subjects_str += '\nДодати предмет: /add_subject'

    await message.answer(all_subjects_str)
    return


@dp.message_handler(commands='all_students')
async def all_students(message: types.Message):
    query = """SELECT username, firstname FROM students;"""
    my_cursor.execute(query)
    students = my_cursor.fetchall()

    all_students_str = 'Список усіх зареєстрованих студентів:\n\n'
    if students:
        i = 1
        for username, firstname in students:
            all_students_str += f"{i}. {firstname} ({username})\n"
    else:
        all_students_str += 'Зареєстрованих студентів ще немає.\n'
    all_students_str += '\nДодати студента: /add_student'

    await message.answer(all_students_str)
    return


def get_first_free_pos(positions):
    if not positions:
        return 1
    for i in range(active_student, 25):  # зробити адаптивним максимальну кількість
        if i not in positions:
            return i

    return None


@dp.message_handler(commands='sign_in')
async def sign_in(message: types.Message):
    user = message.from_user
    add_user(user)
    user_id = user.id
    user_name = user.first_name

    arguments = message.get_args().split(" ")
    if len(arguments) not in (1, 2) or not arguments[0]:
        await message.answer("Неправильна команда. Необхідно вказати назву або"
                             " номер предмету, в чергу якого бажаєте записату.\nНаприклад /sign_in Математика")
        return

    data = arguments[0]
    subjects = get_subjects()
    sub_with_queue = get_subjects_with_queues()

    try:
        if 0 < int(data) <= len(subjects):
            subject = subjects[int(data) - 1]
        else:
            await message.answer(
                f"Предмет за номером {data} невідомий. Ви можете додати предмет командою /add_lesson")
            return
    except ValueError:
        subject = data

    if subject not in subjects:
        await message.answer(
            f"Предмет {subject} невідомий. Ви додати предмет командою /add_lesson")
        return

    if subject not in sub_with_queue:
        await message.answer(
            f"Предмет {subject} не має черги. Ви можете створити чергу командою /create_queue")
        return

    cheak_stundent = """SELECT su.position
                        FROM sign_ups su
                        JOIN students st
                            USING (telegram_user_id)
                        JOIN queues qu
                            USING (id_queue)
                        JOIN subjects sb
                            USING (subject_id)
                        WHERE st.telegram_user_id = %s and sb.title = %s"""
    my_cursor.execute(cheak_stundent, (user_id, subject))
    exist_pos = my_cursor.fetchall()
    exist_pos = tuple(map(lambda x: x[0], exist_pos))

    if exist_pos and len(exist_pos) == 1:
        max_pos = exist_pos[0]

    if exist_pos:
        max_pos = max(exist_pos)
    else:
        max_pos = 0

    """
    Заборонити запис раніше курентної позиції в активній черзі!!!
    Дозволити повторно реєструватись людям на "доздачу"
    """

    if max_pos > active_student:
        await message.answer(f"Ви вже записані в цю чергу під номером {exist_pos[0]}. Якщо бажаєте змінити позицію, то"
                             f"\"ВИЙДИ ЗВІДСИ, РОЗБІЙНИК!\"")
        return

    if len(arguments) == 1:  # Випадок, коли юзер вказав лише назву предмету. Записуємо на перше вільне місце
        get_all_from_queue = """SELECT position
                                FROM sign_ups
                                JOIN queues
                                    USING (id_queue)
                                JOIN subjects sb
                                    USING (subject_id)
                                WHERE sb.title = %s"""

        my_cursor.execute(get_all_from_queue, (subject,))
        positions = my_cursor.fetchall()
        positions = tuple(map(lambda x: x[0], positions))
        position = get_first_free_pos(positions)

        if not position:
            await message.answer("Черга заповнена. Можна змінити кількість студенетів і налаштуваннях.")
            return

    else:  # Випадок, коли юзер вказав назву предмету та конкретне місце в черзі
        try:
            position = int(arguments[1])
        except ValueError:
            await message.answer("Неправильна команда. Необхідно вказати назву або"
                                 " номер предмету та бажаний номер у черзі, в чергу якого бажаєте записату."
                                 "\nНаприклад /sign_in Математика 5")
            return

        if position < 0 or position > 25:  # !!!Додати можливість зміни максимальної кількості
            await message.answer("Помилка. Максимальний номер у черзі 25")
            return

        if position <= active_student:
            await message.answer(f"Черга під номером {position} вже пройшла. Запишіться вперед по черзі")
            return

        # Перевірка, чи є вже на цьому місці записаний студент

        check_student_by_pos = """SELECT st.firstname
                                   FROM sign_ups su
                                   JOIN students st
                                       USING (telegram_user_id)
                                   JOIN queues qu
                                       USING (id_queue)
                                   JOIN subjects sb
                                       USING (subject_id)
                                   WHERE su.position = %s and sb.title = %s"""

        my_cursor.execute(check_student_by_pos, (position, subject))
        name_of_student = my_cursor.fetchone()

        if name_of_student:
            await message.answer(f"Помилка. На цю позицію записаний/на вже {name_of_student[0]}")
            return

    get_id_queue = """SELECT id_queue
                      FROM queues
                      JOIN subjects sb
                        USING (subject_id)
                      WHERE sb.title = %s"""
    my_cursor.execute(get_id_queue, (subject,))
    id_queue = my_cursor.fetchone()[0]

    sign_up_student = """INSERT INTO sign_ups
                         VALUES(DEFAULT, %s, %s, %s)"""
    my_cursor.execute(sign_up_student, (id_queue, user_id, position))
    db.mydb.commit()

    await message.answer(f"{user_name} було успішно записано в чергу на {subject} під номером {position}")
    return


@dp.message_handler(commands='sign_out')
async def sign_out(message: types.Message):
    user = message.from_user
    add_user(user)
    user_id = user.id

    data = message.get_args()
    if not data:
        await message.answer("Неправильна команда. Необхідно вказати назву або"
                             " номер предмету, для якого хочете покинути чергу.\nНаприклад /sign_out Математика")
        return

    subjects = get_subjects()
    sub_with_queue = get_subjects_with_queues()

    try:
        if 0 < int(data) <= len(subjects):
            subject = subjects[int(data) - 1]
        else:
            await message.answer(f"Предмет за номером {data} невідомий. Ви можете додати предмет командою /add_lesson")
            return
    except ValueError:
        subject = data

    if subject in subjects:
        if subject in sub_with_queue:

            get_queue_id = """SELECT id_queue 
                              FROM queues 
                              JOIN subjects sb
                                USING (subject_id)
                              WHERE sb.title = %s"""
            my_cursor.execute(get_queue_id, (subject,))
            id_queue = my_cursor.fetchone()[0]

            check_sign_up = """SELECT position
                               FROM sign_ups
                               WHERE telegram_user_id = %s
                               AND id_queue = %s;
                               """
            my_cursor.execute(check_sign_up, (user_id, id_queue))
            position = my_cursor.fetchone()

            if position:
                position = position[0]

                delete_sign_up = f"""DELETE FROM sign_ups
                                     WHERE position = {position} ;
                                     """
                my_cursor.execute(delete_sign_up)
                db.mydb.commit()

                update_positions = f"""UPDATE sign_ups
                                       SET position = position-1
                                       WHERE position > {position};"""
                my_cursor.execute(update_positions)
                db.mydb.commit()

                await message.answer(f"Вас було видалено з черги")
            else:
                await message.answer(
                    f"Ви не були записані в чергу на {subject}."
                    f" Але не переживайте, результат, це всеодно, що вас виписали")
        else:
            await message.answer(f"До предмету {subject} ще не створена черга. Ви можете її створити /create_queue")
    else:
        await message.answer(f"Предмет {subject} невідомий. Ви можете додати предмет командою /add_lesson")
    return


if __name__ == '__main__':
    try:
        print("Initializing Database...")
        print("Connected to the database")

        sql_command = """CREATE DATABASE IF NOT EXISTS `queue-bot-kpi` DEFAULT CHARACTER SET utf8 ;"""
        my_cursor.execute(sql_command)
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Subjects`(
            `subject_id` INT          NOT NULL AUTO_INCREMENT,
            `title`      VARCHAR(100) NOT NULL,
            `id_teacher` INT          NOT NULL,
            PRIMARY KEY (`subject_id`),
            UNIQUE INDEX `title_UNIQUE` (`title` ASC) VISIBLE,
            UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
            CONSTRAINT `fk_id_teacher`
                FOREIGN KEY (`id_teacher`)
                REFERENCES `queue-bot-kpi`.`teachers` (`id_teacher`)
                ON DELETE NO ACTION
                ON UPDATE CASCADE);"""
        my_cursor.execute(sql_command)
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Students` (
            `telegram_user_id` CHAR(12) NOT NULL,
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
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Sign_ups` (
            `id_sign_up` INT NOT NULL AUTO_INCREMENT,
            `id_queue` INT NOT NULL,
            `telegram_user_id` CHAR(12) NOT NULL,
            `position` INT NOT NULL,
            PRIMARY KEY (`id_sign_up`),
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
        sql_command = """CREATE TABLE IF NOT EXISTS `queue-bot-kpi`.`Teachers`(
            `id_teacher`        INT         NOT NULL AUTO_INCREMENT,
            `username_telegram` VARCHAR(45) NULL,
            `phone_number`      CHAR(13)    NULL,
            `email`             VARCHAR(60) NULL,
            `info`              TEXT(1000)  NULL,
            PRIMARY KEY (`id_teacher`),
            UNIQUE INDEX `id_teacher_UNIQUE` (`id_teacher` ASC) VISIBLE,
            UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC) VISIBLE,
            UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE);"""
        my_cursor.execute(sql_command)
        print("All tables are ready")
        print("Bot Started")
        executor.start_polling(dp, skip_updates=True)

    except Exception as error:
        print('Cause: {}'.format(error))
