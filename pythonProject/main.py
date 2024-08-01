from connect import *
from telebot import *
from telegram import ReplyKeyboardMarkup
from telebot import types
import datetime
import random
from statistics import *
import time


bot = telebot.TeleBot('***********************************************')

# Функция для генерации всех ответов на первое задание
def generate_all_answers_on_question_1(callback):

	# Подключение к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	# Массив в котором будут хранится все ответы
	answers = []

	# Добавляю в answers правильный ответ
	cursor.execute("SELECT answer_true FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1", (callback.from_user.id, ))
	answers.append(cursor.fetchone()[0])

	while len(answers) < 8:
		cursor.execute("SELECT answer FROM questions_1 ORDER BY RANDOM() LIMIT 1")
		res = cursor.fetchone()[0]
		if res not in answers:
			answers.append(res)
		else:
			continue

	random.shuffle(answers)

	cursor.execute("UPDATE results SET answer_all = %s WHERE user_id = %s AND "
				   "answer_num_all = (SELECT answer_num_all FROM results "
				   "WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)", (answers, callback.from_user.id, callback.from_user.id))

	# Закрываю соединение с базой
	connection.commit()
	cursor.close()
	connection.close()


def generate_all_answers_on_question_3(callback):

	# Подключение к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	# Массив в котором будут хранится все ответы
	answers = []

	# Добавляю в answers id правильного ответа
	cursor.execute("SELECT id FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1",
				   (callback.from_user.id, ))
	answer_true = cursor.fetchone()[0]
	answers.append(answer_true)
	connection.commit()

	while len(answers) < 4:
		cursor.execute("SELECT id FROM questions_3 ORDER BY RANDOM() LIMIT 1")
		res = cursor.fetchone()[0]
		if res not in answers:
			answers.append(res)
		else:
			continue

	random.shuffle(answers)

	# Здесь еще будет часть по добавлению правильного ответа
	position_true = answers.index(answer_true)

	cursor.execute("UPDATE results SET answer_true = %s, answer_all = %s WHERE user_id = %s AND "
				   "answer_num_all = (SELECT answer_num_all FROM results "
				   "WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)",
				   (position_true, answers, callback.from_user.id, callback.from_user.id))

	connection.commit()
	cursor.close()
	connection.close()


# Здесь просто приветствие и переход к главной менюшке от превью
@bot.message_handler(commands=['start'])
def send_welcome(message):

	# Здесь я сохраняю name пользователя и id
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	cursor.execute(
					"INSERT INTO users (user_id, username, user_state) VALUES (%s, %s, %s) ON CONFLICT (user_id)"
							" DO UPDATE SET username = EXCLUDED.username, user_state = EXCLUDED.user_state",
						(message.from_user.id, message.from_user.username, 'start')
					)

	cursor.execute("INSERT INTO statistics (user_id) VALUES (%s) ON CONFLICT (user_id)"
				   "DO UPDATE SET user_id = EXCLUDED.user_id", (message.from_user.id, ))

	connection.commit()
	cursor.close()
	connection.close()

	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	btn_menu = types.KeyboardButton('💬 Меню')
	markup.row(btn_menu)
	bot.delete_message(message.chat.id, message.message_id)
	bot.send_message(message.chat.id, 'Привет! Добро пожаловать в бота, который поможет тебе подготовиться к ЕГЭ по истории. \n \n'
									  'Нажми на кнопку «*💬 Меню*», чтобы вызвать панель со всеми функциями',
					 				  reply_markup=markup, parse_mode="Markdown")


