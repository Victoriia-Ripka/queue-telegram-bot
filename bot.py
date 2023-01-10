import logging

import mysql.connector

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

import db

API_TOKEN = '5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k'

bot = Bot(token=API_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

my_cursor = None

active_subject = ''
active_student = 0

max_in_queue = 40


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


# @dp.message_handler(commands='start')
# async def start(message: types.Message):
#     chat_name = 'user'
#     # chat_name = message['chat']['first_name']
#     # how to get chat_name in chat and use it in answer?
#     await message.answer(f'hello, {chat_name}')


@dp.message_handler(commands='help')
async def help(message: types.Message):
    text = 'all commands definitions will be here soon'
    await message.answer(text)


# @dp.message_handler(commands='end')
# async def end(message: types.Message):
#     print('Start deletind DB...')
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
#     print('All tables are deleted')
#     text = 'All tables are deleted'
#     await message.answer(text)


@dp.message_handler(commands='add_subject')
async def add_subject_start(message: types.Message):
    subjects = get_subjects()
    str = ''
    if subjects:
        str += '📚 Список вже існуючих предметів:\n'
        for subject, i in zip(subjects, range(len(subjects))):
            str += f'{i + 1}. {subject}\n'
    else:
        str = '🫥 Список вже існуючих предметів порожній\n\n'
    
    teachers = get_teachers_with_id()
    if teachers:
        await Form.subject.set()
        str += '\n👩‍🏫 Список викладачів:\n'
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f'{teacher[0]}: {teacher[1]}\n'
        str += '\n📝 Напишіть назву предмета, який хочете додати, і номер викладача зі списку'
    else:
        str += '🫥 Список викладачів порожній\nСпочатку додайте викладачів, щоб додавати предмети!'
        str += '\n\nДодати викладача: /add_teacher'

    await message.answer(str)
    return 


@dp.message_handler(state=Form.subject)
async def add_subject(message: types.Message, state: FSMContext):
    data = message.values['text'].split(' ')
    if len(data) >= 2:
        try:
            teacher_id = int(data[len(data) - 1])
        except ValueError:
            await state.finish()
            await message.answer(f'1️⃣  Після назви повинне бути вказаним число\n\nСпробувати ще раз: /add_subject')
            return
        separator = ' '
        data.pop()
        title = separator.join(data)
        if not isinstance(teacher_id, int) or not isinstance(title, str):
            await state.finish()
            await message.answer(f'☹ Ви ввели неправильні дані\n\nСпробувати ще раз: /add_subject')
            return
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 2 параметри: назва предмета'
                             'і номер викладача зі списку\n\n'
                             'Спробувати ще раз: /add_subject')
        return
    
    new_subject = (title, teacher_id)
    sql = 'INSERT INTO subjects (subject_id, title, id_teacher) VALUES (NULL, %s, %s);'
    my_cursor.execute(sql, new_subject)
    db.mydb.commit()

    if my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'✅ Предмет {title} додано до списку')
    await state.finish()
    return       
    

@dp.message_handler(commands='add_teacher')
async def add_teacher_start(message: types.Message):
    await Form.teacher.set()
    teachers = get_teachers()
    if teachers:
        str = '👩‍🏫 Список вже доданих викладачів:\n'
        for subject, i in zip(teachers, range(len(teachers))):
            str += f'{i + 1}. {subject}\n'
    else:
        str = '🫥 Список викладачів порожній. Ви додасте першого викладача\n'
    str += '\n📝 Введіть ім\'я викладача\n' \
           '💁 За бажанням також можна вписати телеграм-тег, номер телефону та email, розділивши все комою'
    await message.answer(str)


