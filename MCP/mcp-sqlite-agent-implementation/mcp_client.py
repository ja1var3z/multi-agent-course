import logging
import sqlite3
import asyncio
import re
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import json
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')

openai_client = AsyncAzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_API_VERSION
)

conversation_history = [{"role": "system", "content": "You are a helpful assistant who works with an SQLite database. Please ensure that SQL queries you generate are compatible with SQLite syntax."}]


server_params = StdioServerParameters(
command="uv", 
args=["run","mcp_server.py"],
env=None, 

)

def extract_sql_query(text: str) -> str:
    match = re.search(r'```sql\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

async def detect_and_handle_local_function(user_input, session):
    user_input_lower = user_input.lower()
    if "create table" in user_input_lower:
        # Call OpenAI to generate SQL query
        print(f"[USING OpenAI] Generating SQL query from user input")
        conversation_history.append({"role": "user", "content": user_input})

        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo", messages=conversation_history
        )
        assistant_response = response.choices[0].message.content
        print(f"\nAssistant: {assistant_response}")
        
        # Extract SQL query from assistant's response
        sql_query = extract_sql_query(assistant_response)
        if sql_query:
            # Execute the extracted SQL query
            print(f"[USING LOCAL FUNCTION: database_update_tool]")
            tool_result = await session.call_tool("database_update_tool", arguments={"query": sql_query})
            print(f"\nAssistant: {tool_result}")
            conversation_history.append({"role": "assistant", "content": tool_result})
        else:
            print("Error: Could not extract SQL query from the response.")
        
        return True
    return False

# Example prompt loop to handle user input
async def run():
    print("\n===== MCP CLIENT =====\n")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Debugging: List available tools when MCP session is initialized
            tools = await session.list_tools()
            print(f"Available tools at startup: {[tool.name for tool in tools.tools]}")  # Debugging

            while True:
                user_input = input("\nYou: ").strip()
                if user_input.lower() == "exit":
                    print("Exiting...")
                    break
                if not await detect_and_handle_local_function(user_input, session):
                    print("\n[USING OpenAI]")
                    conversation_history.append({"role": "user", "content": str(user_input)})

                    response = await openai_client.chat.completions.create(
                        model="gpt-3.5-turbo", messages=conversation_history
                    )
                    assistant_response = response.choices[0].message.content
                    print(f"\nAssistant: {assistant_response}")
                    conversation_history.append({"role": "assistant", "content": assistant_response})

if __name__ == "__main__":
    asyncio.run(run())