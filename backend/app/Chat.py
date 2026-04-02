import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings

router = APIRouter()

class Chatrequest(BaseModel):
    video_id: str
    message: list[dict]


@router.post("/ask")
async def ask(request: Chatrequest):
    openai_messages = [
        {"role": "system", "content": "You are a helpful assistant that answers questions about the content of the video."} # add more contex for the llm about the video
    ]
    for msg in request.message:
        if msg["role"] == "user":
            openai_messages.append({"role": "user", "content": msg["content"]})

    async with httpx.AsyncClient() as client:
        try:
            result = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "content-type": "application/json"
                },
                json={
                    "model": "openrouter/free",#
                    "messages": openai_messages
                },
                timeout=60.0
            )
            if result.status_code != 200:
                print(f"Error: OpenRouter API returned status code {result.status_code} with response: {result.text}")
                raise HTTPException(status_code=502, detail="Error from AI provider.")
            return result.json()
        except httpx.TimeoutException:
            print("Error: The request to OpenRouter API timed out after 60 seconds.")
            raise HTTPException(status_code=504, detail="Request to AI provider timed out.")