@dp.message_handler(state=Form.teacher)
async def add_teacher(message: types.Message, state: FSMContext):
    data = message.values['text'].split(', ')
    if len(data) == 1:
        name = data[0]
        if not all(x.isalpha() or x.isspace() for x in name):
            await state.finish()
            await message.answer('🔤 Ім\'я викладача повинне складатися лише з літер\n\nСпробувати ще раз: /add_teacher')
            return
        new_teacher = (name, )
        sql = 'INSERT INTO teachers (name) VALUES (%s);'
        my_cursor.execute(sql, new_teacher)  
        db.mydb.commit()
    elif len(data) == 2:
        name = data[0]
        username_telegram = data[1]
        if not all(x.isalpha() or x.isspace() for x in name):
            await state.finish()
            await message.answer('🔤 Ім\'я викладача повинне складатися лише з літер\n\nСпробувати ще раз: /add_teacher')
            return
        new_teacher = (name, username_telegram)
        sql = 'INSERT INTO teachers (name, username_telegram) VALUES (%s, %s);'
        my_cursor.execute(sql, new_teacher)
        db.mydb.commit()
    elif len(data) == 3:
        name = data[0]
        username_telegram = data[1]
        phone_number = data[2]
        if not all(x.isalpha() or x.isspace() for x in name):
            await state.finish()
            await message.answer('🔤 Ім\'я викладача повинне складатися лише з літер\n\nСпробувати ще раз: /add_teacher')
            return
        new_teacher = (name, username_telegram, phone_number)
        sql = 'INSERT INTO teachers (name, username_telegram, phone_number) VALUES (%s, %s, %s);'
        my_cursor.execute(sql, new_teacher)
        db.mydb.commit()
    elif len(data) == 4:
        name = data[0]
        username_telegram = data[1]
        phone_number = data[2]
        email = data[3]
        if not all(x.isalpha() or x.isspace() for x in name):
            await state.finish()
            await message.answer('🔤 Ім\'я викладача повинне складатися лише з літер\n\nСпробувати ще раз: /add_teacher')
            return
        new_teacher = (name, username_telegram, phone_number, email)
        sql = 'INSERT INTO teachers (name, username_telegram, phone_number, email) VALUES (%s, %s, %s, %s);'
        my_cursor.execute(sql, new_teacher)
        db.mydb.commit()
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели забагато параметрів (більш ніж 4)\n\nСпробувати ще раз: /add_teacher')
        return

    if my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'✅ Викладача {name} додано до списку')
    await state.finish()


@dp.message_handler(commands='add_teacher_info')
async def add_teacher_info_start(message: types.Message):
    await Form.info.set()
    teachers = get_teachers_with_id()
    if teachers:
        str = '👩‍🏫 Список викладачів:\n'
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f'{teacher[0]}. {teacher[1]}\n'
        str += '\n1️⃣ Введіть номер викладача із списку\n\nПісля цього додайте всю необхідну інформацію'
    else:
        str = '🫥 Список викладачів порожній. Спочатку додайте викладача'
        str += '\n\nДодати інформацію про викладача: /add_teacher_info'
    await message.answer(str)


@dp.message_handler(state=Form.info)
async def add_teacher_info(message: types.Message, state: FSMContext):
    data = message.values['text'].split(' ')
    if len(data) >= 2:
        try:
            id = int(data[0])
        except ValueError:
            await state.finish()
            await message.answer('1️⃣  Першим повинен бути номер\n\nСпробувати ще раз: /add_teacher_info')
            return
        separator = ' '
        del data[0]
        info = separator.join(data)
        # if not isinstance(info, str) or not isinstance(id, int):
        #     await state.finish()
        #     await message.answer('Щось пішло не так\n\nСпробувати ще раз: /add_teacher_info')
        #     return
        new_info = (info, id)
        sql = 'UPDATE teachers SET info = %s WHERE id_teacher = %s;'
        my_cursor.execute(sql, new_info)
        db.mydb.commit()
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 2 параметри: номер викладача'
                             'зі списку і додаткова інформація про нього \n\n'
                             'Спробувати ще раз: /add_teacher_info')
        return

    if my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'✅ Інформація додана')
    await state.finish()


@dp.message_handler(commands='update_subject')
async def update_subject_start(message: types.Message):
    subjects = get_subjects_with_teachers()
    if subjects:
        await Form.update_subject.set()
        str = '📚 Список існуючих предметів:\n'
        for subject, i in zip(subjects, range(len(subjects))):
            str += f'{subject[0]}. {subject[1]} - {subject[2]}\n'
        
        teachers = get_teachers_with_id()
        str += '👩‍🏫 Список доданих викладачів:\n'
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f'{teacher[0]}: {teacher[1]}\n'
        str += '\n📝 Введіть номер предмета зі списку, нову назву предмета та номер викладача зі списку'
    else:
        str = '🫥 Список предметів порожній. Спочатку додайте предмет\n\nДодати предмет: /add_subject'
    await message.answer(str)
    return 


