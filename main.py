import json
import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

# Enable CORS configuration so your local frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# Helper function to load catalog
def load_catalog() -> List[Dict[str, Any]]:
    catalog_path = os.path.join(os.path.dirname(__file__), "catalog.json")
    if not os.path.exists(catalog_path):
        return []
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

# Helper function to tokenize text for keyword matching
def tokenize(text: str) -> set:
    return set(re.findall(r'\w+', text.lower()))

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    catalog = load_catalog()
    if not catalog:
        return {
            "response": "Hello! I am currently unable to access the assessment catalog database. Please verify catalog.json exists.",
            "recommendations": []
        }
    
    query_tokens = tokenize(user_message)
    scored_recommendations = []
    
    # Simple Content-Based Filtering using Jaccard-like keyword overlap
    for item in catalog:
        # Combine available text fields safely
        name = item.get("assessment_name", "")
        description = item.get("description", "")
        test_type = item.get("test_type", "")
        
        item_text = f"{name} {description} {test_type}"
        item_tokens = tokenize(item_text)
        
        # Calculate intersection score
        overlap = query_tokens.intersection(item_tokens)
        score = len(overlap)
        
        scored_recommendations.append((score, item))
    
    # Sort by score descending
    scored_recommendations.sort(key=lambda x: x[0], reverse=True)
    
    # Extract top matching items (Targeting between 5 and 10)
    top_items = []
    for score, item in scored_recommendations:
        # Include items with matching words, or fill up to at least 5 baseline solutions
        if score > 0 or len(top_items) < 5:
            # Map clean metadata structure matching evaluation requirements
            top_items.append({
                "assessment_name": item.get("assessment_name", "Standard Assessment"),
                "url": item.get("url", "https://www.shl.com"),
                "remote_testing_support": item.get("remote_testing_support", "Yes"),
                "adaptive_irt_support": item.get("adaptive_irt_support", "No"),
                "duration": item.get("duration", "30 mins"),
                "test_type": item.get("test_type", "Cognitive Ability")
            })
        if len(top_items) >= 10:
            break

    # Build clear textual UI response string
    response_text = f"Based on your query, I found {len(top_items)} highly relevant assessment solutions from the SHL catalog:\n\n"
    
    return {
        "response": response_text,
        "recommendations": top_items
    }