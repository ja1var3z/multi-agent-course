
# MCP Server Example  🚀

This project demonstrates an MCP server that integrates with multiple external tools, including weather fetching, YouTube summarization. It communicates with a client via the Model Context Protocol (MCP), enabling seamless interaction with different services.

## Overview

This project includes the following features:
- MCP server with custom tools for fetching weather data, summarizing YouTube videos, and more.
- Integration with OpenAI and Azure OpenAI for generating responses and YouTube summaries.
- Real-time interaction through the MCP client.

## Project Structure

```
.
├── pyproject.toml          # Project configuration
├── README.md               # Project documentation
├── mcp_client.py           # MCP client implementation
├── mcp_server.py           # MCP server with custom tools
└── uv.lock                 # Dependency lock file
```

## Server Implementation

The server exposes the following tools:

1. **`calculate_bmi`** – A tool that calculates the Body Mass Index (BMI) based on weight (kg) and height (m).
2. **`fetch_weather`** – An async tool that retrieves the current weather for a location using latitude and longitude.
3. **`fetch_fun_fact`** – An async tool that retrieves a random fun fact from an external API.
4. **`summarize_youtube`** – An async tool that fetches the top 3 YouTube videos based on a query, and then summarizes the content of each video using YouTube transcripts.

## Client Implementation

The client connects to the server, initializes a session, and can call the server’s tools. It interacts with the user, handling requests for BMI calculation, weather information, fun facts, and YouTube video summaries.

### Key Features:
- **User input handling:** The client listens for user input and sends requests to the server to invoke specific tools.
- **Tool execution:** The client sends requests to the server, which executes the respective tool and returns results like weather data or video summaries.

## Getting Started

### Prerequisites

- Python 3.9+
- uv (Python package manager)
- Environment variables for API keys:
  - `AZURE_OPENAI_KEY`
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_API_VERSION`
  - `YOUTUBE_API_KEY`

### Installation

```bash
# Install dependencies
uv add -r requirements.txt .
```

### Running the Example

1. Start the client (which will automatically start the server):

```bash
uv run mcp_client.py
```

2. The client will connect to the server, list available tools, and prompt you to input commands.

## Usage

The client can:
- Request BMI calculation by providing weight and height.
- Fetch weather data by providing latitude and longitude.
- Request a random fun fact.
- Summarize YouTube videos based on a user query.

## Example Interaction

```
Available tools: calculate_bmi, fetch_weather, fetch_fun_fact, summarize_youtube
You: What is the weather in New York?
Assistant: Fetching weather data for New York...
Weather data: {"current_weather": {"temperature": 14.2, "windspeed": 12.6, ...}}

You: Can you summarize some YouTube videos about "AI"?
Assistant: Fetching top 3 AI videos and summarizing...
📺 **AI Tutorial: How It Works**
📝 Summary: This video explains how artificial intelligence works, covering key concepts like machine learning, deep learning, and neural networks...

You: Exit
Exiting...
```

## Test with MCP Inspector

To inspect the running server and monitor tool invocations:

1. Start the server using:

```bash
mcp dev example_server.py
```

2. Open the MCP Inspector at [http://localhost:5173](http://localhost:5173) to monitor incoming requests.

## Resources

This project uses:
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Official Documentation](https://modelcontextprotocol.io)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Azure OpenAI SDK](https://github.com/Azure/azure-sdk-for-python)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