@dp.message_handler(state=Form.update_subject)
async def update_subject(message: types.Message, state: FSMContext):
    data = message.values['text'].split(' ')
    if len(data) > 2:
        id = data[0]
        teacher_id = data[len(data)-1]
        separator = '_'
        del data[0]
        del data[len(data)-1]
        title = separator.join(data)
        if not isinstance(title, str):
            await message.answer('☹ Ви ввели неправильні дані!\n\nНеобхідно ввести номер предмета зі списку, '
                                 'нову назву предмета та номер викладача зі списку'
                                 '\n\nСпробувати ще раз: /update_subject')
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 3 параметри: номер предмета'
                             'зі списку, нова назва предмета і номер викладача зі списку'
                             '\n\nСпробувати ще раз: /update_subject')
        return

    try:
        new_subject = (title, int(teacher_id), int(id))
    except ValueError:
        await state.finish()
        await message.answer('Щось пішло не так. Спробуйте ще раз /update_subject')
        return
    else:
        sql = 'UPDATE subjects SET title = %s, id_teacher = %s WHERE subject_id = %s;'
        my_cursor.execute(sql, new_subject)
        db.mydb.commit()

    if my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'🔄 Предмет {title} успішно оновлений')
    await state.finish()
    return


@dp.message_handler(commands='update_teacher')
async def update_teacher_start(message: types.Message):
    await Form.update_teacher.set()
    teachers = get_teachers_with_all_info()
    if teachers:
        str = '👩‍🏫 Список викладачів:\n'
        for teacher, i in zip(teachers, range(len(teachers))):
            str += f'{teacher[0]}. {teacher[1]}\nТелеграм: {teacher[2]}\n' \
                   f'Номер телефону: {teacher[3]}\nEmail: {teacher[4]}\n'
        str += '\n📝 Введіть номер викладача зі списку' \
               '\n\nПісля цього ім\'я, нік в телеграмі, номер телефону та email.' \
               'Якщо якоїсь інформації немає, поставте "-"'
    else:
        str = '🫥 Список викладачів порожній. Спочатку додайте викладачів до списку'
        str += '\n\nДодати викладача: /add_teacher'
    await message.answer(str)


@dp.message_handler(state=Form.update_teacher)
async def update_teacher(message: types.Message, state: FSMContext):
    data = message.values['text'].split(', ')
    if len(data) == 5:
        id = data[0]
        name = data[1]
        username_telegram = data[2]
        phone_number = data[3]
        email = data[4]
        if not isinstance(id, int) and not isinstance(username_telegram, str):
            await message.answer('Щось пішло не так. Спробуйте ще раз /update_teacher')
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 4 параметри: ім\'я викладача,'
                             'зі списку, нік в телеграмі, номер телефону та email'
                             '\n\nСпробувати ще раз: /update_teacher')
        return

    try:
        new_teacher_info = (name, username_telegram, phone_number, email, id)
        sql = 'UPDATE Teachers SET name = %s, username_telegram = %s, phone_number = %s, email = %s WHERE id_teacher = %s'
        my_cursor.execute(sql, new_teacher_info)
        db.mydb.commit()
        await state.finish()
    except mysql.connector.Error:
        await state.finish()
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
        return

    if my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'🔄 Викладач {username_telegram} успішно оновлений')
    await state.finish()
    return


@dp.message_handler(commands='delete_subject')
async def delete_subject_start(message: types.Message):
    await Form.delete_subject.set()
    subjects = get_subjects_with_id()
    str = '📚 Список існуючих предметів:\n'
    for subject, i in zip(subjects, range(len(subjects))):
        str += f'{subject[0]}: {subject[1]}\n'
    str += '📝 Напишіть номер предмета, який пострібно видалити, зі списку'
    await message.answer(str)
    return 


@dp.message_handler(state=Form.delete_subject)
async def delete_subject(message: types.Message, state: FSMContext):
    data = message.values['text'].split(' ')
    if len(data) == 1:
        try:
            id = int(data[0])
        except ValueError:
            await state.finish()
            await message.answer('1️⃣ Потрібно ввести номер предмета зі списку\n\nСпробувати ще раз: /delete_subject')
            return
    else: 
        await state.finish()
        await message.answer('🗿 Ви ввели більш ніж одне число\n\nСпробувати ще раз: /delete_subject')
        return
        
    sql = 'DELETE FROM subjects WHERE subject_id = %s;'
    my_cursor.execute(sql, (id,)) 
    db.mydb.commit()

    if my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'🗑 Предмет було успішно видалено')
    await state.finish()
    return


