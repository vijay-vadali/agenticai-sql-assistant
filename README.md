# 🧠 Agentic SQL Assistant

A natural language interface to query structured data using **LangChain Agents**, **OpenAI's GPT**, and **Streamlit**. This assistant enables non-technical users to explore complex SQL databases using plain English.

## ✨ Features

- Ask natural language questions and get SQL queries.
- Executes and explains SQL.
- Auto-corrects invalid SQL using LLMs.
- Stores recent conversation history.
- Built-in Streamlit UI.
- Run locally or in Docker.

---

## 📦 Project Structure

```

.
├── main.py # Streamlit + Agent application
├── utils.py # Helper functions
├── Dockerfile # For containerization
├── coinmarketcap.sqlite # Sample SQLite DB (CoinMarketCap data)
├── requirements.txt # Python dependencies
├── README.md
├── agentic_sql_assistant.ipynb Jupyter Notebook

```

---

## ⚙️ Requirements

- Python 3.10+
- OpenAI API key
- SQLite3
- (Optional) Docker

---

## 🚀 Getting Started

### 🖥️ Run Locally (Streamlit)

1. **Clone the Repository**

   ```bash
   git clone https://github.com/vijay-vadali/agentic-sql-assistant.git
   cd agentic-sql-assistant
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Your API Key**
   Export your OpenAI key in the shell:

   ```bash
   export OPENAI_API_KEY=sk-xxxxx
   ```

   Or edit `main.py` and replace:

   ```python
   os.environ["OPENAI_API_KEY"] = "sk-xxxxx"
   ```

4. **Run the App**

   ```bash
   streamlit run main.py
   ```

5. **Open in Browser**
   Navigate to `http://localhost:8501` to start querying.

---

### 🐳 Run in Docker

1. **Build the Image**

   ```bash
   docker build -t agentic-sql-assistant .
   ```

2. **Run the Container**

   ```bash
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=sk-xxxxx \
     agentic-sql-assistant
   ```

3. **Access the App**
   Open your browser at [http://localhost:8501](http://localhost:8501)

---

## 🧪 Example Questions

- What was the highest price of Bitcoin in January 2020?
- Which coins had the lowest volume in March 2019?
- Top 5 coins by market cap in 2021.
- What is the average daily volume for Ethereum in 2022?

---

## 🧠 How It Works

The agent uses:

- **LangChain Toolkit**: For SQL schema parsing and routing
- **LLMs (GPT-3.5/4)**: To translate natural language to SQL
- **Streamlit**: To serve an intuitive UI
- **SQLite**: A local demo DB (CoinMarketCap data)

---

## 🐛 Troubleshooting

- **Could not parse LLM output**: Set `handle_parsing_errors=True`
- **LangChainDeprecationWarning**: Ensure you're importing from `langchain_community`
- **API limit exceeded**: Use a different provider or manage usage with API key rotation.

---

## 📂 Dataset

This project uses the [CoinMarketCap Historical Data](https://www.kaggle.com/datasets/bizzyvinci/coinmarketcap-historical-data) available on Kaggle. It contains detailed daily historical data for various cryptocurrencies including price, volume, market cap, and more.

Make sure to download the dataset and place the `coinmarketcap.sqlite` file in the project root.

---

## 🛠️ Future Improvements

- Add authentication
- Add support for more SQL engines (Postgres, MySQL)
- Fine-tuned models for better SQL accuracy
- Export results to CSV