# Здесь будет главное меню
@bot.message_handler(content_types=['text'])
def on_click(message):

	# Подключаемся к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	if message.text != '💬 Меню':
		bot.delete_message(message.chat.id, message.message_id)

	elif message.text == '💬 Меню':

		# Получаю состояние юзера
		cursor.execute("SELECT user_state FROM users WHERE user_id = %s", (message.from_user.id, ))
		user_state = cursor.fetchone()[0]

		current_date = datetime.datetime.now().strftime('%Y-%m-%d')
		current_time = datetime.datetime.now().strftime('%H:%M:%S')
		cursor.execute("UPDATE users SET user_state = %s, last_date_start_menu = %s, last_time_start_menu = %s, selected_questions = %s, selected_amount = %s WHERE user_id = %s",
				('menu', current_date, current_time, 0, 0, message.from_user.id))
		connection.commit()

		if 'menu' in user_state:
			bot.delete_message(message.chat.id, message.message_id)

		if 'start' in user_state:

			cursor.execute("UPDATE users SET last_menu_message_id = %s WHERE user_id = %s", (message.message_id, message.from_user.id))

			bot.delete_message(message.chat.id, message.message_id)

			# Генерация кнопок и удаление последнего сообщения
			markup = types.InlineKeyboardMarkup()
			btn_tests = types.InlineKeyboardButton('📝 Выполнять задания', callback_data='settings_tests')
			btn_profil = types.InlineKeyboardButton('👤 Статистика', callback_data='profil')
			btn_feedback = types.InlineKeyboardButton('🛎 Оставить отзыв/поддержка', callback_data='feedback')
			markup.row(btn_tests)
			markup.row(btn_profil)
			markup.row(btn_feedback)
			bot.send_message(message.chat.id, "*💬 Меню*", reply_markup=markup,
								  parse_mode="Markdown")

		if ('settings_test' in user_state) or ('profil' in user_state):

			bot.delete_message(message.chat.id, message.message_id)

			cursor.execute("SELECT last_menu_message_id FROM users WHERE user_id = %s", (message.from_user.id, ))
			message_id = cursor.fetchone()[0]

			# Генерация кнопок и удаление последнего сообщения
			markup = types.InlineKeyboardMarkup()
			btn_tests = types.InlineKeyboardButton('📝 Выполнять задания', callback_data='settings_tests')
			btn_profil = types.InlineKeyboardButton('👤 Мой профиль', callback_data='profil')
			btn_feedback = types.InlineKeyboardButton('🛎 Оставить отзыв/поддержка', callback_data='feedback')
			markup.row(btn_tests)
			markup.row(btn_profil)
			markup.row(btn_feedback)
			bot.edit_message_text("*💬 Меню*", message.chat.id, message_id+1, reply_markup=markup, parse_mode="Markdown")

	# Закрываем соединение с базой данных
	connection.commit()
	cursor.close()
	connection.close()


# ---- В ЭТОЙ ЧАСТИ ИДЕТ ОБРАБОТКА ПРОХОЖДЕНИЯ ТЕСТА ----
# -------------------------------------------------------------------------------

# Здесь меню с настройками тестов
@bot.callback_query_handler(func=lambda callback: callback.data == 'settings_tests')
def settings_tests(callback):


	# Подключаемся к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	# Изменяем состояние пользователя на settings_test
	cursor.execute("UPDATE users SET user_state = %s WHERE user_id = %s", ('settings_test', callback.from_user.id))

	# Генерация кнопок и удаление последнего сообщения
	markup = types.InlineKeyboardMarkup()
	btn_tasks = types.InlineKeyboardButton("Выбрать номер задания", callback_data='choise_questions')
	btn_amount = types.InlineKeyboardButton("Выбрать количество номеров", callback_data='choise_amount')
	btn_start_test = types.InlineKeyboardButton('Начать ➡️', callback_data='start_test')
	markup.row(btn_tasks)
	markup.row(btn_amount)
	markup.row(btn_start_test)

	# Получаю данные о заданиях пользователя
	cursor.execute("SELECT selected_questions FROM users WHERE user_id = %s", (callback.from_user.id, ))
	selected_questions = cursor.fetchone()[0]
	cursor.execute(f"SELECT selected_amount FROM users WHERE user_id = %s", (callback.from_user.id, ))
	selected_amount = cursor.fetchone()[0]

	# Отправляю сообщение к кнопкам с выбранными заданиями
	if selected_amount == 0 and selected_questions == 0:
		message_text = "⚙️ *Настройка теста* \n \nВыбери задание ЕГЭ 📝 \nВыбери количество заданий 🔢"
	elif selected_amount == -1 and selected_questions == 0:
		message_text = "⚙️ *Настройка теста* \n \nВыбери задание ЕГЭ 📝 \nВыбран бесконечный режим ✅"
	elif selected_amount != 0 and selected_amount != -1 and selected_questions == 0:
		message_text = f"⚙️ *Настройка теста* \n \nВыбери задание ЕГЭ 📝 \nКоличество заданий ЕГЭ - {selected_amount} ✅"
	elif selected_questions != 0 and selected_amount == 0:
		message_text = f"⚙️ *Настройка теста* \n \nВыбрано задание ЕГЭ - {selected_questions} ✅ \nВыбери количество заданий 🔢"
	elif selected_questions != 0 and selected_amount == -1:
		message_text = f"⚙️ *Настройка теста* \n \nВыбрано задание ЕГЭ - {selected_questions} ✅ \nВыбран бесконечный режим ✅"
	elif selected_questions != 0:
		message_text = f"⚙️ *Настройка теста* \n \nВыбрано задание ЕГЭ - {selected_questions} ✅ \nКоличество заданий ЕГЭ - {selected_amount} ✅"
	else:
		message_text = "⚙️ *Настройка теста* "

	bot.edit_message_text(message_text, callback.message.chat.id, callback.message.message_id, reply_markup=markup, parse_mode="Markdown")

	# Закрываем соединение с базой данных
	connection.commit()
	cursor.close()
	connection.close()