@dp.message_handler(commands='delete_teacher')
async def delete_teacher_start(message: types.Message):
    await Form.delete_teacher.set()
    teachers = get_teachers_with_id()
    str = '👩‍🏫 Список викладачів:\n'
    for teacher, i in zip(teachers, range(len(teachers))):
        str += f'{teacher[0]}: {teacher[1]}\n'
    str += '\n📝 Введіть номер викладача, якого потрібно видалити, зі списку\n\n' \
           '☝ Якщо викладач читає якийсь предмет, то видалити його неможливо. ' \
           'В такому випадку або видаліть предмет, який викладає цей викладач, або змініть викладача для предмета'
    str += '\n\nВидалити предмет: /delete_subject\nЗмінити викладача для предмета: /update_subject'
    await message.answer(str)
    return


@dp.message_handler(state=Form.delete_teacher)
async def delete_teacher(message: types.Message, state: FSMContext):
    data = message.values['text'].split(' ')
    if len(data) == 1:
        try:
            id = int(data[0])
        except ValueError:
            await state.finish()
            await message.answer('1️⃣ Потрібно ввести номер викладача зі списку\n\nСпробувати ще раз: /delete_teacher')
            return
        else:
            sql = 'DELETE FROM Teachers WHERE id_teacher = %s;'
            my_cursor.execute(sql, (id,))
            db.mydb.commit()
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели більш ніж одне число\n\nСпробувати ще раз: /delete_teacher')
        return

    if my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'🗑 Викладача було успішно видалено')
    await state.finish()
    return




def get_teachers():
    my_cursor.execute('SELECT DISTINCT name FROM teachers;')
    result = my_cursor.fetchall()

    teachers = []
    for teacher in result:
        teachers.append(teacher[0])

    return teachers

def get_teachers_with_id():
    my_cursor.execute('SELECT DISTINCT id_teacher, name FROM teachers;')
    result = my_cursor.fetchall()

    teachers = []
    for teacher in result:
        teachers.append((teacher[0], teacher[1]))

    return teachers

def get_teachers_with_all_info():
    my_cursor.execute('SELECT * FROM teachers;')
    result = my_cursor.fetchall()

    teachers = []
    for teacher in result:
        teachers.append((teacher[0], teacher[1], teacher[2], teacher[3], teacher[4], teacher[5]))

    return teachers

def get_subjects():
    my_cursor.execute("""SELECT title FROM subjects
                         ORDER BY subject_id;""")
    result = my_cursor.fetchall()

    subjects = []
    for subject in result:
        subjects.append(subject[0])

    return subjects


def get_subjects_with_id():
    my_cursor.execute('SELECT DISTINCT subject_id, title FROM subjects;')
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
        str = '📝 Оберіть предмет, на який хочете створити чергу:\n\n'
        for subject, i in zip(subjects, range(len(subjects))):
            str += f'{i + 1}. {subject}\n'
    else:
        str = '🫥 Список предметів порожній\n'
    str += '\nДодати предмет: /add_subject'
    await message.answer(str)


@dp.message_handler(state=Form.create_queue_st)
async def create_queue(message: types.Message, state: FSMContext):
    subjects = get_subjects()
    subjects_with_queues = get_subjects_with_queues()

    data = message.values['text']

    #  Вибір предмета відбувається написання назвою або номером
    try:  # Спроба конвертації користувацького вводу як інтове число. Якщо не виходить - сприймаємо як назву
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects):
            subject = subjects[data - 1]
        else:
            await message.answer(f'❓ Предмет за номером {data} невідомий'
                                 f'\n\nСпробувати ще раз: /create_queue\nДодати предмет: /add_subject')
            await state.finish()
            return

    if subject in subjects_with_queues:
        await message.answer(f'🗒 Черга на {subject} вже існує\n\nСпробувати ще раз: /create_queue')
        await state.finish()
        return
    else:
        subject_id = get_subject_id(subject)

        if subject_id:
            my_cursor.execute('INSERT INTO queues (id_queue, subject_id) VALUES(DEFAULT, %s)', (subject_id,))
            db.mydb.commit()
            await message.answer(f'✅ Чергу на предмет {subject} створено')
        else:
            await message.answer(f'🫥 Предмета {subject} немає у списку предметів'
                                 f'\n\nДодати предмет: /add_subject')

    await state.finish()
    return


