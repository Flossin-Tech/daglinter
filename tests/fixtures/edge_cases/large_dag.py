"""Large DAG file for performance testing."""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# Large file with many lines for performance testing

dag = DAG(
    'large_performance_test',
    doc_md='Performance test DAG with many tasks and operations',
    start_date=datetime(2024, 1, 1),
)

# Generate 100 tasks
def task_function_0():
    """Task 0."""
    return "result_0"

def task_function_1():
    """Task 1."""
    return "result_1"

def task_function_2():
    """Task 2."""
    return "result_2"

def task_function_3():
    """Task 3."""
    return "result_3"

def task_function_4():
    """Task 4."""
    return "result_4"

def task_function_5():
    """Task 5."""
    return "result_5"

def task_function_6():
    """Task 6."""
    return "result_6"

def task_function_7():
    """Task 7."""
    return "result_7"

def task_function_8():
    """Task 8."""
    return "result_8"

def task_function_9():
    """Task 9."""
    return "result_9"

# Additional comments to increase file size
# """ + "\n# Comment line\n" * 900 + """

# More task definitions...
task_0 = PythonOperator(task_id='task_0', python_callable=task_function_0, dag=dag)
task_1 = PythonOperator(task_id='task_1', python_callable=task_function_1, dag=dag)
task_2 = PythonOperator(task_id='task_2', python_callable=task_function_2, dag=dag)
task_3 = PythonOperator(task_id='task_3', python_callable=task_function_3, dag=dag)
task_4 = PythonOperator(task_id='task_4', python_callable=task_function_4, dag=dag)
task_5 = PythonOperator(task_id='task_5', python_callable=task_function_5, dag=dag)
task_6 = PythonOperator(task_id='task_6', python_callable=task_function_6, dag=dag)
task_7 = PythonOperator(task_id='task_7', python_callable=task_function_7, dag=dag)
task_8 = PythonOperator(task_id='task_8', python_callable=task_function_8, dag=dag)
task_9 = PythonOperator(task_id='task_9', python_callable=task_function_9, dag=dag)

# Dependencies
task_0 >> task_1 >> task_2 >> task_3 >> task_4
task_5 >> task_6 >> task_7 >> task_8 >> task_9