# Здесь я отправляю сообщение с выбором номера задания
@bot.callback_query_handler(func=lambda callback: callback.data == 'choise_questions')
def select_num_question(callback):

	# Здесь я отправляю сообщение с выбором задания
	markup = types.InlineKeyboardMarkup()
	btn_question_num_1 = types.InlineKeyboardButton("1 (даты 📅)", callback_data='btn_question_num_1')
	markup.row(btn_question_num_1)
	btn_question_num_3 = types.InlineKeyboardButton("3 (факт - явление 🔍)", callback_data='btn_question_num_3')
	markup.row(btn_question_num_3)
	btn_back = types.InlineKeyboardButton("⬅️ Вернуться назад", callback_data='come_back_to_settings_test')
	markup.row(btn_back)
	bot.edit_message_text("Выберите номер задания 📝", callback.message.chat.id, callback.message.message_id, reply_markup=markup)


# В этой части я обрабатываю разом каждый из возможных выбранных номеров заданий
@bot.callback_query_handler(func=lambda call: call.data.startswith('btn_question_num_'))
def btn_question_num_to_database(callback):

	callback_data = callback.data.split('_')

	# Подключаемся к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	cursor.execute("UPDATE users SET selected_questions = %s WHERE user_id = %s", (int(callback.data.split('_')[3]), callback.from_user.id))

	# Закрываем соединение с базой данных
	connection.commit()
	cursor.close()
	connection.close()

	settings_tests(callback)


# Здесь я отправляю сообщение с выбором количества вопросов
@bot.callback_query_handler(func=lambda callback: callback.data == 'choise_amount')
def select_choise_amount(callback):

	markup = types.InlineKeyboardMarkup()
	btn_choise_question_5 = types.InlineKeyboardButton("5", callback_data = "btn_choise_question_5")
	btn_choise_question_10 = types.InlineKeyboardButton("10", callback_data="btn_choise_question_10")
	btn_choise_question_20 = types.InlineKeyboardButton("20", callback_data="btn_choise_question_20")
	markup.row(btn_choise_question_5, btn_choise_question_10, btn_choise_question_20)
	btn_choise_question_infinity = types.InlineKeyboardButton("Бесконечный режим ♾️", callback_data="btn_choise_question_infinity")
	markup.row(btn_choise_question_infinity)
	btn_back = types.InlineKeyboardButton("⬅️ Вернуться назад", callback_data='come_back_to_settings_test')
	markup.row(btn_back)
	bot.edit_message_text("Выберите количество вопросов 🔢", callback.message.chat.id, callback.message.message_id, reply_markup=markup)


# Здесь я обрабатываю выбранное пользователем количество номеров
@bot.callback_query_handler(func=lambda callback: callback.data.startswith('btn_choise_question_'))
def btn_choise_question_to_database(callback):

	callback_data = callback.data.split('_')

	# Подключаемся к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	if callback_data[3] != 'infinity':
		bot.answer_callback_query(callback_query_id=callback.id,
								  text="Эта функция пока не работает, выберите бесконечный режим.",
								  show_alert=True)
		return

	if callback_data[3] == 'infinity':
		cursor.execute("UPDATE users SET selected_amount = %s WHERE user_id = %s", (-1, callback.from_user.id))
	else:
		cursor.execute("UPDATE users SET selected_amount = %s, mode = %s WHERE user_id = %s", (int(callback.data.split('_')[3]), 1, callback.from_user.id))

	# Закрываем соединение с базой данных
	connection.commit()
	cursor.close()
	connection.close()

	settings_tests(callback)


# Здесь заработает кнопка вернуться назад
@bot.callback_query_handler(func=lambda callback: callback.data == "come_back_to_settings_test")
def come_back_to_settings_test(callback):

	settings_tests(callback)


