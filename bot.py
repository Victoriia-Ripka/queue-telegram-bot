import logging

import mysql.connector

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import db

API_TOKEN = '5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k'

bot = Bot(token=API_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


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
    text = '⚙ Всі команди бота <b>Q Bot KPI</b>:\n' \
           '\n/start — запустити бота для цієї групи' \
           '\n/help — вивести всі команди' \
           '\n/back — повернутися в головне меню, коли бот очікує якісь дані' \
           '\n/all_students — вивести всіх студентів' \
           '\n/all_subjects — вивести всі предмети' \
           '\n/all_teachers — вивести всіх викладачів' \
           '\n/add_subject — додати предмет' \
           '\n/add_teacher — додати викладача' \
           '\n/add_teacher_info — додати або оновити додаткову інформацію про викладача' \
           '\n/update_subject — оновити предмет' \
           '\n/update_teacher — оновити викладача' \
           '\n/delete_subject — видалити предмет' \
           '\n/delete_teacher — видалити викладача' \
           '\n/create_queue — створити чергу на предмет' \
           '\n/clear_queue — очистити чергу на предмет' \
           '\n/delete_queue — видалити чергу на предмет' \
           '\n/show_needed_queue — вивести конкретну чергу' \
           '\n/start_queue — розпочати чергу на предмет' \
           '\n/next — здійснити рух черги' \
           '\n/show_current_student — дізнатися, хто здає зараз' \
           '\n/set_max <i>{число}</i> — встановити максимальну довжину черги' \
           '\n/sign_up <i>{номер або назва предмету} {позиція в черзі (за бажанням)}</i> — ' \
           'записатися в чергу на предмет' \
           '\n/sign_out <i>{номер або назва предмету}</i> — виписатися з черги на предмет' \
           '\n/skip <i>{кількість студентів (за замовчуванням: 1)}</i> — пропустити певну кількість людей вперед'
    await message.answer(text)


# @dp.message_handler(commands='end')
# async def end(message: types.Message):
#     print('Start deleting DB...')
#     sql_command = """DROP TABLE IF EXISTS `{group_id}`.`teachers` ;"""
#     db.my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `{group_id}`.`Sign_ups` ;"""
#     db.my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `{group_id}`.`Queues` ;"""
#     db.my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `{group_id}`.`Students` ;"""
#     db.my_cursor.execute(sql_command)
#     sql_command = """DROP TABLE IF EXISTS `{group_id}`.`Subjects` ;"""
#     db.my_cursor.execute(sql_command)
#     print('All tables are deleted')
#     text = 'All tables are deleted'
#     await message.answer(text)


@dp.message_handler(commands='add_subject')
async def add_subject_start(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    subjects = get_subjects(group_id)
    string = ''
    if subjects:
        string += '📚 Список вже існуючих предметів:\n'
        for subject, i in zip(subjects, range(len(subjects))):
            string += f'{i + 1}. {subject}\n'
    else:
        string = '🫥 Список вже існуючих предметів порожній\n'
    
    teachers = get_teachers(group_id)
    if teachers:
        await Form.subject.set()
        string += '\n👩‍🏫 Список викладачів:\n'
        for teacher, i in zip(teachers, range(len(teachers))):
            string += f'{i + 1}. {teacher}\n'
        string += '\n📝 Напишіть назву предмету, який хочете додати, і номер викладача зі списку через пробіл' \
                  '\n👉 Наприклад: Алгоритмізація 4'
    else:
        string += '🫥 Список викладачів порожній\nСпочатку додайте викладачів, щоб додавати предмети!'
        string += '\n\nДодати викладача: /add_teacher'

    await message.answer(string)
    return


@dp.message_handler(state=Form.subject)
async def add_subject(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    teachers = get_teachers(group_id)
    subjects = get_subjects(group_id)

    data = message.values['text'].split(' ')
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return
    if len(data) >= 2:
        try:
            number = int(data[-1])
        except ValueError:
            await state.finish()
            await message.answer(f'1️⃣  Після назви повинен бути вказаний номер викладача зі списку'
                                 f'\n\nСпробувати ще раз: /add_subject')
            return

        if not 0 < number <= len(teachers):
            await state.finish()
            await message.answer(f'☹ Ви ввели неправильні дані. Номер викладача повинен бути зі списку'
                                 f'\n\nСпробувати ще раз: /add_subject')
            return

        teacher = teachers[number-1]
        teacher_id = get_teacher_id(group_id, teacher)
        separator = ' '
        data.pop()
        title = separator.join(data)

        print(len(title))
        if len(title) > 200:
            await state.finish()
            await message.answer('🙆‍♀ Задовга назва предмету (більше 200 символів)'
                                 '\n\nСпробувати ще раз: /add_subject')
            return

        subjects_lowercase = []
        for subject in subjects:
            subjects_lowercase.append(subject.lower())
        if title.lower() in subjects_lowercase:
            await state.finish()
            await message.answer('😉 Цей предмет уже доданий'
                                 '\n\nДодати інший предмет: /add_subject\nДодати викладача: /add_teacher')
            return

    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 2 параметри: назва предмету'
                             'і номер викладача зі списку'
                             '\n\nСпробувати ще раз: /add_subject')
        return

    new_subject = (title, teacher_id)
    sql = f'INSERT INTO `{group_id}`.subjects (title, id_teacher) VALUES (%s, %s);'
    try:
        db.my_cursor.execute(sql, new_subject)
    except mysql.connector.IntegrityError:
        await state.finish()
        await message.answer('😉 Цей предмет уже доданий'
                             '\n\nДодати інший предмет: /add_subject\nДодати викладача: /add_teacher')
        return
    except mysql.connector.DatabaseError:
        await state.finish()
        await message.answer('😳 Ви використовуєте емоджи або інші незрозумілі символи чи вводите занадто довгі дані'
                             '\n\nСпробувати ще раз: /add_subject')
        return
    else:
        db.mydb.commit()

    sql = f'SELECT name FROM `{group_id}`.teachers WHERE id_teacher = {teacher_id};'
    db.my_cursor.execute(sql)
    teacher_name = db.my_cursor.fetchone()[0]  # для виведення тексту у випадку успіху

    if db.my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /add_subject')
    else:
        await message.answer(f'✅ Предмет {title} викладача {teacher_name} додано до списку')
    await state.finish()
    return       
    

@dp.message_handler(commands='add_teacher')
async def add_teacher_start(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    await Form.teacher.set()
    teachers = get_teachers(group_id)
    if teachers:
        string = '👩‍🏫 Список уже доданих викладачів:\n'
        for subject, i in zip(teachers, range(len(teachers))):
            string += f'{i + 1}. {subject}\n'
    else:
        string = '🫥 Список викладачів порожній. Ви додасте першого викладача\n'
    string += '\n📝 Введіть ПІБ викладача\n' \
              '💁 За бажанням також можна вписати телеграм-тег, номер телефону та email, розділивши все комами'
    await message.answer(string)


@dp.message_handler(state=Form.teacher)
async def add_teacher(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    teachers = get_teachers(group_id)

    data = message.values['text'].split(', ')
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return

    if len(data) not in range(1, 5):
        await state.finish()
        await message.answer('🗿 Ви ввели забагато параметрів (більш ніж 4)\n\nСпробувати ще раз: /add_teacher')
        return

    name = data[0]
    if len(name) > 200:
        await state.finish()
        await message.answer('🙆‍♀ Задовге ім\' викладача (більше 200 символів)'
                             '\n\nСпробувати ще раз: /add_teacher')
        return

    teachers_lowercase = []
    for teacher in teachers:
        teachers_lowercase.append(teacher.lower())
    if name.lower() in teachers_lowercase:
        await state.finish()
        await message.answer('😉 Цей викладач уже доданий'
                             '\n\nДодати іншого викладача: /add_teacher\nДодати предмет: /add_subject')
        return
    allowed_name_symbols = ('-', '.', "'", "`")
    if not all(x.isalpha() or x.isspace() or x in allowed_name_symbols for x in name):
        await state.finish()
        await message.answer('🔤 Ім\'я викладача повинне складатися лише з літер та символів, '
                             'що використовуються в іменах\n\nСпробувати ще раз: /add_teacher')
        return
    if len(data) == 1:
        new_teacher = (name,)
        sql = f'INSERT INTO `{group_id}`.teachers (name) VALUES (%s);'
    else:
        username_telegram = data[1]
        username_telegram = username_telegram if username_telegram[0] == '@' else '@' + username_telegram
        if len(data) == 2:
            new_teacher = (name, username_telegram)
            sql = f'INSERT INTO `{group_id}`.teachers (name, username_telegram) VALUES (%s, %s);'
        elif len(data) == 3:
            phone_number = data[2]
            new_teacher = (name, username_telegram, phone_number)
            sql = f'INSERT INTO `{group_id}`.teachers (name, username_telegram, phone_number) VALUES (%s, %s, %s);'
        elif len(data) == 4:
            phone_number = data[2]
            email = data[3]
            new_teacher = (name, username_telegram, phone_number, email)
            sql = f'INSERT INTO `{group_id}`.teachers (name, username_telegram, phone_number, email)' \
                  f'VALUES (%s, %s, %s, %s);'
    try:
        db.my_cursor.execute(sql, new_teacher)
    except mysql.connector.IntegrityError:
        await state.finish()
        await message.answer('😉 Цей викладач уже доданий'
                             '\n\nДодати іншого викладача: /add_teacher\nДодати предмет: /add_subject')
        return
    except mysql.connector.DatabaseError:
        await state.finish()
        await message.answer('😳 Ви використовуєте емоджи або інші незрозумілі символи чи вводите занадто довгі дані'
                             '\n\nСпробувати ще раз: /add_teacher')
        return
    else:
        db.mydb.commit()

    if db.my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /add_subject')
    else:
        await message.answer(f'✅ Викладача {name} додано до списку')
    await state.finish()


@dp.message_handler(commands='add_teacher_info')
async def add_teacher_info_start(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    await Form.info.set()
    teachers = get_teachers(group_id)
    if teachers:
        string = '👩‍🏫 Список викладачів:\n'
        for teacher, i in zip(teachers, range(len(teachers))):
            string += f'{i + 1}. {teacher}\n'
        string += '\n📝 Введіть номер викладача зі списку, після чого через кому додайте всю необхідну інформацію'
    else:
        string = '🫥 Список викладачів порожній. Спочатку додайте викладача'
        string += '\n\nДодати викладача: /add_teacher'
    await message.answer(string)


@dp.message_handler(state=Form.info)
async def add_teacher_info(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    data = message.values['text'].split(', ')
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return

    if len(data) >= 2:
        try:
            number = int(data[0])
        except ValueError:
            await state.finish()
            await message.answer('1️⃣  Першим повинен бути номер\n\nСпробувати ще раз: /add_teacher_info')
            return
        separator = ' '
        del data[0]

        info = separator.join(data)
        max_info_size = 1000
        if len(info) > max_info_size:
            await state.finish()
            await message.answer(f'🙆‍♀ Завеликий об\'єм інформації! Введіть не більше {max_info_size} символів '
                                 'включно з пробілами\n\nСпробувати ще раз: /add_teacher_info')
            return

        name = get_teachers(group_id)[number - 1]
        id = get_teacher_id(group_id, name)

        db.my_cursor.execute(f"SELECT info FROM `{group_id}`.teachers WHERE id_teacher = %s", (id,))
        info_exists = bool(db.my_cursor.fetchone()[0])

        new_info = (info, id)
        sql = f'UPDATE `{group_id}`.teachers SET info = %s WHERE id_teacher = %s;'
        try:
            db.my_cursor.execute(sql, new_info)
        except mysql.connector.DatabaseError:
            await state.finish()
            await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /add_teacher_info')
            return
        else:
            db.mydb.commit()
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 2 параметри через кому: '
                             'номер викладача зі списку і додаткова інформація про нього \n\n'
                             'Спробувати ще раз: /add_teacher_info')
        return

    if db.my_cursor.rowcount < 1:
        await message.answer('🤔 Здається, Ви ввели інформацію, яка є ідентичною до вже існуючої'
                             '\n\nСпробувати ще раз: /add_teacher_info')
    else:
        if info_exists:
            await message.answer(f'🔄 Інформацію оновлено')
        else:
            await message.answer(f'✅ Інформацію додано')
    await state.finish()
    return


@dp.message_handler(commands='update_subject')
async def update_subject_start(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    subjects = get_subjects_with_teachers(group_id)
    if subjects:
        await Form.update_subject.set()
        string = '📚 Список існуючих предметів:\n\n'
        for subject, i in zip(subjects, range(len(subjects))):
            string += f'{subject[0]}. {subject[1]} — {subject[2]}\n'
        
        teachers = get_teachers(group_id)
        string += '\n👩‍🏫 Список доданих викладачів:\n'
        for teacher, i in zip(teachers, range(len(teachers))):
            string += f'{i + 1}. {teacher}\n'
        string += '\n📝 Введіть номер предмету зі списку, нову назву предмету та' \
                  'номер викладача зі списку через пробіл' \
                  '\n👉 Наприклад: 3 Алгоритми і структури даних 5'
    else:
        string = '🫥 Список предметів порожній. Спочатку додайте предмет'
        string += '\n\nДодати предмет: /add_subject'
    await message.answer(string)
    return 


@dp.message_handler(state=Form.update_subject)
async def update_subject(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    subjects = get_subjects(group_id)
    teachers = get_teachers(group_id)
    data = message.values['text'].split(' ')
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return
    if len(data) > 2:
        try:
            subject_number = int(data[0])
            teacher_number = int(data[-1])
        except ValueError:
            await state.finish()
            await message.answer('1️⃣ Номери предмету і викладача повинні бути числами'
                                 '\n\nСпробувати ще раз: /update_subject')
            return
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 3 параметри: номер предмету'
                             'зі списку, нова назва предмету і номер викладача зі списку'
                             '\n\nСпробувати ще раз: /update_subject')
        return

    if not 0 < subject_number <= len(subjects) or not 0 < teacher_number <= len(teachers):
        await state.finish()
        await message.answer('☹ Ви ввели неправильні дані!\n\nНеобхідно ввести номер предмету зі списку, '
                             'нову назву предмету та номер викладача зі списку'
                             '\n\nСпробувати ще раз: /update_subject')
        return

    separator = ' '
    del data[0]
    del data[-1]
    title = separator.join(data)

    if len(title) > 200:
        await state.finish()
        await message.answer('🙆‍♀ Задовга назва предмету (більше 200 символів)'
                             '\n\nСпробувати ще раз: /update_subject')
        return

    previous_title = subjects[subject_number - 1]
    subject_id = get_subject_id(group_id, previous_title)

    subjects_without_current = list(subjects)
    subjects_without_current_lowercase = []
    for subject in subjects:
        if subject == previous_title:
            subjects_without_current.remove(previous_title)
    for subject in subjects_without_current:
        subjects_without_current_lowercase.append(subject.lower())
    if title.lower() in subjects_without_current_lowercase:
        await state.finish()
        await message.answer(f'🙄 Предмет з назвою {title} вже є'
                             f'\n\nСпробувати ще раз: /update_subject')
        return

    name = teachers[teacher_number - 1]
    teacher_id = get_teacher_id(group_id, name)

    new_subject = (title, teacher_id, subject_id)

    sql = f'UPDATE `{group_id}`.subjects SET title = %s, id_teacher = %s WHERE subject_id = %s;'
    try:
        db.my_cursor.execute(sql, new_subject)
    except mysql.connector.IntegrityError:
        await state.finish()
        await message.answer('😉 Цей предмет уже доданий'
                             '\n\nСпробувати ще раз: /update_subject\nДодати предмет: /add_subject')
        return
    except mysql.connector.DatabaseError:
        await state.finish()
        await message.answer('🔧 Виникла проблема із запитом до бази даних'
                             '\n\nСпробувати ще раз: /update_subject')
        return
    else:
        db.mydb.commit()

    if db.my_cursor.rowcount < 1:
        await message.answer('🤔 Здається, Ви ввели дані, які є ідентичними до вже існуючих'
                             '\n\nСпробувати ще раз: /update_subject')
    else:
        await message.answer(f'🔄 Предмет {title} успішно оновлений')
    await state.finish()
    return


@dp.message_handler(commands='update_teacher')
async def update_teacher_start(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    teachers = get_teachers_with_all_info(group_id)
    if teachers:
        await Form.update_teacher.set()
        string = '👩‍🏫 Список викладачів:\n'
        for i, name, username_telegram, phone_number, email, info in teachers:
            username_telegram = username_telegram if username_telegram else '(немає)'
            phone_number = phone_number if phone_number else '(немає)'
            email = email if email else '(немає)'
            string += f'\n{i}. {name}\n' \
                      f'  💬  Телеграм: {username_telegram}\n' \
                      f'  📱  Номер телефону: {phone_number}\n' \
                      f'  ✉  Ел. пошта: {email}\n'
        string += '\n📝 Введіть номер викладача зі списку, ' \
                  'після цього ім\'я, нік в телеграмі, номер телефону та email. Все через кому. ' \
                  'Якщо якоїсь інформації немає, поставте "-"' \
                  '\n👉 Наприклад: 2, Коваленко Іван Андрійович, -, +380000000000, -' \
                  '\n\n☝ Якщо ви бажаєте оновити інформацію про викладача, скористайтесь для цього окремою командою. ' \
                  'Щоб додати викладача до предмету, потрібно вказати його при створенні або ж оновленні предмету' \
                  '\n\nДодати або оновити інформацію про викладача: /add_teacher_info' \
                  '\nДодати предмет: /add_subject\nОновити предмет: /update_subject'
    else:
        string = '🫥 Список викладачів порожній. Спочатку додайте викладачів до списку'
        string += '\n\nДодати викладача: /add_teacher'
    await message.answer(string)


@dp.message_handler(state=Form.update_teacher)
async def update_teacher(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    teachers = get_teachers(group_id)
    data = message.values['text'].split(', ')
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return
    if len(data) == 5:
        number = data[0]

        if len(data[1]) > 200:
            await state.finish()
            await message.answer('🙆‍♀ Задовге ім\'я викладача (більше 200 символів)'
                                 '\n\nСпробувати ще раз: /update_teacher')
            return
        name = data[1]

        if len(data[2]) > 60:
            await state.finish()
            await message.answer('😔 На жаль, задовгий нікнейм Telegram. Сконтактуйте з розробниками бота'
                                 '\n\nСпробувати ще раз: /update_teacher')
            return
        username_telegram = data[2] if data[2] != '-' else None

        if len(data[3]) > 20:
            await state.finish()
            await message.answer('🙆‍♀ Задовгий номер телефону. Будь ласка, вмістіть його у 20 символів'
                                 '\n\nСпробувати ще раз: /update_teacher')
            return
        phone_number = data[3] if data[3] != '-' else None

        if len(data[4]) > 70:
            await state.finish()
            await message.answer('😔 На жаль, задовга електронна пошта. Сконтактуйте з розробниками бота'
                                 '\n\nСпробувати ще раз: /update_teacher')
            return
        email = data[4] if data[4] != '-' else None
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели неправильну кількість параметрів. Необхідно 5 параметрів через кому:'
                             'номер викладача зі списку, ім\'я викладача, нік в телеграмі, номер телефону та email. '
                             'Якщо якоїсь інформації немає, необхідно поставити "-".'
                             '\n\nСпробувати ще раз: /update_teacher')
        return

    try:
        number = int(number)
    except ValueError:
        await state.finish()
        await message.answer('1️⃣ Першим параметром потрібно ввести номер викладача зі списку'
                             '\n\nСпробувати ще раз: /update_teacher')
        return

    if not 0 < number <= len(teachers):
        await state.finish()
        await message.answer(f'☹ Ви ввели неправильні дані. Номер викладача повинен бути зі списку'
                             '\n\nСпробувати ще раз: /update_teacher')
        return

    previous_name = teachers[number - 1]
    teacher_id = get_teacher_id(group_id, previous_name)

    teachers_without_current = list(teachers)
    teachers_without_current_lowercase = []
    for teacher in teachers:
        if teacher == previous_name:
            teachers_without_current.remove(previous_name)
    for teacher in teachers_without_current:
        teachers_without_current_lowercase.append(teacher.lower())
    if name.lower() in teachers_without_current_lowercase:
        await state.finish()
        await message.answer(f'🙄 Викладач з іменем {name} вже є'
                             f'\n\nСпробувати ще раз: /update_teacher')
        return

    if username_telegram and username_telegram[0] != '@':
        username_telegram = '@' + username_telegram

    new_teacher_data = (name, username_telegram, phone_number, email, teacher_id)
    sql = f"""UPDATE `{group_id}`.teachers
             SET name = %s, username_telegram = %s, phone_number = %s, email = %s
             WHERE id_teacher = %s"""
    try:
        db.my_cursor.execute(sql, new_teacher_data)
    except mysql.connector.IntegrityError:
        await state.finish()
        await message.answer('😉 Цей викладач уже доданий'
                             '\n\nСпробувати ще раз: /update_teacher\nДодати викладача: /add_teacher')
        return
    except mysql.connector.DatabaseError:
        await state.finish()
        await message.answer('😳 Ви використовуєте емоджи або інші незрозумілі символи чи вводите занадто довгі дані'
                             '\n\n🔧 Якщо ні, то виникла якась інша проблема із запитом до бази даних'
                             '\n\nСпробувати ще раз: /update_teacher')
        return
    else:
        db.mydb.commit()

    if db.my_cursor.rowcount < 1:
        await message.answer('🤔 Здається, Ви ввели дані, які є ідентичними до вже існуючих'
                             '\n\nСпробувати ще раз: /update_teacher')
    else:
        await message.answer(f'🔄 Викладач {name} успішно оновлений')
    await state.finish()
    return


@dp.message_handler(commands='delete_subject')
async def delete_subject_start(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    await Form.delete_subject.set()
    subjects = get_subjects_with_id(group_id)
    string = '📚 Список існуючих предметів:\n'
    for subject, i in zip(subjects, range(len(subjects))):
        string += f'{i + 1}. {subject[1]}\n'
    string += '\n📝 Напишіть номер предмету, який пострібно видалити, зі списку'
    await message.answer(string)
    return 


@dp.message_handler(state=Form.delete_subject)
async def delete_subject(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    subjects = get_subjects(group_id)
    data = message.values['text'].split(' ')
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return
    if len(data) == 1:
        try:
            number = int(data[0])
        except ValueError:
            await state.finish()
            await message.answer('1️⃣ Потрібно ввести номер предмету зі списку\n\nСпробувати ще раз: /delete_subject')
            return

        if not 0 < number <= len(subjects):
            await state.finish()
            await message.answer(f'☹ Ви ввели неправильні дані. Номер предмету повинен бути зі списку'
                                 f'\n\nСпробувати ще раз: /delete_subject')
            return

    else:
        await state.finish()
        await message.answer('🗿 Ви ввели більш ніж одне число\n\nСпробувати ще раз: /delete_subject')
        return

    title = subjects[number - 1]
    id = get_subject_id(group_id, title)

    sql = f'DELETE FROM `{group_id}`.subjects WHERE subject_id = %s;'

    try:
        db.my_cursor.execute(sql, (id,))
    except mysql.connector.IntegrityError:
        await state.finish()
        await message.answer('🗒 На цей предмет існує черга. Спочатку видаліть її\n\n'
                             'Видалити чергу: /delete_queue\nСпробувати ще раз: /delete_subject')
        return
    db.mydb.commit()

    if db.my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_subject')
    else:
        await message.answer(f'🗑 Предмет було успішно видалено')
    await state.finish()
    return


@dp.message_handler(commands='delete_teacher')
async def delete_teacher_start(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    await Form.delete_teacher.set()
    teachers = get_teachers_with_id(group_id)
    string = '👩‍🏫 Список викладачів:\n'
    for teacher, i in zip(teachers, range(len(teachers))):
        string += f'{i + 1}. {teacher[1]}\n'
    string += '\n📝 Введіть номер викладача, якого потрібно видалити, зі списку\n\n' \
              '☝ Якщо викладач читає якийсь предмет, то видалити його неможливо. ' \
              'В такому випадку або видаліть предмет, який викладає цей викладач, або змініть викладача для предмету'
    string += '\n\nВидалити предмет: /delete_subject\nЗмінити викладача для предмету: /update_subject'
    await message.answer(string)
    return


@dp.message_handler(state=Form.delete_teacher)
async def delete_teacher(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    teachers = get_teachers(group_id)
    data = message.values['text'].split(' ')
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return
    if len(data) == 1:
        try:
            number = int(data[0])
        except ValueError:
            await state.finish()
            await message.answer('1️⃣ Потрібно ввести номер викладача зі списку\n\nСпробувати ще раз: /delete_teacher')
            return
    else:
        await state.finish()
        await message.answer('🗿 Ви ввели більш ніж одне число\n\nСпробувати ще раз: /delete_teacher')
        return
    if not 0 < number <= len(teachers):
        await state.finish()
        await message.answer(f'☹ Ви ввели неправильні дані. Номер викладача повинен бути зі списку'
                             f'\n\nСпробувати ще раз: /delete_teacher')
        return

    name = teachers[number - 1]
    id = get_teacher_id(group_id, name)
    sql = f'DELETE FROM `{group_id}`.teachers WHERE id_teacher = %s;'
    try:
        db.my_cursor.execute(sql, (id,))
    except mysql.connector.IntegrityError:
        await state.finish()
        await message.answer('📙 Цей викладач читає якийсь предмет. Спершу видаліть цей предмет '
                             'або призначте для нього іншого викладача\n\nВидалити предмет: /delete_subject'
                             '\nЗмінити викладача для предмету: /update_subject\nСпробувати ще раз: /delete_teacher')
        return
    else:
        db.mydb.commit()

    if db.my_cursor.rowcount < 1:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_teacher')
    else:
        await message.answer(f'🗑 {name} було успішно видалено')
    await state.finish()
    return


def get_teachers(group_id):
    db.my_cursor.execute(f"""SELECT name FROM `{group_id}`.teachers
                            ORDER BY id_teacher;""")
    result = db.my_cursor.fetchall()

    teachers = []
    for teacher in result:
        teachers.append(teacher[0])

    return tuple(teachers)


def get_teacher_id(group_id, teacher_name):
    query = f"""SELECT id_teacher
                FROM `{group_id}`.teachers
                WHERE name = %s"""
    db.my_cursor.execute(query, (teacher_name,))
    teacher_id = int(db.my_cursor.fetchone()[0])

    return teacher_id


def get_teachers_with_id(group_id):
    db.my_cursor.execute(f"""SELECT id_teacher, name FROM `{group_id}`.teachers
                            ORDER BY id_teacher;""")
    result = db.my_cursor.fetchall()

    teachers = []
    for i, teacher in enumerate(result):
        teachers.append((i+1, teacher[1]))

    return tuple(teachers)


def get_teachers_with_all_info(group_id):
    db.my_cursor.execute(f"""SELECT `name`, `username_telegram`, `phone_number`, `email`, `info`
                            FROM `{group_id}`.teachers
                            ORDER BY id_teacher;""")
    result = db.my_cursor.fetchall()

    teachers = []
    for i, teacher in enumerate(result):
        teachers.append((i+1, teacher[0], teacher[1], teacher[2], teacher[3], teacher[4]))

    return tuple(teachers)


def get_subjects(group_id):
    db.my_cursor.execute(f"""SELECT title FROM `{group_id}`.subjects
                            ORDER BY subject_id""")
    result = db.my_cursor.fetchall()

    subjects = []
    for subject in result:
        subjects.append(subject[0])

    return tuple(subjects)


def get_subjects_with_id(group_id):
    db.my_cursor.execute(f"""SELECT subject_id, title FROM `{group_id}`.subjects
                            ORDER BY subject_id;""")
    result = db.my_cursor.fetchall()

    subjects = []
    for i, subject in enumerate(result):
        subjects.append((i+1, subject[1]))

    return tuple(subjects)


def get_subjects_with_teachers(group_id):
    db.my_cursor.execute(f"""SELECT subject_id, title, name
                         FROM `{group_id}`.`Subjects`
                         INNER JOIN `{group_id}`.teachers ON subjects.id_teacher = teachers.id_teacher
                         ORDER BY subject_id;""")
    result = db.my_cursor.fetchall()

    subjects = []
    for i, subject in enumerate(result):
        subjects.append((i+1, subject[1], subject[2]))

    return tuple(subjects)


def get_subjects_with_queues(group_id):
    db.my_cursor.execute(f"""SELECT DISTINCT title FROM `{group_id}`.subjects
                      WHERE subject_id IN
                      (SELECT subject_id FROM `{group_id}`.queues)
                      ORDER BY subject_id;""")
    result = db.my_cursor.fetchall()

    subjects_with_queues = []

    for subject in result:
        subjects_with_queues.append(subject[0])

    return tuple(subjects_with_queues)


def get_subject_id(group_id, subject=None):
    db.my_cursor.execute(f'SELECT `active_subject` FROM `{group_id}`.system_settings;')
    active_subject = db.my_cursor.fetchone()[0]

    subject = subject if subject else active_subject

    query = f"""SELECT subject_id  # неможливо скористатися f-стрічкою через предмети, що мають у назві апостроф
               FROM `{group_id}`.subjects
               WHERE title = %s;"""
    db.my_cursor.execute(query, (subject,))
    temp = db.my_cursor.fetchone()

    if temp:
        subject_id = temp[0]
        return subject_id
    else:
        return 0


@dp.message_handler(commands='create_queue')
async def create_queue(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    await Form.create_queue_st.set()
    subjects = get_subjects(group_id)
    if subjects:
        string = '📝 Оберіть предмет, на який хочете створити чергу:\n\n'
        for subject, i in zip(subjects, range(len(subjects))):
            string += f'{i + 1}. {subject}\n'
    else:
        string = '🫥 Список предметів порожній\n'
    string += '\nДодати предмет: /add_subject'
    await message.answer(string)


@dp.message_handler(state=Form.create_queue_st)
async def create_queue(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    subjects = get_subjects(group_id)
    subjects_with_queues = get_subjects_with_queues(group_id)

    data = message.values['text']
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return

    #  Вибір предмету відбувається написання назвою або номером
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
        subject_id = get_subject_id(group_id, subject)

        if subject_id:
            try:
                db.my_cursor.execute(f'INSERT INTO `{group_id}`.queues (id_queue, subject_id)'
                                     f'VALUES(DEFAULT, %s)', (subject_id,))
            except mysql.connector.DatabaseError:
                await state.finish()
                await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /add_subject')
                return
            else:
                db.mydb.commit()
            await message.answer(f'✅ Чергу на предмет {subject} створено')
        else:
            await message.answer(f'🫥 Предмету {subject} немає у списку предметів'
                                 f'\n\nДодати предмет: /add_subject')

    await state.finish()
    return


@dp.message_handler(commands='clear_queue')
async def clear_queue(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    subjects_with_queues = get_subjects_with_queues(group_id)
    if subjects_with_queues:
        await Form.clear_queue_st.set()
        string = '📚 Список усіх предметів, на які існують черги:\n'
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            string += f'{i + 1}. {subject}\n'
        string += '\n📝 Введіть номер предмету, на який бажаєте очистити чергу'
    else:
        string = '🫥 Список предметів з чергами порожній' \
              '\n\nСтворити чергу на предмет: /create_queue\nДодати предмет: /add_subject'
    await message.answer(string)


@dp.message_handler(state=Form.clear_queue_st)
async def clear_queue(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    subjects = get_subjects(group_id)
    subjects_with_queues = get_subjects_with_queues(group_id)

    data = message.values['text']
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return

    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects):
            subject = subjects_with_queues[data - 1]
        else:
            await message.answer(f'❓ Предмет за номером {data} невідомий'
                                 f'\n\nДодати предмет: /add_subject')
            await state.finish()
            return

    if subject in subjects:
        if subject in subjects_with_queues:
            delete_users = f"""DELETE sign_ups FROM `{group_id}`.sign_ups
                              JOIN `{group_id}`.queues
                                     USING(id_queue)
                              JOIN `{group_id}`.subjects sb
                                     USING(subject_id)
                              WHERE sb.title = %s;"""
            try:
                db.my_cursor.execute(delete_users, (subject,))
            except mysql.connector.DatabaseError:
                await state.finish()
                await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /clear_queue')
                return
            else:
                db.mydb.commit()
            await message.answer(f'🧹 Черга на предмет {subject} очищена')
        else:
            await message.answer(f'🫥 Черга на предмет {subject} ще не створена'
                                 f'\n\nСтворити чергу: /create_queue')
    else:
        await message.answer(f'🫥 предмету {subject} немає у списку'
                             f'\n\nДодати предмет: /add_subject')
    db.my_cursor.execute(f'UPDATE `{group_id}`.system_settings SET `active_student` = 0;')
    db.mydb.commit()
    await state.finish()
    return


@dp.message_handler(commands='delete_queue')
async def delete_queue(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    subjects_with_queues = get_subjects_with_queues(group_id)

    if subjects_with_queues:
        await Form.delete_queue_st.set()
        string = '📚 Список усіх предметів з чергами:\n'
        for i, subject in enumerate(subjects_with_queues):
            string += f'{i + 1}. {subject}\n'
        string += '\nДодати предмет: /add_subject\nСтворити чергу: /create_queue'
    else:
        string = '🫥 Ще не створено жодної черги'
        string += '\n\nСтворити чергу: /create_queue'
    await message.answer(string)


@dp.message_handler(state=Form.delete_queue_st)
async def delete_queue(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    subjects = get_subjects(group_id)
    subjects_with_queues = get_subjects_with_queues(group_id)

    data = message.values['text']
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return

    try:
        data = int(data)
    except ValueError:
        subject = data
    else:
        if 0 < data <= len(subjects):
            subject = subjects_with_queues[data - 1]
        else:
            await message.answer(f'❓ Предмет за номером {data} невідомий'
                                 f'\n\nДодати предмет: /add_subject\nСтворити чергу: /create_queue')
            await state.finish()
            return

    if subject in subjects:
        if subject in subjects_with_queues:
            delete_users = f"""DELETE sign_ups FROM `{group_id}`.sign_ups
                              JOIN `{group_id}`.queues
                                  USING(id_queue)
                              JOIN `{group_id}`.subjects sb
                                  USING(subject_id)
                              WHERE sb.title = %s;"""
            try:
                db.my_cursor.execute(delete_users, (subject,))
            except mysql.connector.DatabaseError:
                await state.finish()
                await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_queue')
                return
            else:
                db.mydb.commit()
            delete_users = f"""DELETE queues FROM `{group_id}`.queues
                              JOIN `{group_id}`.subjects sb
                                  USING(subject_id)
                              WHERE sb.title = %s;"""
            try:
                db.my_cursor.execute(delete_users, (subject,))
            except mysql.connector.DatabaseError:
                await state.finish()
                await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /delete_queue')
                return
            else:
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
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    await Form.show_queue_st.set()
    subjects_with_queues = get_subjects_with_queues(group_id)

    if subjects_with_queues:
        string = '📝 Виберіть предмет, на який шукаєте чергу:\n'
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            string += f'{i + 1}. {subject}\n'
        string += '\n☝ Якщо на ваш предмет ще немає черги, Ви можете створити її'
    else:
        string = '🫥 Ще не створено жодної черги'

    string += '\n\nСтворити чергу: /create_queue\n'
    string += 'Отримати всі предмети: /get_subjects\n'
    string += 'Додати предмет: /add_subject'

    await message.answer(string)


@dp.message_handler(state=Form.show_queue_st)
async def show_needed_queue(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    subjects_with_queues = get_subjects_with_queues(group_id)

    data = message.values['text']
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return
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

    queue_str = queue_to_str(fetch_queue(group_id, get_subject_id(group_id, subject)))

    await message.answer(queue_str)

    await state.finish()

    return


def fetch_queue(group_id, subject_id):
    query = f"""SELECT position, username, firstname
                FROM `{group_id}`.sign_ups
                INNER JOIN `{group_id}`.students
                ON sign_ups.telegram_user_id = students.telegram_user_id
                AND id_queue = (SELECT id_queue FROM `{group_id}`.queues
                                WHERE subject_id = {subject_id})
                ORDER BY position;"""
    db.my_cursor.execute(query)
    queue = db.my_cursor.fetchall()

    return queue


def get_sign_up(group_id, subject=None, student=None):
    db.my_cursor.execute(f'SELECT `active_subject`, `active_student` FROM `{group_id}`.system_settings;')
    fetched = db.my_cursor.fetchone()
    active_subject = fetched[0] if fetched[0] else ''
    active_student = fetched[1]
    subject = subject if subject else active_subject
    student = student if student else active_student

    sign_up_str = ''
    if not subject or not student:
        sign_up_str += '🙄 Жодна черга не активна\n\nРозпочати чергу: /start_queue'
        return sign_up_str

    queue = fetch_queue(group_id, get_subject_id(group_id, subject))

    if queue:
        positions = tuple(map(lambda x: x[0], queue))

        if student != positions[-1] + 1:
            while student not in positions:
                student += 1

            next_st = student + 1
            if student != positions[-1]:
                while next_st not in positions:
                    next_st += 1

            for i, username, firstname in queue:
                if i == student:
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
    sign_up_str += '\nЗаписатися в чергу: /sign_up <i>{номер або назва предмету} {місце в черзі (за бажанням)}</i>' \
                   '\nВиписатися з черги: /sign_out <i>{номер або назва предмету}</i>' \
                   '\nВсі предмети: /all_subjects'

    return sign_up_str


def queue_to_str(queue):
    queue_str = ''
    if queue:
        for i, username, firstname in queue:
            queue_str += f'{i}. {firstname} ({username})\n' if username else f'{i}. {firstname}\n'
    else:
        queue_str += '🫥 Черга порожня\n'
    queue_str += '\nЗаписатися в чергу: /sign_up <i>{номер або назва предмету} {місце в черзі (за бажанням)}</i>' \
                 '\nВиписатися з черги: /sign_out <i>{номер або назва предмету}</i>' \
                 '\nВсі предмети: /all_subjects'

    return queue_str


def active_queue_to_str(queue, end, active_student=0, next_student=0):
    # функція, що просто виводить активну чергу, не повинна змінювати значення активного студента

    queue_str = ''
    if queue:
        if end:
            for i, username, firstname in queue:
                queue_str += f'<del>{i}. {firstname} ({username})</del>\n' if username else f'<del>{i}. {firstname}</del>\n'
            queue_str += '\nЧерга закінчена 🔚\n'
        else:
            for i, username, firstname in queue:
                if i == active_student:
                    queue_str += f'{i}. <b>{firstname} (@{username})</b> 🟢\n' if username else f'{i}. <b>{firstname}</b> 🟢\n'
                elif i == next_student:
                    queue_str += f'{i}. <i>{firstname} (@{username}) — приготуватися</i>\n' if username else f'{i}. <i>{firstname} — приготуватися</i>\n'
                elif i < active_student:
                    queue_str += f'<del>{i}. {firstname} ({username})</del>\n' if username else f'<del>{i}. {firstname}</del>\n'
                else:
                    queue_str += f'{i}. {firstname} ({username})\n' if username else f'{i}. {firstname}\n'
            queue_str += '\nЧерга активна ☑\n'
    else:
        queue_str += '🫥 Черга порожня\n'
    queue_str += '\nЗаписатися в чергу: /sign_up <i>{номер або назва предмету} {місце в черзі (за бажанням)}</i>' \
                 '\nВиписатися з черги: /sign_out <i>{номер або назва предмету}</i>' \
                 '\nВидалити чергу: /delete_queue' \
                 '\nВсі предмети: /all_subjects'

    return queue_str


def add_user(user, group_id):
    user_id = user.id
    name = user.first_name
    username = user.username if user.username else None

    # Записуємо користувача в базу, якщо його немає
    get_user = f'SELECT * FROM `{group_id}`.students WHERE telegram_user_id = %s'
    db.my_cursor.execute(get_user, (user_id,))
    exists = db.my_cursor.fetchone()

    if not exists:
        put_user = f'INSERT INTO `{group_id}`.students VALUES(%s, %s, %s)'
        db.my_cursor.execute(put_user, (user_id, username, name))  # вставка даних і так безпечна
        db.mydb.commit()
    return


@dp.message_handler(commands='start_queue')
async def start_queue(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return

    subjects_with_queues = get_subjects_with_queues(group_id)

    if subjects_with_queues:
        await Form.start_queue_st.set()
        string = '📝 Виберіть предмет для запуску черги:\n'
        for subject, i in zip(subjects_with_queues, range(len(subjects_with_queues))):
            string += f'{i + 1}. {subject}\n'
        string += '\n☝ Якщо на ваш предмет ще немає черги, Ви можете створити її'
    else:
        string = '🫥 Ще не створено жодної черги'
    string += '\n\nСтворити чергу: /create_queue'
    # конкретно в цьому випадку можна створити однакову підсказку для обох випадків if/else

    await message.answer(string)


@dp.message_handler(state=Form.start_queue_st)
async def start_queue(message: types.Message, state: FSMContext):
    group_id = str(message.chat.id)
    subjects_with_queues = get_subjects_with_queues(group_id)

    data = message.values['text']
    if message.values['text'][0] == '/':
        if message.values['text'] == '/back' or message.values['text'] == '/back@kpi_q_bot':
            await state.finish()
            await message.answer('🔙 Повернуто в головне меню')
            return
        else:
            await message.answer('📋 Перед використанням нової команди '
                                 'завершіть роботу зі старою або поверніться в головне меню командою /back'
                                 '\n\n⬆ Зараз бот досі очікує відповіді на попереднє повідомлення')
            return

    try:
        data = int(data)
    except ValueError:
        if data in subjects_with_queues:
            active_subject = data
            db.my_cursor.execute(f'UPDATE `{group_id}`.system_settings SET `active_subject` = {active_subject};')
            db.mydb.commit()
        else:
            await message.answer(f'🫥 Немає черги на предмет під назвою {data}'
                                 f'\n\nСтворити чергу: /create_queue\nДодати предмет: /add_subject')
            await state.finish()
            return
    else:
        if 0 < data <= len(subjects_with_queues):
            active_subject = subjects_with_queues[data - 1]
            db.my_cursor.execute(f"UPDATE `{group_id}`.system_settings SET `active_subject` = '{active_subject}';")
            db.mydb.commit()
        else:
            await message.answer(f'🫥 Немає черги на предмет під номером {data}'
                                 f'\n\nСтворити чергу: /create_queue\nДодати предмет: /add_subject')
            await state.finish()
            return

    active_student = 0
    db.my_cursor.execute(f"UPDATE `{group_id}`.system_settings SET `active_student` = '{active_student}';")
    db.mydb.commit()

    await next(message)

    await state.finish()

    return


@dp.message_handler(commands='next')
async def next(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    db.my_cursor.execute(f'SELECT `active_subject`, `active_student` FROM `{group_id}`.system_settings;')
    fetched = db.my_cursor.fetchone()
    active_subject = fetched[0]
    active_student = fetched[1]

    if not active_subject:
        await message.answer('🙄 Жодна черга не активна\n\nРозпочати чергу: /start_queue')
        return
    else:
        active_student += 1

    queue = fetch_queue(group_id, get_subject_id(group_id))

    positions = tuple(map(lambda x: x[0], queue))

    if queue and active_student != positions[-1] + 1:
        # перевірка на наявність черги на вищому рівні за функцію active_queue_to_str()
        # потрібна для того, щоб запобігти нескінченному виконанню циклів while
        # і убезпечитися від зміни активного студента
        end = False

        while active_student not in positions:
            active_student += 1
        db.my_cursor.execute(f'UPDATE `{group_id}`.system_settings SET `active_student` = {active_student};')
        db.mydb.commit()

        next_student = active_student + 1
        if active_student != positions[-1]:
            print(f'Ми пройшли перевірку на неостанній елемент, коли active_student та next_student '
                  f'мали значення {active_student} та {next_student}. Останній елемент в позишинс: {positions[-1]}')
            while next_student not in positions:
                next_student += 1
        print(next_student)
        queue_str = active_queue_to_str(queue, end, active_student, next_student)
    else:
        if not queue:
            active_student = 0
            db.my_cursor.execute(f'UPDATE `{group_id}`.system_settings SET `active_student` = {active_student};')
            db.mydb.commit()
        end = True
        queue_str = active_queue_to_str(queue, end)

        active_subject = ''
        active_student = 0
        db.my_cursor.execute(f"UPDATE `{group_id}`.system_settings "
                             f"SET `active_student` = {active_student}, `active_subject` = '{active_subject}';")
        db.mydb.commit()

    await message.answer(queue_str)


@dp.message_handler(commands='skip')
async def skip(message: types.Message):
    group_id = str(message.chat.id)
    db.my_cursor.execute(f'SELECT `active_subject`, `active_student` FROM `{group_id}`.system_settings;')
    fetched = db.my_cursor.fetchone()
    active_subject = fetched[0]
    active_student = fetched[1]

    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    if not active_subject:
        await message.answer('🙄 Пропустити студента(-ів) можна лише в активній черзі!')
        return

    user = message.from_user
    add_user(user, group_id)
    user_id = user.id
    user_name = user.first_name

    arguments = message.get_args().split(' ')
    if len(arguments) not in (0, 1):
        await message.answer('🗿 Ви ввели забагато аргументів'
                             '\n\n☝ Необхідно вказати кількість місць, в черзі, які Ви хочете пропустити, '
                             'або ж не вказувати нічого для пропускання одного студента'
                             '\n\n👉 Наприклад: /skip або /skip 3')
        return

    arguments = ''.join(arguments)
    if arguments:
        try:
            arguments = int(arguments)
        except ValueError:
            await message.answer('1️⃣  Аргумент повинен бути лише числом!')
            return
    else:
        arguments = 1
    to_skip = arguments

    get_queue_id = f"""SELECT id_queue
                      FROM `{group_id}`.queues
                      JOIN `{group_id}`.subjects sb
                          USING (subject_id)
                      WHERE sb.title = %s;"""
    db.my_cursor.execute(get_queue_id, (active_subject,))
    id_queue = db.my_cursor.fetchone()[0]

    check_sign_up = f"""SELECT position
                       FROM `{group_id}`.sign_ups
                       WHERE telegram_user_id = %s
                       AND id_queue = %s;"""
    db.my_cursor.execute(check_sign_up, (user_id, id_queue))
    position = db.my_cursor.fetchone()

    if not position:
        await message.answer('📜 Ви не записані в активну чергу, щоб пропускати когось')
        return

    position = position[0]
    if position >= active_student:  # пофіксити баг з пропуском при перезаписі
        queue = fetch_queue(group_id, get_subject_id(group_id))
        positions = tuple(map(lambda x: x[0], queue))

        position_index = 0
        for index, k in enumerate(positions):
            if k == position:
                position_index = index

        index_to_jump_to = position_index + to_skip
        if index_to_jump_to <= positions.index(positions[-1]):
            range_of_indeces = slice(position_index+1, index_to_jump_to+1)
        else:
            await message.answer('🔚 Неможливо пропустити більше студентів, '
                                 f'ніж записано в черзі після студента {user_name}')
            return

        delete_sign_up = f"""DELETE FROM `{group_id}`.sign_ups
                             WHERE id_queue = {id_queue} AND position = {position};"""
        try:
            db.my_cursor.execute(delete_sign_up)
        except mysql.connector.DatabaseError:
            await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /skip')
            return
        else:
            db.mydb.commit()

        move_sign_ups = f"""UPDATE `{group_id}`.sign_ups
                           SET position = position - 1
                           WHERE id_queue = {id_queue} AND position """  # (...)
        if len(positions[range_of_indeces]) == 1:
            move_sign_ups += f'= {positions[range_of_indeces][0]};'
        else:
            move_sign_ups += f'IN {positions[range_of_indeces]};'

        print(move_sign_ups)
        try:
            db.my_cursor.execute(move_sign_ups)
        except mysql.connector.DatabaseError:
            await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /skip')
            return
        else:
            db.mydb.commit()

        make_sign_up = f"""INSERT INTO `{group_id}`.sign_ups
                           VALUES (DEFAULT, {id_queue}, {user_id}, {positions[index_to_jump_to]});"""
        print(make_sign_up)
        try:
            db.my_cursor.execute(make_sign_up)
        except mysql.connector.DatabaseError:
            await message.answer('🔧 Виникла проблема із запитом до бази даних'
                                 '\n\nСпробувати ще раз: /skip <i>{кількість місць (за замовчуванням: 1)}</i>')
            return
        else:
            db.mydb.commit()

        if db.my_cursor.rowcount < 1:
            await message.answer('🔧 Виникла проблема із запитом до бази даних'
                                 '\n\nСпробувати ще раз: /skip <i>{кількість місць (за замовчуванням: 1)}</i>')
        else:
            if to_skip == 1:
                await message.answer(f'🔃 {user_name} пропустив(-ла) 1 студента')
            else:
                await message.answer(f'🔃 {user_name} пропустив(-ла) {to_skip} студентів')

            next_student = active_student + 1
            if active_student != positions[-1]:
                while next_student not in positions:
                    next_student += 1

            if next_student != active_student + 1 and position == active_student:
                await next(message)
            else:
                queue = fetch_queue(group_id, get_subject_id(group_id))  # повторний фетчинг черги (вже оновленої)
                await message.answer(active_queue_to_str(queue, False, active_student, next_student))
    else:
        await message.answer('🙄 Ви вже здали!')
    return


@dp.message_handler(commands='show_current_student')
async def show_current_student(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    await message.answer(get_sign_up(group_id))


@dp.message_handler(commands='all_teachers')
async def all_teachers(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    teachers = get_teachers_with_all_info(group_id)
    teachers_lists = []
    for teacher in teachers:
        teacher_id = get_teacher_id(group_id, teacher[1])

        sql = f"""SELECT title FROM `{group_id}`.subjects
                  WHERE id_teacher = {teacher_id};"""
        db.my_cursor.execute(sql)
        temp = db.my_cursor.fetchall()

        teacher_subjects = []
        for subject in temp:
            teacher_subjects.append(subject[0])
        teacher_subjects = ', '.join(teacher_subjects)

        lst_teacher = list(teacher)
        lst_teacher.append(teacher_subjects)
        teachers_lists.append(lst_teacher)

    if teachers:
        all_teachers_str = '👩‍🏫 Список усіх викладачів:\n'
        for i, name, username, phone, email, info, subjects in teachers_lists:
            username = username if username else '(немає)'
            phone = phone if phone else '(немає)'
            email = email if email else '(немає)'
            info = info if info else '</i>(немає)<i>'
            subjects = subjects if subjects else '(нічого)'
            teacher_str = f'\n<b>{i}. {name}</b>\n' \
                          f'  💬  {username}\n' \
                          f'  📱  {phone}\n' \
                          f'  ✉  {email}\n' \
                          f'  📕  {subjects}\n' \
                          f'  ℹ  <i>{info}</i>\n'

            str_len = len(all_teachers_str) + len(teacher_str)
            if str_len > 4096:
                await message.answer(all_teachers_str)
                all_teachers_str = teacher_str
            else:
                all_teachers_str += teacher_str
    else:
        all_teachers_str = '🫥 Список викладачів порожній\n'

    add_teacher_hint = '\nДодати викладача: /add_teacher'
    if len(all_teachers_str) + len(add_teacher_hint) < 4096:
        all_teachers_str += add_teacher_hint
        await message.answer(all_teachers_str)
    else:
        await message.answer(all_teachers_str)
        await message.answer(add_teacher_hint)
    return


@dp.message_handler(commands='all_subjects')
async def all_subjects(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    query = f"""SELECT subjects.title, teachers.name
               FROM `{group_id}`.subjects
               LEFT OUTER JOIN `{group_id}`.teachers
                   USING (id_teacher)
               ORDER BY subject_id;"""
    db.my_cursor.execute(query)
    subjects = db.my_cursor.fetchall()

    all_subjects_str = '📚 Список усіх предметів:\n'
    if subjects:
        for i, (title, teacher_name) in enumerate(subjects):
            all_subjects_str += f'\n{i + 1}. {title}\nВикладає: {teacher_name}\n'
    else:
        all_subjects_str += '🫥 Список предметів порожній\n'
    all_subjects_str += '\nДодати предмет: /add_subject'

    await message.answer(all_subjects_str)
    return


@dp.message_handler(commands='all_students')
async def all_students(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    query = f"""SELECT username, firstname FROM `{group_id}`.students
               ORDER BY firstname;"""
    db.my_cursor.execute(query)
    students = db.my_cursor.fetchall()

    all_students_str = '🧑‍🎓 Список усіх зареєстрованих студентів:\n\n'
    if students:
        for i, (username, firstname) in enumerate(students):
            all_students_str += f'{i + 1}. {firstname} ({username})\n'
    else:
        all_students_str += '🫥 Список зареєстрованих студентів порожній\n'

    await message.answer(all_students_str)
    return


@dp.message_handler(commands='set_max')
async def set_max(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    arguments = message.get_args()

    try:
        number = int(arguments)
    except ValueError:
        await message.answer('1️⃣ Щоб виставити максимальну довжину черги необхідно вказати число, більше за нуль'
                             '\n👉 Наприклад, /set_max 30')
        return

    if number < 1 or number > 500:
        await message.answer('☝ Мінімальна довжина черги - 1 студент, а максимальна - 500 студентів'
                             '\n\nСпробувати задати довжину ще раз: /set_max <i>{затребувана довжина черги}</i>')
        return

    db.my_cursor.execute(f'UPDATE `{group_id}`.system_settings SET `max_in_queue` = {number};')
    db.mydb.commit()

    await message.answer(f'🔄 Максимальна довжина черги тепер {number}')
    return


def get_first_free_pos(group_id, positions):
    db.my_cursor.execute(f'SELECT `active_student`, `max_in_queue` FROM `{group_id}`.system_settings;')
    fetched = db.my_cursor.fetchone()
    active_student = fetched[0]
    max_in_queue = fetched[1]

    if not positions:
        return 1
    for i in range(active_student, max_in_queue):  # зробити адаптивним максимальну кількість
        if i and i not in positions:
            return i

    return None


@dp.message_handler(commands='sign_up')
async def sign_up(message: types.Message):
    group_id = str(message.chat.id)
    db.my_cursor.execute(f'SELECT `active_student`, `max_in_queue` FROM `{group_id}`.system_settings;')
    fetched = db.my_cursor.fetchone()
    active_student = fetched[0]
    max_in_queue = fetched[1]

    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return
    user = message.from_user
    add_user(user, group_id)
    user_id = user.id
    user_name = user.first_name

    arguments = message.get_args().split(' ')

    if not arguments:
        await message.answer('🗿 Ви не ввели аргументи!'
                             '\n\n☝ Необхідно вказати назву або номер предмету, в чергу на який хочете записатися'
                             '\n\n💁 За бажанням також можна вказати конкретну позицію в черзі, якщо вона вільна'
                             '\n\n👉 Наприклад: /sign_up Математика або /sign_up Математика 5')
        return
    if arguments[0] == '':
        await message.answer('🗿 Ви не ввели аргументи!'
                             '\n\n☝ Необхідно вказати назву або номер предмету, в чергу на який хочете записатися'
                             '\n\n💁 За бажанням також можна вказати конкретну позицію в черзі, якщо вона вільна'
                             '\n\n👉 Наприклад: /sign_up Математика або /sign_up Математика 5')
        return

    if len(arguments) >= 2:
        try:
            position = int(arguments[-1])
        except ValueError:
            position = None
        else:
            del arguments[-1]
        subject_input = ' '.join(arguments)
    else:  # if len(arguments) == 1:
        position = None
        subject_input = arguments[0]

    subjects = get_subjects(group_id)
    sub_with_queue = get_subjects_with_queues(group_id)

    try:
        subject_number = int(subject_input)
    except ValueError:
        subject = subject_input
    else:
        if 0 < subject_number <= len(subjects):
            subject = subjects[subject_number - 1]
        else:
            await message.answer(f'❓ Предмет за номером {subject_number} невідомий\n\nДодати предмет: /add_subject')
            return

    if subject not in subjects:
        await message.answer(f'❓ Предмет {subject} невідомий\n\nДодати предмет: /add_subject')
        return

    if subject not in sub_with_queue:
        await message.answer(f'🫥 Предмет {subject} не має черги\n\nСтворити чергу: /create_queue')
        return

    check_stundent = f"""SELECT su.position
                        FROM `{group_id}`.sign_ups su
                        JOIN `{group_id}`.students st
                            USING (telegram_user_id)
                        JOIN `{group_id}`.queues qu
                            USING (id_queue)
                        JOIN `{group_id}`.subjects sb
                            USING (subject_id)
                        WHERE st.telegram_user_id = %s and sb.title = %s"""
    db.my_cursor.execute(check_stundent, (user_id, subject))
    exist_pos = db.my_cursor.fetchall()
    exist_pos = tuple(map(lambda x: x[0], exist_pos))

    if exist_pos:
        max_pos = max(exist_pos)
    else:
        max_pos = 0

    if max_pos > active_student:
        await message.answer(f'📃 {user_name} вже записаний(-а) в цю чергу на місце {exist_pos[0]}'
                             f'\n\n☝ Щоб перезаписатися на інше місце, спочатку випишіться з черги, '
                             f'а тоді запишіться заново'
                             '\n\nВиписатися з черги: /sign_out <i>{номер або назва предмету}</i>')
        return

    if not position:  # Випадок, коли юзер вказав лише назву предмету. Записуємо на перше вільне місце
        get_all_from_queue = f"""SELECT position
                                FROM `{group_id}`.sign_ups
                                JOIN `{group_id}`.queues
                                    USING (id_queue)
                                JOIN `{group_id}`.subjects sb
                                    USING (subject_id)
                                WHERE sb.title = %s"""
        db.my_cursor.execute(get_all_from_queue, (subject,))
        positions = db.my_cursor.fetchall()
        positions = tuple(map(lambda x: x[0], positions))
        position = get_first_free_pos(group_id, positions)

        if not position:
            await message.answer('🙆‍♀ Черга заповнена'
                                 '\n\n☝ Можна змінити максимальну кількість студентів у черзі в налаштуваннях')
            return

    else:  # Випадок, коли юзер вказав назву предмету та конкретне місце в черзі
        # try:
        #     position = int(arguments[1])
        # except ValueError:
        #     await message.answer('🗿 Ви неправильно вказуєте номер у черзі'
        #                          '\n\n☝ Необхідно вказати назву або номер предмету та бажаний номер у черзі,'
        #                          'в чергу якого бажаєте записатися'
        #                          '\n\n👉 Наприклад: /sign_up Математика 5')
        #     return

        if position < 0 or position > max_in_queue:
            await message.answer(f'🙆‍♀ Максимальний номер у черзі: {max_in_queue}')
            return

        if position <= active_student:
            await message.answer(f'🏃‍♂ Черга вже пройшла місце {position}. '
                                 f'Зараз здає студент на позиції {active_student}\n\n'
                                 f'⤵ Запишіться на місце попереду!')
            return

        # Перевірка, чи є вже на цьому місці записаний студент
        check_student_by_pos = f"""SELECT st.firstname
                                   FROM `{group_id}`.sign_ups su
                                   JOIN `{group_id}`.students st
                                       USING (telegram_user_id)
                                   JOIN `{group_id}`.queues qu
                                       USING (id_queue)
                                   JOIN `{group_id}`.subjects sb
                                       USING (subject_id)
                                   WHERE su.position = %s and sb.title = %s"""

        db.my_cursor.execute(check_student_by_pos, (position, subject))
        name_of_student = db.my_cursor.fetchone()

        if name_of_student:
            await message.answer(f'😔 На цю позицію вже записаний(-а) {name_of_student[0]}')
            return

    get_id_queue = f"""SELECT id_queue
                      FROM `{group_id}`.queues
                      JOIN `{group_id}`.subjects sb
                        USING (subject_id)
                      WHERE sb.title = %s"""
    db.my_cursor.execute(get_id_queue, (subject,))
    id_queue = db.my_cursor.fetchone()[0]

    sign_up_student = f"""INSERT INTO `{group_id}`.sign_ups
                         VALUES(DEFAULT, %s, %s, %s)"""
    try:
        db.my_cursor.execute(sign_up_student, (id_queue, user_id, position))
    except mysql.connector.DatabaseError:
        await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /sign_up')
        return
    else:
        db.mydb.commit()

    await message.answer(f'✍ {user_name} було успішно записано в чергу на {subject} під номером {position}')
    return


@dp.message_handler(commands='sign_out')
async def sign_out(message: types.Message):
    group_id = str(message.chat.id)
    if not check_database(message):
        await message.answer('👉 Бот для цієї групи ще не активний. Запустіть його командою /start')
        return

    user = message.from_user
    add_user(user, group_id)
    user_id = user.id
    user_name = user.first_name

    data = message.get_args()
    if not data:
        await message.answer('🗿 Ви неправильно вводите команду'
                             '\n\n☝ Необхідно вказати назву або номер предмету, чергу на який Ви хочете покинути'
                             '\n\n👉 Наприклад /sign_out Математика')
        return

    subjects = get_subjects(group_id)
    sub_with_queue = get_subjects_with_queues(group_id)

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

            get_queue_id = f"""SELECT id_queue 
                              FROM `{group_id}`.queues 
                              JOIN `{group_id}`.subjects sb
                                  USING (subject_id)
                              WHERE sb.title = %s"""
            db.my_cursor.execute(get_queue_id, (subject,))
            id_queue = db.my_cursor.fetchone()[0]

            check_sign_up = f"""SELECT position
                               FROM `{group_id}`.sign_ups
                               WHERE telegram_user_id = %s
                               AND id_queue = %s;"""
            db.my_cursor.execute(check_sign_up, (user_id, id_queue))
            position = db.my_cursor.fetchone()

            if position:
                position = position[0]

                delete_sign_up = f"""DELETE FROM `{group_id}`.sign_ups
                                     WHERE id_queue = {id_queue} AND position = {position};"""
                try:
                    db.my_cursor.execute(delete_sign_up)
                except mysql.connector.DatabaseError:
                    await message.answer('🔧 Виникла проблема із запитом до бази даних\n\nСпробувати ще раз: /sign_out')
                    return
                else:
                    db.mydb.commit()

                await message.answer(f'❌ {user_name} було успішно видалено з черги')
            else:
                await message.answer(f'👌🏼 Ви і так не були записані в чергу на {subject}')
        else:
            await message.answer(f'🫥 До предмету {subject} ще не створена черга'
                                 f'\n\nСтворити чергу: /create_queue')
    else:
        await message.answer(f'❓ Предмет {subject} невідомий'
                             f'\n\nДодати предмет: /add_subject')
    return


def check_database(message: types.Message):
    group_id = str(message.chat.id)
    query = f'SELECT * FROM `{group_id}`.`System_settings`;'
    try:
        db.my_cursor.execute(query)
    except mysql.connector.ProgrammingError:  # якщо бази даних не існує
        return False
    else:
        db.my_cursor.fetchall()  # все одно фетчимо, щоб не отримати помилку unread result found, але ніде не зберігаємо
        return True


@dp.message_handler(commands='start')
async def start(message: types.Message):
    group_id = str(message.chat.id)

    print(group_id)  # тимчасово (технічно)

    is_group = True if group_id[0] == '-' else False
    if not is_group:
        await message.answer(f"😊 {message.from_user.first_name}, я працюю лише в групах. Додай мене в групу")
        return

    if not check_database(message):
        try:
            db.start_settings()
            db.create_database(group_id)
            db.create_tables(group_id)
            db.end_settings()
        except Exception as error:
            print('Cause: {}'.format(error))
        else:
            await message.answer(f"🫡 Розпочинаю роботу в групі {message.chat.title}")

        print(f'\nAll tables for group \033[4m{message.chat.title}\033[0m\033[92m are ready')
        print(f'\n\033[1mBOT STARTED FOR GROUP \033[4m{message.chat.title}\n\033[0m')
    else:
        await message.answer(f"😉 Я вже працюю в цій групі. Можна користуватися мною")
    return

if __name__ == '__main__':
    try:
        print('\033[93mInitializing database server...\n')
        db.connect_to_server()
        print('\033[92mSuccessfully connected to the database server\n')

        executor.start_polling(dp, skip_updates=True)
    except Exception as error:
        print('Cause: {}'.format(error))
