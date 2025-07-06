graph TD
    A[User Input] --> B[Streamlit UI]
    B --> C{Agent Executor}
    
    subgraph LangChain Agent
        C --> D[StrictSQLGenerator Tool]
        C --> E[SQLDatabase Toolkit]
        D --> F[LLM -- ChatOpenAI]
        F -->|Prompt| G[SQL Query Generation]
    end

    G --> H[Validation & Auto-correction]
    H --> I{Missing Tables?}
    I -- Yes --> J[Fix SQL using LLM Prompt]
    J --> K[Execute Corrected SQL]
    I -- No --> K[Execute SQL]
    K --> L[SQLite Database]
    L --> M[Query Result]
    
    M --> N[Streamlit UI: Show Result]
    N --> O[Optional: Explain SQL via LLM]
    N --> P[Download SQL]
    N --> Q[Append to Session History]

    style B fill:#E6F7FF,stroke:#0099CC
    style C fill:#FFF7E6,stroke:#FF9900
    style G fill:#F6FFED,stroke:#52C41A
    style L fill:#F0F0F0,stroke:#666
    style M fill:#D9F7BE,stroke:#389E0D