@dp.message_handler(commands='clear_queue')
async def clear_queue(message: types.Message):
    await Form.clear_queue_st.set()
    subjects_with_queues = get_subjects_with_queues()
    if subjects_with_queues:
        str = '📚 Список усіх предметів, на які існують черги:\n'
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            str += f'{i + 1}. {subject}\n'
    else:
        str = '🫥 Список предметів з чергами порожній' \
              '\n\nДодати предмет: /add_subject\nСтворити чергу на предмет: /create_queue'
    await message.answer(str)


@dp.message_handler(state=Form.clear_queue_st)
async def clear_queue(message: types.Message, state: FSMContext):
    subjects = get_subjects()
    subjects_with_queues = get_subjects_with_queues()

    data = message.values['text']

    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects):
            subject = subjects[data - 1]
        else:
            await message.answer(f'❓ Предмет за номером {data} невідомий'
                                 f'\n\nДодати предмет: /add_subject')
            await state.finish()
            return

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
            await message.answer(f'🧹 Черга на предмет {subject} очищена')
        else:
            await message.answer(f'🫥 Черга на предмет {subject} ще не створена'
                                 f'\n\nСтворити чергу: /create_queue')
    else:
        await message.answer(f'🫥 Предмета {subject} немає у списку'
                             f'\n\nДодати предмет: /add_subject')
    await state.finish()
    return


@dp.message_handler(commands='delete_queue')
async def delete_queue(message: types.Message):
    await Form.delete_queue_st.set()
    subjects_with_queues = get_subjects_with_queues()

    if subjects_with_queues:
        str = '📚 Список усіх предметів з чергами:\n'
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            str += f'{i + 1}. {subject}\n'
        str += '\nДодати предмет: /add_subject\nСтворити чергу: /create_queue'
    else:
        str = '🫥 Ще не створено жодної черги'
        str += '\n\nСтворити чергу: /create_queue'
    await message.answer(str)


@dp.message_handler(state=Form.delete_queue_st)
async def delete_queue(message: types.Message, state: FSMContext):
    subjects = get_subjects()
    subjects_with_queues = get_subjects_with_queues()

    data = message.values['text']

    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects):
            subject = subjects[data - 1]
        else:
            await message.answer(f'❓ Предмет за номером {data} невідомий'
                                 f'\n\nДодати предмет: /add_subject\nСтворити чергу: /create_queue')
            await state.finish()
            return

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
            delete_users = """DELETE queues FROM queues
                              JOIN subjects sb
                                     USING(subject_id)
                              WHERE sb.title = %s;
                              """
            my_cursor.execute(delete_users, (subject,))
            db.mydb.commit()
            await message.answer(f'🗑 Черга на предмет {subject} видалена')
        else:
            await message.answer(f'🫥 Черга на предмет {subject} ще не створена'
                                 f'\n\nСтворити чергу: /create_queue')
    else:
        await message.answer(f'❓ Предмет за {subject} невідомий'
                             f'\n\nДодати предмет: /add_lesson')
    await state.finish()
    return


@dp.message_handler(commands='show_needed_queue')
async def show_needed_queue(message: types.Message):
    await Form.show_queue_st.set()
    subjects_with_queues = get_subjects_with_queues()

    if subjects_with_queues:
        str = '📝 Виберіть предмет, на який шукаєте чергу:\n'
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            str += f'{i + 1}. {subject}\n'
        str += '\n☝ Якщо на ваш предмет ще немає черги, Ви можете створити її'
    else:
        str = '🫥 Ще не створено жодної черги'

    str += '\n\nСтворити чергу: /create_queue\n'
    str += 'Отримати всі предмети: /get_subjects\n'
    str += 'Додати предмет: /add_subject'

    await message.answer(str)


@dp.message_handler(state=Form.show_queue_st)
async def show_needed_queue(message: types.Message, state: FSMContext):
    subjects_with_queues = get_subjects_with_queues()

    data = message.values['text']
    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects_with_queues):
            subject = subjects_with_queues[data - 1]
        else:
            await message.answer(f'🫥 Немає черги на предмет під номером {data}\n'
                                 f'\n\nСтворити чергу: /create_queue\nДодати предмет: /add_subject')
            await state.finish()
            return

    queue_str = queue_to_str(fetch_queue(get_subject_id(subject)))

    await message.answer(queue_str)

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
                        sign_up_str += f'🟢 Зараз здає <b>{firstname} ({username})</b>\nМісце в черзі: {i}\n'
                    else:
                        sign_up_str += f'🟢 Зараз здає <b>{firstname}</b>\nМісце в черзі: {i}\n'
                if i == next_st:
                    if username:
                        sign_up_str += f'\nНаступним здаватиме <i>{firstname} ({username})</i>\n'
                    else:
                        sign_up_str += f'\nНаступним здаватиме <i>{firstname}</i>\n'
        else:
            sign_up_str += '🫥 Запис відсутній'
    else:
        sign_up_str += '🫥 Черга порожня\n'
    sign_up_str += '\nЗаписатися в чергу: /sign_up <i>{номер або назва предмета} {місце в черзі (за бажанням)}</i>' \
                   '\nВиписатися з черги: /sign_out <i>{номер або назва предмета}</i>' \
                   '\nВсі предмети: /all_subjects'

    return sign_up_str


