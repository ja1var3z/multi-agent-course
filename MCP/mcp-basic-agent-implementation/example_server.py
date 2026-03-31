from mcp.server.fastmcp import FastMCP
import httpx
import asyncio
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv
import os
from openai import AsyncAzureOpenAI

load_dotenv()

mcp = FastMCP("Python360")

@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m ** 2)

@mcp.tool()
async def fetch_weather(latitude: float, longitude: float) -> str:
    """Fetch current weather for a location using latitude and longitude"""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&current_weather=true&"
        f"hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

import logging

@mcp.tool()
async def fetch_fun_fact() -> str:
    """Fetch a random fun fact"""
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                fact_data = response.json()
                return fact_data.get("text", "No fun fact available.")
            else:
                return f"Error: Unable to fetch fun fact. Status code: {response.status_code}"
    except httpx.RequestError as e:
        logging.error(f"An error occurred while fetching the fun fact: {e}")
        return "Error: Could not fetch fun fact due to a request error."
    except ValueError as e:
        logging.error(f"Error parsing the response: {e}")
        return "Error: Failed to parse the fun fact response."





AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')



openai_client =  AsyncAzureOpenAI(
  azure_endpoint =AZURE_OPENAI_ENDPOINT,
  api_key=AZURE_OPENAI_KEY,
  api_version=AZURE_API_VERSION
)


YOUTUBE_API_KEY =os.getenv('YOUTUBE_API_KEY')

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


@mcp.tool()

async def summarize_youtube(query: str) -> str:
    """Search YouTube for top 3 videos based on user query and return summarized content"""
    try:
        search_response = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=3
        ).execute()

        video_summaries = []
        for video in search_response["items"]:
            video_id = video["id"]["videoId"]
            title = video["snippet"]["title"]

            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                full_text = " ".join([entry["text"] for entry in transcript])

                summary_prompt = f"Summarize the following YouTube transcript in a few sentences:\n\n{full_text}"

                summary_resp = await openai_client.chat.completions.create(
                    model="gpt-4",  
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes YouTube videos."},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=300
                )

                summary = summary_resp.choices[0].message.content

            except (TranscriptsDisabled, NoTranscriptFound):
                summary = "Transcript not available for this video."

            video_summaries.append(f"📺 **{title}**\nhttps://www.youtube.com/watch?v={video_id}\n📝 Summary: {summary}\n")

        return "\n\n".join(video_summaries)

    except Exception as e:
        return f"An error occurred: {e}"



if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(asyncio.sleep(0))  
    mcp.run()

    """Since mcp.run() is blocking, but we also have async functions (like fetch_weather), 
        the best solution is to run the  async tasks in a background event loop before calling mcp.run().
    """