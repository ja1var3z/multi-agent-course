
# MCP SQL Agent 

This project demonstrates a simple client-server implementation using the Model Context Protocol (MCP), which is a standardized way to connect large language models with tools and data, specifically for managing and interacting with an SQLite database.

## Overview

This example shows how to:
- Create an MCP server with custom tools to interact with an SQLite database.
- Connect to the server using an MCP client.
- Call tools to generate SQL queries, create database tables, and retrieve data.
- Use OpenAI (or Azure OpenAI) to dynamically generate SQL queries.

## Project Structure

```
.
├── .env                        # Environment variables for sensitive data
├── .gitignore                  # Files/folders to ignore in version control
├── mcp_client.py               # MCP client implementation to interact with the server
├── mcp_db.db                   # SQLite database where data is stored
├── mcp_server.py               # MCP server with tools for database management
├── pyproject.toml              # Project metadata and dependencies
├── requirements.txt            # List of required Python packages
└── uv.lock                     # Lock file for uv package manager
```

## Creating the Database

Before running the project, ensure that the `mcp_db.db` SQLite database exists. If it doesn’t, it will be created automatically when the first SQL command is executed by the server. You can also manually create the database file if needed using the following SQLite command:

```bash
sqlite3 mcp_db.db
```

This will create an empty SQLite database that the server will interact with.

## Server Implementation

The server exposes two tools:
1. **`database_update_tool`**: Executes SQL commands such as creating tables in the SQLite database (`mcp_db.db`).
2. **`query_data`**: Executes SELECT queries to retrieve data from the SQLite database.

The server listens for requests from the client and interacts with the SQLite database accordingly.

## Client Implementation

The client connects to the server via stdio, initializes a session, and sends SQL commands based on user input. The client uses OpenAI (or Azure OpenAI) to generate SQL queries dynamically from natural language input.

### Key Features:
- **SQLite Integration**: The client communicates with the `mcp_db.db` SQLite database, performing operations like creating tables and querying data.
- **Dynamic SQL Generation**: OpenAI generates SQL queries based on user input.
- **MCP Protocol**: The client and server communicate using the MCP protocol to call tools and execute SQL commands.

## Getting Started

### Prerequisites

- Python 3.9+
- `uv` (Python package manager)
- SQLite (included with Python, but ensure it's available)

### Installation

```bash
# Install dependencies
uv add "mcp[cli]" requests python-dotenv openai
# Or alternatively, install from requirements.txt
uv add -r requirements.txt
```

### Running the Example

1. **Start the client** (which will automatically start the server):

```bash
uv run mcp_client.py
```

This command will:
- Start the client, which connects to the MCP server.
- The client will then send requests to the server to execute SQL queries.

### Running the Server Manually

If you prefer, you can run the server separately with:

```bash
uv run mcp_server.py
```

### Running the Client and Interacting with the Database

Once the client is running, it will:
1. Connect to the server.
2. Allow the user to input SQL-related commands (such as creating tables).
3. The client sends the input to OpenAI, which generates a corresponding SQL query.
4. The server executes the SQL query on the SQLite database and returns the result.

### Example Use Case: Create a Table

For example, if the user types:

```
create table locations
```

The client will:
- Ask OpenAI to generate a valid SQL query for creating the table.
- The server will then execute the query in the `mcp_db.db` SQLite database.

### Example Response

```
===== MCP CLIENT =====

[04/08/25 00:36:47] INFO     Processing request of type ListToolsRequest                                                                                           server.py:534
Available tools at startup: ['database_update_tool', 'query_data']

You: create table locations
[USING OpenAI] Generating SQL query from user input

Assistant: To create a table named `locations` in an SQLite database, you can use the following SQL statement. This example assumes you want to include some common fields such as `id`, `name`, and `address`, but you can modify it as needed to fit your use case.

```sql
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    latitude REAL,
    longitude REAL
);
```

This creates a table with the following columns:
- `id`: An integer that auto-increments with each new entry (serves as the primary key).
- `name`: A text field for the name of the location (not null).
- `address`: A text field for the address of the location (not null).
- `latitude`: A real number to store the latitude of the location.
- `longitude`: A real number to store the longitude of the location.

Feel free to adjust the column names and data types based on your specific requirements!

[USING LOCAL FUNCTION: database_update_tool]
[04/08/25 00:36:56] INFO     Processing request of type CallToolRequest                                                                                            server.py:534

Assistant: meta=None content=[TextContent(type='text', text='Query executed successfully. 0 rows affected.', annotations=None)] isError=False
```

## Resources

This project uses:
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Official Documentation](https://modelcontextprotocol.io)
