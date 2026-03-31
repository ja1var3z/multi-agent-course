from mcp.server.fastmcp import FastMCP
import sqlite3

# Initialize FastMCP server
mcp = FastMCP("DatabaseTool")

def execute_sql_command(sql: str) -> str:
    try:
        # Connect to the database named 'mcp_db' (or create it if not exists)
        conn = sqlite3.connect('./mcp_db.db')  
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        result = cursor.fetchall()
        conn.close()
        return f"Query executed successfully. {len(result)} rows affected."
    except Exception as e:
        return f"Error: {str(e)}"

# Tool to handle database updates
@mcp.tool()
async def database_update_tool(query: str) -> str:
    """Execute SQL update queries"""
    if "CREATE TABLE" in query.upper():
        return execute_sql_command(query)
    else:
        return "Error: Invalid SQL query. Please provide a valid CREATE TABLE query."

# Tool to query database
@mcp.tool()
async def query_data(sql: str) -> str:
    """Execute SELECT SQL queries safely"""
    try:
        conn = sqlite3.connect("./mcp_db.db") 
        cursor = conn.cursor()
        result = cursor.execute(sql).fetchall()
        conn.commit()
        conn.close()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"

# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="stdio")