def queue_to_str(queue):
    queue_str = ''
    if queue:
        for i, username, firstname in queue:
            if username:
                queue_str += f'{i}. {firstname} ({username})\n'
            else:
                queue_str += f'{i}. {firstname}\n'
    else:
        queue_str += '🫥 Черга порожня\n'
    queue_str += '\nЗаписатися в чергу: /sign_up <i>{номер або назва предмета} {місце в черзі (за бажанням)}</i>' \
                 '\nВиписатися з черги: /sign_out <i>{номер або назва предмета}</i>' \
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
                        queue_str += f'{i}. <b>{firstname} (@{username})</b> 🟢\n'
                    else:
                        queue_str += f'{i}. <b>{firstname}</b> 🟢\n'
                elif i is next_student:
                    if username:
                        queue_str += f'{i}. <i>{firstname} (@{username}) — приготуватися</i>\n'
                    else:
                        queue_str += f'{i}. <i>{firstname} — приготуватися</i>\n'
                elif i < active_student:
                    if username:
                        queue_str += f'<del>{i}. {firstname} ({username})</del>\n'
                    else:
                        queue_str += f'<del>{i}. {firstname}</del>\n'
                else:
                    if username:
                        queue_str += f'{i}. {firstname} ({username})\n'
                    else:
                        queue_str += f'{i}. {firstname}\n'
            queue_str += '\nЧерга активна ☑\n'
        else:
            for i, username, firstname in queue:
                if username:
                    queue_str += f'<del>{i}. {firstname} ({username})</del>\n'
                else:
                    queue_str += f'<del>{i}. {firstname}</del>\n'
            queue_str += '\nЧерга закінчена 🔚\n'

            global active_subject
            active_subject = ''
    else:
        queue_str += '🫥 Черга порожня\n'
    queue_str += '\nЗаписатися в чергу: /sign_up <i>{номер або назва предмета} {місце в черзі (за бажанням)}</i>' \
                 '\nВиписатися з черги: /sign_out <i>{номер або назва предмета}</i>' \
                 '\nВидалити чергу: /delete_queue' \
                 '\nВсі предмети: /all_subjects'

    return queue_str


def add_user(user):
    user_id = user.id
    name = user.first_name
    username = user.username if user.username else None

    # Записуємо користувача в базу, якщо його немає
    get_user = 'SELECT * FROM students WHERE telegram_user_id = %s'
    my_cursor.execute(get_user, (user_id,))
    exists = my_cursor.fetchone()

    if not exists:
        put_user = 'INSERT INTO students VALUES(%s, %s, %s)'
        my_cursor.execute(put_user, (user_id, username, name))
        db.mydb.commit()
    return


@dp.message_handler(commands='start_queue')
async def start_queue(message: types.Message):

    subjects_with_queues = get_subjects_with_queues()

    if subjects_with_queues:
        await Form.start_queue_st.set()
        str = '📝 Виберіть предмет для запуску черги:\n'
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            str += f'{i + 1}. {subject}\n'
        str += '\n☝ Якщо на ваш предмет ще немає черги, Ви можете створити її'
    else:
        str = '🫥 Ще не створено жодної черги'
    str += '\n\nСтворити чергу: /create_queue'
    # конкретно в цьому випадку можна створити однакову підсказку для обох випадків if/else

    await message.answer(str)


