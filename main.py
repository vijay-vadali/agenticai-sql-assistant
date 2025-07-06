import warnings

warnings.filterwarnings("ignore")

import logging

logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("langchain").setLevel(logging.ERROR)

import os
from utils import (
    strict_sql_generator,
    fix_invalid_sql,
    extract_sql_from_response,
    validate_sql_tables,
    auto_correct_sql,
)
from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLDataBaseTool,
)
from langchain.agents import Tool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents import Tool as LangchainTool
import sqlite3
import streamlit as st

from datetime import datetime

os.environ["OPENAI_API_KEY"] = "key"

db_path = "coinmarketcap.sqlite"
conn = sqlite3.connect(db_path)

cursor = conn.cursor()

db = SQLDatabase.from_uri("sqlite:///coinmarketcap.sqlite")

tools = [
    QuerySQLDataBaseTool(db=db),
    InfoSQLDatabaseTool(db=db),
    ListSQLDatabaseTool(db=db),
    LangchainTool(
        name="Explain SQL",
        func=lambda sql: ChatOpenAI(temperature=0).predict(f"Explain this SQL: {sql}"),
        description="Explains the meaning of a given SQL query",
    ),
    LangchainTool(
        name="StrictSQLGenerator",
        func=strict_sql_generator,
        description="NLQ -> SQL only",
    ),
]
schema = db.get_table_info()

strict_sql_tool = Tool(
    name="StrictSQLGenerator",
    func=strict_sql_generator,
    description="Takes a natural language question and returns only the SQL query",
)
llm = ChatOpenAI(temperature=0, model="gpt-4o")  # or "gpt-4" or "gpt-3.5-turbo"

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    tools=[strict_sql_tool],
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors=True,
)

# --- Streamlit UI ---
st.set_page_config(page_title="Text-to-SQL Agent", layout="wide")
st.title("🤖 Agentic SQL Assistant")

st.sidebar.title("📊 Example Questions")
# st.sidebar.markdown("""
# - Top 5 coins by market cap in 2021
# - What was the highest price of Bitcoin in January 2020?
# - Which coin had the lowest volume in March 2019?
# """)
st.sidebar.markdown(
    """
- Top 5 coins by market cap in 2021  
- What was the highest price of Bitcoin in January 2020?  
- Which coin had the lowest volume in March 2019?  
- Show the top 3 coins with a market cap over $1B in July 2021  
- What are the top 3 coins with highest 7-day percent change in 2021?  
- List top 3 coins that dropped more than 10% in a day in 2020
"""
)
user_question = st.text_input(
    "Enter your question:", placeholder="e.g. What is the average market cap in 2021?"
)


if "history" not in st.session_state:
    st.session_state.history = []

if user_question:
    with st.spinner("Generating SQL..."):
        agent_prompt = (
            "You are a SQL expert.\n"
            "Use only the following database schema to answer the question.\n\n"
            f"{schema}\n\n"
            "Translate the question into a valid SQL query.\n"
            "Do NOT make up tables or columns.\n"
            # "Return only valid SQL inside a markdown code block.\n\n"
            "Return ONLY the SQL query. Do NOT wrap it in markdown or provide explanation.\n\n"
            f"Question: {user_question}\nSQL:"
        )
        # raw_output = agent_executor.run(agent_prompt)
        raw_output = llm.predict(agent_prompt)
        # sql = strict_sql_generator(user_question)
        generated_sql = extract_sql_from_response(raw_output)

    st.subheader("Agent Response")
    raw_sql = strict_sql_generator(user_question)
    sql = extract_sql_from_response(raw_sql)
    st.text_area("Generated SQL", sql)
    col1, col2 = st.columns(2)

    if st.button("Run and Explain SQL"):
        missing_tables = validate_sql_tables(generated_sql, db)
        if missing_tables:
            st.warning(f"⚠️ Invalid SQL: {', '.join(missing_tables)}")
            if st.button("🔁 Auto-correct SQL"):
                corrected_sql = auto_correct_sql(generated_sql, schema, missing_tables)
                corrected_sql_clean = extract_sql_from_response(corrected_sql)
                print(corrected_sql_clean)
                if sql.lower().startswith("-- no valid sql"):
                    st.warning(
                        "⚠️ The model couldn't generate a SQL query based on your question."
                    )
                else:
                    st.text_area("✅ Corrected SQL:", corrected_sql_clean)
        else:
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute(sql)
                rows = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]
                conn.close()
                st.success("✅ Query executed successfully")
                result = [dict(zip(col_names, row)) for row in rows]
                st.dataframe(result)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.history.append(
                    (
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        user_question,
                        generated_sql,
                        result,
                    )
                )
                explain_prompt = f"Explain what the following SQL query does:\n\n{sql}"
                explanation = llm.predict(explain_prompt)
                # st.markdown(f"**Explanation:**{explanation}")
                st.info(explanation)
            except Exception as e:
                st.error(f"❌ SQL Error: {e}")
                if st.checkbox("Try auto-fix SQL"):
                    fixed_sql = fix_invalid_sql(generated_sql, str(e))
                    st.warning("Suggested fix:")
    st.download_button(
        label="💾 Download SQL",
        data=sql,
        file_name="generated_query.sql",
        mime="text/sql",
    )
st.subheader("Conversation History")
for i, (ts, q, sql, result) in enumerate(reversed(st.session_state.history[-5:]), 1):
    print(i, q, sql, result)
    st.markdown(f"**{i}. Q:** {q}")
    st.code(sql, language="sql")