# Здесь я обрабатываю сам тест
@bot.callback_query_handler(func=lambda callback: callback.data == 'start_test')
def start_test(callback):

	# Подключаемся к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	cursor.execute("SELECT selected_questions, selected_amount FROM users WHERE user_id = %s", (callback.from_user.id, ))
	selected = cursor.fetchone()
	if selected[0] == 0 or selected[1] == 0:
		bot.answer_callback_query(callback_query_id=callback.id,
								  text="Перед началом теста выберите количество вопросов и номер задания из ЕГЭ.", show_alert=True)
		return


	current_date = datetime.datetime.now().strftime('%Y-%m-%d')
	current_time = datetime.datetime.now().strftime('%H:%M:%S')


	cursor.execute("UPDATE statistics SET last_date_start_test = %s, last_time_start_test = %s WHERE user_id = %s", (current_date, current_time, callback.from_user.id))
	connection.commit()

	cursor.execute("SELECT selected_questions FROM users WHERE user_id = %s", (callback.from_user.id, ))
	choise_question = cursor.fetchone()[0]
	connection.commit()

	if choise_question == 1:
		test_send_question_1(callback)
	if choise_question == 3:
		test_send_question_3(callback)



def test_send_question_1(callback):

	# Подключаемся к базе данных
	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	# Выбираю сам вопрос рандомно и сразу записываю его в results
	cursor.execute("SELECT id, question, answer FROM questions_1 ORDER BY RANDOM() LIMIT 1")
	answer = cursor.fetchone()
	cursor.execute("INSERT INTO results (user_id, id, answer_true) VALUES (%s, %s, %s)", (callback.from_user.id, answer[0], answer[2]))

	connection.commit()

	# Функция, которая добавит все остальные ответы в answer_all в рандомном порядке
	generate_all_answers_on_question_1(callback)

	# Создаю список всех ответов
	cursor.execute("SELECT answer_all FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1", (callback.from_user.id, ))
	answers = cursor.fetchone()[0].strip().strip('{}').split(',')

	markup = types.InlineKeyboardMarkup()
	btn_choise_res_answer_0 = types.InlineKeyboardButton(answers[0], callback_data="btn_choise_res_answer_0")
	btn_choise_res_answer_1 = types.InlineKeyboardButton(answers[1], callback_data="btn_choise_res_answer_1")
	btn_choise_res_answer_2 = types.InlineKeyboardButton(answers[2], callback_data="btn_choise_res_answer_2")
	btn_choise_res_answer_3 = types.InlineKeyboardButton(answers[3], callback_data="btn_choise_res_answer_3")
	markup.row(btn_choise_res_answer_0, btn_choise_res_answer_1, btn_choise_res_answer_2, btn_choise_res_answer_3)
	btn_choise_res_answer_4 = types.InlineKeyboardButton(answers[4], callback_data="btn_choise_res_answer_4")
	btn_choise_res_answer_5 = types.InlineKeyboardButton(answers[5], callback_data="btn_choise_res_answer_5")
	btn_choise_res_answer_6 = types.InlineKeyboardButton(answers[6], callback_data="btn_choise_res_answer_6")
	btn_choise_res_answer_7 = types.InlineKeyboardButton(answers[7], callback_data="btn_choise_res_answer_7")
	markup.row(btn_choise_res_answer_4, btn_choise_res_answer_5, btn_choise_res_answer_6, btn_choise_res_answer_7)
	bot.edit_message_text(answer[1], callback.message.chat.id, callback.message.message_id, reply_markup=markup)

	connection.commit()
	cursor.close()
	connection.close()

