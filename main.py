import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS configuration so your local frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (including local files)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Request schema for the chat endpoint
class ChatRequest(BaseModel):
    message: str

# 1. Health Check Endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# 2. Recommender Chat Endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip().lower()
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    # Standard baseline fallback response
    bot_response = "I received your message! I am processing your recommendation request based on the catalog data."
    
    # Simple keyword routing rule as an example
    if "hello" in user_message or "hi" in user_message:
        bot_response = "Hello! I am your SHL Catalog Recommender chatbot. How can I help you find what you need today?"
    elif "catalog" in user_message or "list" in user_message:
        bot_response = "You can view our interactive catalog documentation inside the /docs panel of this API server."
        
    return {"response": bot_response}