from connect import *
from telebot import *
import datetime
import random
import pandas as pd


def compilation_of_statistics(callback):

    config = load_config()
    connection = psycopg2.connect(**config)
    cursor = connection.cursor()

    df = pd.read_sql_query("SELECT * FROM results WHERE user_id = %s AND correct IS NOT NULL", connection, params=(callback.from_user.id, ))
    df[['question_id', 'id_num']] = df['id'].str.split('_', expand=True)

    total_task_complete = int(df['correct'].count())
    cursor.execute("UPDATE statistics SET total_tasks_completed = %s WHERE user_id = %s", (total_task_complete, callback.from_user.id))
    connection.commit()

    df_true = int(df['correct'].sum())
    if total_task_complete > 0:
        correct_answers = int((df_true / total_task_complete) * 100)
    else:
        correct_answers = 0
    cursor.execute("UPDATE statistics SET correct_answers = %s WHERE user_id = %s", (correct_answers, callback.from_user.id))
    connection.commit()

    choise_question = df['question_id'].value_counts()
    favourite_question = int(choise_question.idxmax())
    unfavourity_question = int(choise_question.idxmin())
    cursor.execute("UPDATE statistics SET favourite_question = %s, unfavourite_question = %s WHERE user_id = %s", (favourite_question, unfavourity_question, callback.from_user.id))
    connection.commit()

    task_stats = df.groupby('question_id')['correct'].agg(['mean', 'count'])
    winning_question = int(task_stats['mean'].idxmax())
    losing_question = int(task_stats['mean'].idxmin())
    cursor.execute("UPDATE statistics SET winning_question= %s, losing_question = %s WHERE user_id = %s", (winning_question, losing_question, callback.from_user.id))

    connection.commit()
    cursor.close()
    connection.close()