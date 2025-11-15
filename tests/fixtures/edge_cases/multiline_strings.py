"""File with complex multiline string content."""

from airflow import DAG

# Multiline documentation
dag = DAG(
    'multiline_test',
    doc_md="""
    # Multi-line DAG Documentation

    This is a comprehensive documentation
    that spans multiple lines and includes:

    - Bullet points
    - **Bold text**
    - *Italic text*
    - Code: `variable = value`

    ## Section 2

    More content here with enough text
    to satisfy the minimum length requirement.

    '''
    Triple quotes inside triple quotes
    '''

    And some more text at the end.
    """
)

# Complex string with code-like content
query = """
SELECT *
FROM table
WHERE column = 'value'
  AND other_column IN (
    SELECT id FROM other_table
  )
"""

# Python code in string (should not be analyzed)
code_string = """
import pandas as pd
import psycopg2

conn = psycopg2.connect(host='localhost')
"""

# Multiline f-string
message = f"""
This is a multiline f-string
with {query} embedded
"""

# Raw multiline string
pattern = r"""
    \d+     # Match digits
    [a-z]*  # Match letters
    \s+     # Match whitespace
"""
