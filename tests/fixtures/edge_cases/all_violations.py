"""File that triggers all 4 linting rules."""

# DL001: Heavy imports at module level
import pandas as pd
import numpy as np
import tensorflow as tf

# DL002: Database connections at module level
import psycopg2
import pymongo
from sqlalchemy import create_engine

conn = psycopg2.connect(host='localhost', database='test')
client = pymongo.MongoClient('mongodb://localhost:27017/')
engine = create_engine('postgresql://localhost/mydb')

from airflow import DAG
from airflow.operators.python import PythonOperator

# DL003: Missing documentation (or inadequate)
dag = DAG('all_violations_dag')

# DL004: Complex dependencies
task1 = PythonOperator(task_id='task1', python_callable=lambda: None, dag=dag)
task2 = PythonOperator(task_id='task2', python_callable=lambda: None, dag=dag)
task3 = PythonOperator(task_id='task3', python_callable=lambda: None, dag=dag)
task4 = PythonOperator(task_id='task4', python_callable=lambda: None, dag=dag)
task5 = PythonOperator(task_id='task5', python_callable=lambda: None, dag=dag)
task6 = PythonOperator(task_id='task6', python_callable=lambda: None, dag=dag)
task7 = PythonOperator(task_id='task7', python_callable=lambda: None, dag=dag)
task8 = PythonOperator(task_id='task8', python_callable=lambda: None, dag=dag)
task9 = PythonOperator(task_id='task9', python_callable=lambda: None, dag=dag)
task10 = PythonOperator(task_id='task10', python_callable=lambda: None, dag=dag)
task11 = PythonOperator(task_id='task11', python_callable=lambda: None, dag=dag)
task12 = PythonOperator(task_id='task12', python_callable=lambda: None, dag=dag)

# Excessive fan-out
task1 >> [task2, task3, task4, task5, task6, task7, task8, task9, task10, task11, task12]
