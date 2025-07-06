from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
import re

db = SQLDatabase.from_uri("sqlite:///coinmarketcap.sqlite")
schema = db.get_table_info()

llm = ChatOpenAI(temperature=0, model="gpt-4o")  # or "gpt-4" or "gpt-3.5-turbo"


def strict_sql_generator(question: str) -> str:
    """
    Generate a valid SQL query from a natural language question using an LLM.

    This function uses the current database schema and a language model (ChatOpenAI)
    to translate a user-provided natural language question into a syntactically correct
    SQL query. It strictly enforces that the generated SQL must only use tables and
    columns present in the provided schema and must not include any explanations,
    comments, or markdown formatting.

    Args:
        question (str): The natural language question to translate into SQL.

    Returns:
        str: A raw SQL query as a plain string.
    """
    llm = ChatOpenAI(temperature=0)
    prompt = (
        "You are a SQL expert.\n"
        "Use only the following database schema to answer the question.\n\n"
        f"{schema}\n\n"
        "Translate the question into a valid SQL query.\n"
        "Do NOT make up tables or columns.\n"
        "Return ONLY the SQL query. Do NOT wrap it in markdown or provide explanation.\n\n"
        f"Question: {question}\nSQL:"
    )
    return llm.predict(prompt)


def fix_invalid_sql(sql: str, error_msg: str) -> str:
    """
    Attempts to fix an invalid SQL query by prompting a language model with the error context.

    Given a faulty SQL statement and the associated error message, this function uses an LLM
    (e.g., ChatOpenAI) to suggest a corrected version of the query. The prompt instructs the model
    to return only the fixed SQL query, with no additional explanation or formatting.

    Args:
        sql (str): The original, invalid SQL query.
        error_msg (str): The error message generated when the SQL was executed.

    Returns:
        str: A corrected SQL query as a plain string.
    """
    prompt = (
        f"This SQL caused an error: `{sql}`\n"
        f"Error: {error_msg}\n"
        f"Fix the SQL and return only the corrected query."
    )
    return llm.predict(prompt)


def extract_sql_from_response(text):
    """
    Extracts a raw SQL query from a text response, typically returned by a language model.

    This function searches for SQL code enclosed in markdown-style triple backticks (e.g., ```sql ... ```)
    and extracts the SQL statement. If no code block is found, it returns the entire input text stripped
    of leading and trailing whitespace.

    Args:
        text (str): The text response potentially containing SQL inside a markdown code block.

    Returns:
        str: The extracted SQL query, or the plain text if no code block is found.
    """
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def extract_tables_from_sql(sql_query):
    """
    Extracts table names used in a SQL query.

    This function identifies and returns all table names that appear after
    'FROM' or 'JOIN' keywords in the SQL query using regular expression matching.

    Args:
        sql_query (str): A SQL query string.

    Returns:
        list of tuple: A list of tuples containing table names found after 'FROM' or 'JOIN'.
                       Each tuple contains two elements, with one of them being None
                       depending on which keyword matched.
    """
    return re.findall(r"FROM\s+(\w+)|JOIN\s+(\w+)", sql_query, re.IGNORECASE)


def get_actual_tables(db: SQLDatabase):
    """
    Retrieves the list of actual table names from a SQLite database.

    Connects to the underlying SQLite engine using the LangChain SQLDatabase object,
    queries the `sqlite_master` table to get all table names, and returns them as a set
    of lowercase strings.

    Args:
        db (SQLDatabase): An instance of LangChain's SQLDatabase connected to a SQLite database.

    Returns:
        set: A set containing the names of all tables in the database, in lowercase.
    """
    conn = db._engine.raw_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0].lower() for row in cursor.fetchall()]
    conn.close()
    return set(tables)


def validate_sql_tables(sql_query, db: SQLDatabase):
    """
    Validates whether the SQL query references only existing tables in the database.

    Extracts table names used in the SQL query (from FROM and JOIN clauses), compares
    them against the actual tables present in the database, and identifies any missing
    or invalid table references.

    Args:
        sql_query (str): The SQL query to validate.
        db (SQLDatabase): An instance of LangChain's SQLDatabase connected to the target SQLite database.

    Returns:
        set: A set of table names that are referenced in the SQL query but do not exist in the database.
    """
    actual_tables = get_actual_tables(db)
    sql_tables = set(filter(None, sum(extract_tables_from_sql(sql_query), ())))
    missing = sql_tables - actual_tables
    return missing


def auto_correct_sql(sql_query, schema, missing_tables):
    """
    Attempts to automatically correct a SQL query by leveraging an LLM to fix invalid table references.

    Constructs a prompt that explains the SQL error and provides the valid database schema,
    then asks the LLM to return a corrected SQL query using only valid tables and columns.

    Args:
        sql_query (str): The original SQL query with invalid or missing table references.
        schema (str): The full schema of the valid database tables and columns.
        missing_tables (set): A set of table names that were not found in the database.

    Returns:
        str: A corrected SQL query as suggested by the LLM, typically enclosed in a markdown code block.
    """
    correction_prompt = (
        "You have generated the following SQL query, but it uses missing or invalid tables:\n\n"
        f"{sql_query}\n\n"
        f"Missing tables: {', '.join(missing_tables)}\n\n"
        f"Here is the valid database schema:\n{schema}\n\n"
        "Please return a corrected SQL query using only valid tables and columns. Return only SQL in a markdown code block."
    )
    return llm.predict(correction_prompt)
