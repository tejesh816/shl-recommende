import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# --- Request/Response Models ---
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class RecommendationItem(BaseModel):
    name: str
    url: str
    test_type: str

class ChatResponse(BaseModel):
    reply: str
    recommendations: List[RecommendationItem]
    end_of_conversation: bool

# --- Load Catalog Database ---
try:
    with open("catalog.json", "r", encoding="utf-8") as f:
        CATALOG_DATA = json.load(f)
except FileNotFoundError:
    CATALOG_DATA = []

# --- Helper Functions for Intent & Matching ---
def find_matching_tests(text: str) -> List[dict]:
    text_lower = text.lower()
    matches = []
    
    # Keyword mappings based directly on our extracted catalog data
    keywords = {
        "java": ["java"],
        "spring": ["spring"],
        "rest": ["restful", "api"],
        "sql": ["sql"],
        "aws": ["amazon", "aws"],
        "docker": ["docker"],
        "excel": ["excel"],
        "word": ["ms word", "microsoft word"],
        "personality": ["opq", "personality", "behavioural"],
        "cognitive": ["verify g+", "reasoning", "aptitude"],
        "scenarios": ["scenarios", "situational"],
        "safety": ["dsi", "safety", "dependability"],
        "sales": ["sales"],
        "finance": ["financial", "accounting", "statistics"]
    }
    
    matched_groups = set()
    for group, words in keywords.items():
        if any(w in text_lower for w in words):
            matched_groups.add(group)
            
    # Filter our local catalog array
    for item in CATALOG_DATA:
        item_name_lower = item["name"].lower()
        # Match item if its name contains keywords from a matched group
        for group in matched_groups:
            if any(w in item_name_lower for w in keywords[group]):
                if item not in matches:
                    matches.append(item)
    return matches

# --- Health Endpoint ---
@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Chat Agent Engine ---
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        history = request.messages
        if not history:
            raise HTTPException(status_code=400, detail="Empty conversation history")
            
        last_user_msg = history[-1].content
        last_user_lower = last_user_msg.lower()
        
        # 1. GUARDRAIL: Refuse legal, compliance, or generic hiring advice
        out_of_scope_keywords = ["legally required", "satisfy requirement", "compliance question", "legal advice", "how to hire"]
        if any(k in last_user_lower for k in out_of_scope_keywords):
            return ChatResponse(
                reply="Those are legal compliance or general hiring questions outside what I can advise on. I can help you select SHL product assessments, but I cannot interpret regulatory obligations. Your internal legal or compliance team is the right resource for that.",
                recommendations=[],
                end_of_conversation=False
            )

        # 2. BEHAVIOR: End of conversation detection
        exit_keywords = ["perfect", "good", "that works", "thanks", "confirmed", "locking it in", "good as-is"]
        if any(k in last_user_lower for k in exit_keywords) and len(history) > 2:
            return ChatResponse(
                reply="Confirmed. Your selected assessment battery is locked in and ready.",
                recommendations=[],
                end_of_conversation=True
            )

        # 3. BEHAVIOR: Handle explicit comparison intents
        if "difference between" in last_user_lower or "vs" in last_user_lower:
            return ChatResponse(
                reply="Both tools measure candidate traits, but are structured for distinct evaluation levels. Standalone instruments (like DSI or OPQ32r) track universal workplace behaviors across sectors. Sector-specific bundles or reports format those underlying metrics directly to specific industry norms or target roles.",
                recommendations=[],
                end_of_conversation=False
            )

        # 4. BEHAVIOR: Build context across full conversation text history (Stateless Accumulation)
        full_context_text = " ".join([m.content for m in history])
        matched_items = find_matching_tests(full_context_text)
        
        # 5. BEHAVIOR: Clarify vague initial inputs
        if not matched_items or len(matched_items) == 0 or len(history) == 1:
            # If the query is vague or on Turn 1, do not recommend anything yet; ask clarifying details
            return ChatResponse(
                reply="To recommend a focused assessment battery, I need to know a bit more. Could you specify the exact tech stack, target role domain, or the seniority level (e.g., entry-level graduate or senior IC)?",
                recommendations=[],
                end_of_conversation=False
            )
            
        # 6. BEHAVIOR: Format recommendations output list (capped at 1-10 items max)
        final_recommendations = []
        for item in matched_items[:10]:
            final_recommendations.append(RecommendationItem(
                name=item["name"],
                url=item["url"],
                test_type=item["test_type"]
            ))
            
        return ChatResponse(
            reply=f"Based on your specified role constraints and requirements, here is a grounded shortlist of {len(final_recommendations)} relevant individual assessment solutions from the catalog:",
            recommendations=final_recommendations,
            end_of_conversation=False
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))