def test_send_question_3(callback):

	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	cursor.execute("SELECT id, question, answer FROM questions_3 ORDER BY RANDOM() LIMIT 1")
	answer = cursor.fetchone()
	cursor.execute("INSERT INTO results (user_id, id) VALUES (%s, %s)",
				   (callback.from_user.id, answer[0]))
	connection.commit()

	generate_all_answers_on_question_3(callback)

	# Создаю список всех ответов
	cursor.execute("SELECT answer_all FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1", (callback.from_user.id, ))
	answers = cursor.fetchone()[0].strip().strip('{}').split(',')

	# Представляю в строковом формате явления
	cursor.execute("SELECT answer FROM questions_3 WHERE id = %s", (answers[0], ))
	phenomenon_1 = cursor.fetchone()[0]
	cursor.execute("SELECT answer FROM questions_3 WHERE id = %s", (answers[1],))
	phenomenon_2 = cursor.fetchone()[0]
	cursor.execute("SELECT answer FROM questions_3 WHERE id = %s", (answers[2],))
	phenomenon_3 = cursor.fetchone()[0]
	cursor.execute("SELECT answer FROM questions_3 WHERE id = %s", (answers[3],))
	phenomenon_4 = cursor.fetchone()[0]

	cursor.execute("SELECT question FROM questions_3 WHERE id = (SELECT id FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)", (callback.from_user.id, ))
	fact = cursor.fetchone()[0]

	markup = types.InlineKeyboardMarkup()
	btn_choise_res_answer_0 = types.InlineKeyboardButton("1️⃣", callback_data="btn_choise_res_answer_0")
	btn_choise_res_answer_1 = types.InlineKeyboardButton("2️⃣", callback_data="btn_choise_res_answer_1")
	btn_choise_res_answer_2 = types.InlineKeyboardButton("3️⃣", callback_data="btn_choise_res_answer_2")
	btn_choise_res_answer_3 = types.InlineKeyboardButton("4️⃣", callback_data="btn_choise_res_answer_3")
	markup.row(btn_choise_res_answer_0, btn_choise_res_answer_1, btn_choise_res_answer_2, btn_choise_res_answer_3)
	bot.edit_message_text("ФАКТ\n" + fact + "\n"
						  "ЯВЛЕНИЯ \n" +
						  "1. " + phenomenon_1 + "\n"
						  "2. " + phenomenon_2 + "\n"
						  "3. " + phenomenon_3 + "\n"
						  "4. " + phenomenon_4 + "\n",
						  callback.message.chat.id, callback.message.message_id, reply_markup=markup)

	connection.commit()
	cursor.close()
	connection.close()



