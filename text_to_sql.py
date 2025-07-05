import os
import re
import streamlit as st
from agno.agent import Agent
from agno.tools.sql import SQLTools
from agno.models.groq import Groq

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Database config for insurance policy management
DB_CONFIG = {
    "host": "insurance-db.example.com",
    "port": "",
    "user": "policy_admin",
    "password": "secure_insurance_db_pass",
    "database": "policy_management"
}

db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

system_message = """You are an insurance database expert with complete knowledge of these tables:
=== INSURANCE POLICY SCHEMA ===
1. policies (
   policy_id INT PRIMARY KEY,
   policy_number VARCHAR(50) UNIQUE NOT NULL,
   policy_type ENUM('Auto', 'Home', 'Life', 'Health'),
   start_date DATE,
   end_date DATE,
   premium DECIMAL(12,2),
   status ENUM('Active', 'Expired', 'Cancelled', 'Pending'),
   created_at DATETIME
)

2. customers (
   customer_id INT PRIMARY KEY,
   first_name VARCHAR(100) NOT NULL,
   last_name VARCHAR(100) NOT NULL,
   date_of_birth DATE,
   ssn_encrypted VARCHAR(255),
   email VARCHAR(255),
   phone VARCHAR(20),
   address TEXT
)

3. policy_holders (
   id INT PRIMARY KEY,
   policy_id INT FOREIGN KEY REFERENCES policies(policy_id),
   customer_id INT FOREIGN KEY REFERENCES customers(customer_id),
   relationship ENUM('Primary', 'Secondary', 'Dependent'),
   coverage_level VARCHAR(50)
)

4. claims (
   claim_id INT PRIMARY KEY,
   policy_id INT FOREIGN KEY REFERENCES policies(policy_id),
   claim_date DATE,
   claim_amount DECIMAL(12,2),
   claim_status ENUM('Filed', 'In Review', 'Approved', 'Denied', 'Paid'),
   description TEXT,
   adjuster_id INT
)

5. payments (
   payment_id INT PRIMARY KEY,
   policy_id INT FOREIGN KEY REFERENCES policies(policy_id),
   amount DECIMAL(12,2),
   payment_date DATE,
   payment_method ENUM('Credit Card', 'Bank Transfer', 'Check'),
   transaction_reference VARCHAR(255)
)

=== QUERY GUIDELINES ===
1. Always maintain strict data privacy - never include sensitive fields like SSN in results
2. Use appropriate JOINs to connect related tables (policies → customers → claims)
3. Include relevant date filters when appropriate (active policies, recent claims)
4. For financial calculations, use proper decimal precision
5. For complex queries, use subqueries to break down the problem

=== RESPONSE FORMAT ===
Return ONLY the SQL query wrapped in ```sql code blocks and a brief explanation of what the query does."""

# Initialize agent
try:
    agent = Agent(
        model=Groq(
            id="gemma2-9b-it",
            api_key=os.environ["GROQ_API_KEY"],
            temperature=0.3
        ),
        tools=[SQLTools(db_url=db_url)],
        system_message=system_message,
        tool_choice="none",
        markdown=True
    )
except Exception as e:
    st.error(f"Failed to initialize agent: {str(e)}")
    st.stop()

# Streamlit Interface
st.set_page_config(page_title="Policy Query Assistant", page_icon="🛡️")
st.title("🛡️ Insurance Policy Query Generator")
st.write("Convert your insurance policy questions into SQL queries for our policy database")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about policies (e.g. 'Show active auto policies with claims in 2023'):"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Generating policy query..."):
            full_response = ""
            try:
                response = agent.run(prompt)
                response_content = response.get_content_as_string()
                
                # Extract SQL from either code block or raw response
                sql_match = re.search(r'```sql\n(.*?)\n```', response_content, re.DOTALL)
                if sql_match:
                    formatted_sql = sql_match.group(1).strip()
                    explanation = response_content.replace(sql_match.group(0), '').strip()
                    full_response = f"```sql\n{formatted_sql}\n```\n\n{explanation}"
                else:
                    full_response = f"```sql\n{response_content}\n```"
                
                st.markdown(full_response)

            except Exception as e:
                error_msg = f"⚠️ Policy Query Error: {str(e)}"
                st.error(error_msg)
                full_response = error_msg
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})