@dp.message_handler(state=Form.start_queue_st)
async def start_queue(message: types.Message, state: FSMContext):
    subjects_with_queues = get_subjects_with_queues()
    global active_subject
    global active_student
    active_student = 1

    data = message.values['text']
    try:
        data = int(data)
    except ValueError:
        active_subject = data
    else:
        if 0 < data <= len(subjects_with_queues):
            active_subject = subjects_with_queues[data - 1]
        else:
            await message.answer(f'🫥 Немає черги на предмет під номером {data}'
                                 f'\n\nСтворити чергу: /create_queue\nДодати предмет: /add_subject')
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
        await message.answer('☹ Жодна черга не активна\n\nРозпочати чергу: /start_queue')
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
    query = """SELECT teachers.id_teacher, teachers.name, teachers.username_telegram, teachers.phone_number,
               teachers.email, teachers.info, subjects.title
               FROM teachers
               LEFT OUTER JOIN subjects
                   USING (id_teacher)   
               ORDER BY id_teacher;"""
    my_cursor.execute(query)
    teachers = my_cursor.fetchall()

    all_teachers_str = '👩‍🏫 Список усіх викладачів:\n'
    if teachers:
        for i, name, username, phone, email, info, subject in teachers:
            all_teachers_str += f'\n{i}. ПІБ: {name}\nТелеграм: {username}\nНомер телефону: {phone}\n' \
                                f'Ел. пошта: {email}\nІнформація: {info}\nВикладає: {subject}\n'
    else:
        all_teachers_str += '🫥 Список викладачів порожній\n'
    all_teachers_str += '\nДодати викладача: /add_teacher'

    await message.answer(all_teachers_str)
    return


@dp.message_handler(commands='all_subjects')
async def all_subjects(message: types.Message):
    query = """SELECT subjects.subject_id, subjects.title, teachers.name
               FROM subjects
               LEFT OUTER JOIN teachers
                   USING (id_teacher)
               ORDER BY id_teacher"""
    my_cursor.execute(query)
    subjects = my_cursor.fetchall()

    all_subjects_str = '📚 Список усіх предметів:\n'
    if subjects:
        for i, title, teacher_name in subjects:
            all_subjects_str += f'\n{i}. {title}\nВикладає: {teacher_name}\n'
    else:
        all_subjects_str += '🫥 Список предметів порожній\n'
    all_subjects_str += '\nДодати предмет: /add_subject'

    await message.answer(all_subjects_str)
    return


@dp.message_handler(commands='all_students')
async def all_students(message: types.Message):
    query = """SELECT username, firstname FROM students;"""
    my_cursor.execute(query)
    students = my_cursor.fetchall()

    all_students_str = '🧑‍🎓 Список усіх зареєстрованих студентів:\n\n'
    if students:
        i = 1
        for username, firstname in students:
            all_students_str += f'{i}. {firstname} ({username})\n'
    else:
        all_students_str += '🫥 Список зареєстрованих студентів порожній\n'
    all_students_str += '\nДодати студента: /add_student'

    await message.answer(all_students_str)
    return


@dp.message_handler(commands='set_max')
async def set_max(message: types.Message):
    arguments = message.get_args()

    try:
        number = int(arguments)
    except ValueError:
        await message.answer('1️⃣ Щоб виставити максимальну довжину черги необхідно вказати число, більше за нуль'
                             '\n👉 Наприклад, /set_max 30')
        return

    if number < 1:
        await message.answer('☝ Мінімальна довжина черги - 1 студент'
                             '\n\nСпробувати задати довжину ще раз: /set_max <i>{затребувана довжина черги}</i>')
        return

    global max_in_queue
    max_in_queue = number

    await message.answer(f'🔄 Максимальна довжина черги тепер {number}')
    return


def get_first_free_pos(positions):
    if not positions:
        return 1
    for i in range(active_student, max_in_queue):  # зробити адаптивним максимальну кількість
        if i and i not in positions:
            return i

    return None


