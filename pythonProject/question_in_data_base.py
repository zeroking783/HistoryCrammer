import psycopg2
from connect import *
from questions_id import *

def questions_in_data_base_1(questions_id):

    question_id = questions_id["question"]
    items_list = list(questions_id.items())

    config = load_config()
    connection = psycopg2.connect(**config)
    cursor = connection.cursor()

    question_num = 1

    # Заполняю базу данных вопросами и ответами
    for key, value in items_list[1:]:
        id = str(question_id) + "_" + str(question_num)
        cursor.execute(
            f"INSERT INTO questions_1 (id, question, answer) VALUES (%s, %s, %s) ON CONFLICT (question) DO NOTHING;",
            (id, key, value))
        question_num += 1

    connection.commit()
    cursor.close()
    connection.close()


def question_in_data_base_2(questions_id):

    question_id = questions_id["question"]
    items_list = list(questions_id.items())

    config = load_config()
    connection = psycopg2.connect(**config)
    cursor = connection.cursor()

    question_num = 1

    for key, value in items_list[1:]:
        id = str(question_id) + "_" + str(question_num)
        cursor.execute(
            f"INSERT INTO questions_2 (id, question, answer) VALUES (%s, %s, %s) ON CONFLICT (question) DO NOTHING;",
            (id, key, value))
        question_num += 1

    connection.commit()
    cursor.close()
    connection.close()


def question_in_data_base_3(questions_id):

    question_id = questions_id["question"]
    items_list = list(questions_id.items())

    config = load_config()
    connection = psycopg2.connect(**config)
    cursor = connection.cursor()

    question_num = 1

    for key, value in items_list[1:]:
        id = str(question_id) + "_" + str(question_num)
        cursor.execute(
            f"INSERT INTO questions_3 (id, question, answer) VALUES (%s, %s, %s) ON CONFLICT (question) DO NOTHING;",
            (id, key, value))
        question_num += 1

    connection.commit()
    cursor.close()
    connection.close()

# questions_in_data_base_1(questions_1)
# question_in_data_base_2(questions_2)
question_in_data_base_3(questions_3)