@bot.callback_query_handler(func=lambda callback: callback.data.startswith('btn_choise_res_answer_'))
def result_answer_in_test(callback):

	# Разделяем collback_data вопроса на части по _
	callback_data = callback.data.split('_')
	num_choise = int(callback_data[-1])

	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	cursor.execute("SELECT answer_true, answer_all FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1",(callback.from_user.id, ))
	true_plus_all_answers = cursor.fetchone()
	true = true_plus_all_answers[0]
	all_answers = true_plus_all_answers[1].strip().strip('{}').split(',')

	cursor.execute("SELECT selected_questions FROM users WHERE user_id = %s", (callback.from_user.id, ))
	selected_question = cursor.fetchone()[0]

	if selected_question == 1:
		if true == all_answers[num_choise]:

			cursor.execute("UPDATE results SET correct = %s WHERE user_id = %s AND "
						   "answer_num_all = (SELECT answer_num_all FROM results "
						   "WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)",(True, callback.from_user.id, callback.from_user.id))
			connection.commit()

			markup = types.InlineKeyboardMarkup()
			next_question = types.InlineKeyboardButton("Дальше ➡️", callback_data="next_question")
			markup.row(next_question)
			exit_tests = types.InlineKeyboardButton("Закончить ⬅️", callback_data="settings_tests")
			markup.row(exit_tests)
			bot.edit_message_text('Правильно! ✅', callback.message.chat.id, callback.message.message_id, reply_markup=markup)
		else:

			cursor.execute("UPDATE results SET correct = %s WHERE user_id = %s AND "
						   "answer_num_all = (SELECT answer_num_all FROM results "
						   "WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)",
						   (False, callback.from_user.id, callback.from_user.id))
			cursor.execute("SELECT question FROM questions_1 WHERE id = (SELECT id FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)", (callback.from_user.id, ))
			question = cursor.fetchone()[0]
			connection.commit()


			markup = types.InlineKeyboardMarkup()
			next_question = types.InlineKeyboardButton("Дальше ➡️", callback_data="next_question")
			markup.row(next_question)
			exit_tests = types.InlineKeyboardButton("Закончить ⬅️", callback_data="settings_tests")
			markup.row(exit_tests)
			bot.edit_message_text('Ошибка ❌ \n' + question + '\nПравильный ответ - ' + true, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

	if selected_question == 3:
		if int(true) == int(num_choise):

			cursor.execute("UPDATE results SET correct = %s WHERE user_id = %s AND "
						   "answer_num_all = (SELECT answer_num_all FROM results "
						   "WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)",
						   (True, callback.from_user.id, callback.from_user.id))
			connection.commit()

			markup = types.InlineKeyboardMarkup()
			next_question = types.InlineKeyboardButton("Дальше ➡️", callback_data="next_question")
			markup.row(next_question)
			exit_tests = types.InlineKeyboardButton("Закончить ⬅️", callback_data="settings_tests")
			markup.row(exit_tests)
			bot.edit_message_text('Правильно! ✅', callback.message.chat.id, callback.message.message_id,
								  reply_markup=markup)

		else:

			cursor.execute("UPDATE results SET correct = %s WHERE user_id = %s AND "
						   "answer_num_all = (SELECT answer_num_all FROM results "
						   "WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)",
						   (False, callback.from_user.id, callback.from_user.id))
			cursor.execute(
				"SELECT question FROM questions_3 WHERE id = (SELECT id FROM results WHERE user_id = %s ORDER BY answer_num_all DESC LIMIT 1)",
				(callback.from_user.id,))
			question = cursor.fetchone()[0]
			cursor.execute("SELECT answer FROM questions_3 WHERE id = %s", (all_answers[int(true)], ))
			true_answer = cursor.fetchone()[0]
			connection.commit()

			markup = types.InlineKeyboardMarkup()
			next_question = types.InlineKeyboardButton("Дальше ➡️", callback_data="next_question")
			markup.row(next_question)
			exit_tests = types.InlineKeyboardButton("Закончить ⬅️", callback_data="settings_tests")
			markup.row(exit_tests)
			bot.edit_message_text('Ошибка ❌ \n' + question + '\nПравильный ответ - ' + true_answer, callback.message.chat.id,
								  callback.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'next_question')
def next_question(callback):

	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	cursor.execute("SELECT selected_questions FROM users WHERE user_id = %s", (callback.from_user.id, ))
	selected_question = cursor.fetchone()[0]
	if selected_question == 1:
		test_send_question_1(callback)
	if selected_question == 3:
		test_send_question_3(callback)

	connection.commit()
	cursor.close()
	connection.close()

# -------------------------------------------------------------------


# ---- В ЭТОЙ ЧАСТИ БУДЕТ ОБРАБОТКА ПРОФИЛЯ ----
# -------------------------------------------------------------------

@bot.callback_query_handler(func=lambda callback: callback.data == 'profil')
def choise_profil_in_menu(callback):

	config = load_config()
	connection = psycopg2.connect(**config)
	cursor = connection.cursor()

	cursor.execute("SELECT COUNT(*) FROM results WHERE user_id = %s", (callback.from_user.id, ))
	if cursor.fetchone()[0] == 0:
		bot.answer_callback_query(callback_query_id=callback.id,
								  text="Для вывода статистики нужно ответить хотя бы на 1 вопрос.",
								  show_alert=True)
		return

	# Здесь я обнавляю состояние пользователя
	cursor.execute("UPDATE users SET user_state = %s WHERE user_id = %s", ("profil", callback.from_user.id))
	connection.commit()

	compilation_of_statistics(callback)

	cursor.execute("SELECT * FROM statistics WHERE user_id = %s", (callback.from_user.id, ))
	profil_data_message = cursor.fetchone()

	bot.edit_message_text("*👤 Профиль* \n \n"
						  "Ты уже сделал " + str(profil_data_message[1]) + " заданий \n" +
						  str(profil_data_message[2]) + ("% заданий ты делаешь правильно\n"
						  "Последений раз ты выполнял тест " + str(profil_data_message[3]) + " в " + str(profil_data_message[4]) + "\n"
						  "Твой любимый вопрос " + str(profil_data_message[5]) + "\n"
						  "Твой нелюбимый вопрос " + str(profil_data_message[6]) + "\n"
						  "Вопрос, в котором ты всегда уверен " + str(profil_data_message[7]) + "\n"
						  "Вопрос, в котором ты делаешь больше всего ошибок " + str(profil_data_message[8]) + "\n"),
						  callback.message.chat.id, callback.message.message_id, parse_mode="Markdown")

	connection.commit()
	cursor.close()
	connection.close()



@bot.callback_query_handler(func=lambda callback: callback.data == 'feedback')
def feedback_not_work_yet(callback):

	bot.answer_callback_query(callback_query_id=callback.id,
							  text="Эта функция пока в разработке.",
							  show_alert=True)


bot.polling()
