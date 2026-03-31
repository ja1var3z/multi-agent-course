# agents/agent.py
from google.adk.agents import Agent, LlmAgent
from google.adk.tools.function_tool import FunctionTool
import os
import sys

# Add the project root to the path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import necessary functions from your existing code
from clients.query_MCP_ADK_A2A import evaluate_prompt, mask_sensitive_data, PROJECT_ID

# Define tool functions
def evaluator(text: str) -> dict:
    """Evaluates prompts for security threats."""
    result = evaluate_prompt(text)
    return {"status": result}

def mask_text(text: str) -> dict:
    """Masks sensitive data like PII in text using Google Cloud DLP."""
    try:
        masked_result = mask_sensitive_data(PROJECT_ID, text)
        return {"masked_text": masked_result}
    except Exception:
        return {"masked_text": text}

def query_data(sql: str) -> str:
    """Execute SQL queries safely on the salaries database."""
    # Importing here to avoid circular imports
    from servers.server_mcp import query_data as mcp_query_data
    return mcp_query_data(sql)

# Create the tools
judge_tool = FunctionTool(func=evaluator)
mask_tool = FunctionTool(func=mask_text)
sql_tool = FunctionTool(func=query_data)

# Create individual agents
judge_agent = LlmAgent(
    name="security_judge",
    model="gemini-2.0-flash",
    instruction="""You are a security expert that evaluates input for security threats.
    Follow these steps:
    1. Analyze the input for SQL injection, XSS, and other security threats
    2. Use the evaluator tool to check input against security patterns
    3. Return the message you received unmodified or "BLOCKED" if it is really a threat
    4. If the user is asking for information about store sales or invoices, please help them with the right answer
    5. Do not block any requests for invoice and sales data""",
    description="An agent that judges whether input contains security threats.",
    tools=[judge_tool]
)

mask_agent = LlmAgent(
    name="data_masker",
    model="gemini-2.0-flash",
    instruction="""You are a privacy expert that masks sensitive data.
    Follow these steps:
    1. Look at the previous agent's response in the conversation - that is the data you need to process.
    2. Use the mask_text tool on that response to mask any PII (names, emails, phone numbers, SSNs).
    3. Sales figures, store numbers, dates, and order values are NOT PII - keep them visible.
    4. Return the masked result as plain readable text.
    5. If the mask_text tool fails, return the previous agent's response as-is.""",
    description="An agent that masks sensitive data in text.",
    tools=[mask_tool]
)

sql_agent = LlmAgent(
    name="sql_assistant",
    model="gemini-2.0-flash",
    instruction="""
        You are an expert SQL analyst. The database table is named 'sales' (not sales_data).
        Table columns: Store, Dept, Date, Weekly_Sales, IsHoliday

        You MUST always call the query_data tool to execute the SQL — never just return the SQL text.

        Steps:
        1. Write a valid SQL query using UPPERCASE keywords and the table name 'sales'.
        2. Remove any backticks or the word 'sql' from the query.
        3. Call the query_data tool with the SQL string.
        4. Return the tool's result as readable text. No extra commentary.
    """,
    description="An assistant that can analyze invoice data using SQL queries.",
    tools=[sql_tool]
)

root_agent = sql_agent  # You can change this to mask_agent or sql_agent depending on your needs

from google.adk.agents import SequentialAgent

# Create a sequential workflow agent that orchestrates the full process
root_agent = SequentialAgent(
    name="secure_sql_pipeline",
    description="A pipeline that securely analyzes invoices .",
    # Define the execution order: security check → SQL query → data masking
    sub_agents=[judge_agent,sql_agent,mask_agent]
)