@dp.message_handler(commands='sign_up')
async def sign_up(message: types.Message):
    user = message.from_user
    add_user(user)
    user_id = user.id
    user_name = user.first_name

    arguments = message.get_args().split(' ')
    if len(arguments) not in (1, 2) or not arguments[0]:
        await message.answer('🗿 Ви ввели неправильну кількість аргументів'
                             '\n\n☝ Необхідно вказати назву або номер предмета, в чергу на який хочете записатися'
                             '\n\n💁 За бажанням також можна вказати конкретну позицію в черзі, якщо вона вільна'
                             '\n\n👉 Наприклад /sign_up Математика або /sign_up Математика 5')
        return

    data = arguments[0]
    subjects = get_subjects()
    sub_with_queue = get_subjects_with_queues()

    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects):
            subject = subjects[data - 1]
        else:
            await message.answer(f'❓ Предмет за номером {data} невідомий\n\nДодати предмет: /add_subject')
            return

    if subject not in subjects:
        await message.answer(f'❓ Предмет {subject} невідомий\n\nДодати предмет: /add_subject')
        return

    if subject not in sub_with_queue:
        await message.answer(f'Предмет {subject} не має черги\n\nДодати предмет: /add_subject')
        return

    check_stundent = """SELECT su.position
                        FROM sign_ups su
                        JOIN students st
                            USING (telegram_user_id)
                        JOIN queues qu
                            USING (id_queue)
                        JOIN subjects sb
                            USING (subject_id)
                        WHERE st.telegram_user_id = %s and sb.title = %s"""
    my_cursor.execute(check_stundent, (user_id, subject))
    exist_pos = my_cursor.fetchall()
    exist_pos = tuple(map(lambda x: x[0], exist_pos))

    if exist_pos:
        max_pos = max(exist_pos)
    else:
        max_pos = 0

    if max_pos > active_student:
        await message.answer(f'📃 {user.first_name} вже записаний(-а) в цю чергу на місце {exist_pos[0]}'
                             f'\n\n☝ Щоб перезаписатися на інше місце, спочатку випишіться з черги, '
                             f'а тоді запишіться заново'
                             '\n\nВиписатися з черги: /sign_out <i>{номер або назва предмета}</i>')
        return

    if len(arguments) == 1:  # Випадок, коли юзер вказав лише назву предмета. Записуємо на перше вільне місце
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
            await message.answer('🙆‍♀ Черга заповнена'
                                 '\n\n☝ Можна змінити максимальну кількість студентів у черзі в налаштуваннях')
            return

    else:  # Випадок, коли юзер вказав назву предмета та конкретне місце в черзі
        try:
            position = int(arguments[1])
        except ValueError:
            await message.answer('🗿 Ви неправильно вказуєте номер у черзі'
                                 '\n\n☝ Необхідно вказати назву або номер предмета та бажаний номер у черзі,'
                                 'в чергу якого бажаєте записатися'
                                 '\n\n👉 Наприклад /sign_up Математика 5')
            return

        if position < 0 or position > max_in_queue:
            await message.answer(f'🙆‍♀ Максимальний номер у черзі: {max_in_queue}')
            return

        if position <= active_student:
            await message.answer(f'🏃‍♂ Черга вже пройшла місце {position}. '
                                 f'Зараз здає студент на позиції {active_student}\n\n'
                                 f'⤵ Запишіться на місце попереду!')
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
            await message.answer(f'😔 На цю позицію вже записаний(-а) {name_of_student[0]}')
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

    await message.answer(f'✍ {user_name} було успішно записано в чергу на {subject} під номером {position}')
    return


@dp.message_handler(commands='sign_out')
async def sign_out(message: types.Message):
    user = message.from_user
    add_user(user)
    user_id = user.id
    user_name = user.first_name

    data = message.get_args()
    if not data:
        await message.answer('🗿 Ви неправильно вводите команду'
                             '\n\n☝ Необхідно вказати назву або номер предмета, чергу на який Ви хочете покинути'
                             '\n\n👉 Наприклад /sign_out Математика')
        return

    subjects = get_subjects()
    sub_with_queue = get_subjects_with_queues()

    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects):
            subject = subjects[data - 1]
        else:
            await message.answer(f'❓ Предмет за номером {data} невідомий'
                                 f'\n\nДодати предмет: /add_subject')
            return

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

                await message.answer(f'❌ {user_name} було успішно видалено з черги')
            else:
                await message.answer(f'👌🏼 Ви і так не були записані в чергу на {subject}')
        else:
            await message.answer(f'🫥 До предмета {subject} ще не створена черга'
                                 f'\n\nСтворити чергу: /create_queue')
    else:
        await message.answer(f'❓ Предмет {subject} невідомий'
                             f'\n\nДодати предмет: /add_subject')
    return


if __name__ == '__main__':
    try:
        print('\033[93mInitializing database...\n')
        db.connect_to_server()
        print('\033[92mSuccessfully connected to the database')

        db.start_settings()
        db.create_database()
        db.use_database()
        db.create_tables()
        db.end_settings()
        print('All tables are ready')
        print('\n\033[1mBOT STARTED\n\033[0m')

        my_cursor = db.my_cursor
        executor.start_polling(dp, skip_updates=True)

    except Exception as error:
        print('Cause: {}'.format(error))
