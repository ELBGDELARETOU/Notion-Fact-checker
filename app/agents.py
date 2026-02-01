import os
import json
import re
import asyncio
from groq import Groq
from dotenv import load_dotenv
import httpx

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL1 = "llama-3.1-8b-instant"
MODEL2 = "openai/gpt-oss-120b"
TEMPERATURE = 0.1

def _clean_json(text: str) -> dict:
    """
    formate la réponse des IA en JSON
    """
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"```$", "", text)
    return json.loads(text.strip())

async def check_ai(sentence: str, agent_id: int, AI_model: str) -> dict:
    """
    crée le prompt et récupère les informations au format attendu.
    """

    prompt = f"""
You are a professional fact-checker AI. You are competing with another AI to provide the most truthful, well-sourced answer.

Check the following statement:
"{sentence}"

Reply ONLY in valid JSON in one line, without any line breaks:
{{
  "verdict": "true" | "false" | "uncertain",
  "explanation": "Short, concise explanation of your verdict, no line breaks.",
  "source": "A real or plausible URL supporting your verdict. Must start with http.",
  "search_query": "Keywords you would use to find the source online, e.g. 'PEA plafond 2024'",
  "confidence": 0.0
}}

RULES:
1. All text fields must be on a single line. Replace newlines with spaces if necessary.
2. "source" must be a valid URL. If unsure, use a reliable placeholder URL starting with http.
3. Provide a truthful verdict based on publicly available knowledge or reasoning.
4. Compete to provide the most accurate, well-sourced answer compared to the other AI.
"""


    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.chat.completions.create(
            model=AI_model,
            messages=[
                {"role": "system", "content": "You are a strict fact-checker."},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=500,
        )
    )

    result = _clean_json(response.choices[0].message.content)
    result["agent_id"] = agent_id

    if result.get("search_query"):
        result["source"] = await search_web_for_source(result["search_query"])

    return result


def consensus(a1: dict, a2: dict) -> dict:
    """
    compare les réponses des deux modèles et calcule la confiance
    """
    print("AI1 verdict:", a1["verdict"])
    print("AI2 verdict:", a2["verdict"])
    if a1["verdict"] == a2["verdict"]:
        source = a1.get("source", "https://example.com")
        if source == "https://example.com" and a2.get("source"):
            source = a2.get("source")
        
        return {
            "verdict": a1["verdict"],
            "confidence": (a1["confidence"] + a2["confidence"]) / 2,
            "explanation": a1["explanation"],
            "source": source,
            "agents_agree": True,
        }

    best = a1 if a1["confidence"] > a2["confidence"] else a2
    
    return {
        "verdict": "uncertain",
        "confidence": max(a1["confidence"], a2["confidence"]) * 0.7,
        "source": best.get("source", "https://example.com"),
        "agents_agree": False,
        "details": {"agent1": a1, "agent2": a2},
    }


async def check_statement(sentence: str) -> dict:
    """
    Vérifie la véracité d'une phrase en utilisant deux agents IA concurrents.
    """
    a1, a2 = await asyncio.gather(
        check_ai(sentence, 1, MODEL1),
        check_ai(sentence, 2, MODEL2),
    )
    return consensus(a1, a2)

def normalize_source(source: str) -> str:
    """
    S'assure que source est une URL valide pour Notion
    """
    if source and source.strip().startswith(("http://", "https://")):
        return source.strip()
    return "https://example.com"

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

async def search_web_for_source(query: str) -> str:
    """
    Recherche une vraie source sur le web
    """
    if not SERPER_API_KEY:
        return "https://example.com"
    
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "q": query,
                    "gl": "fr",
                    "hl": "fr",
                    "num": 3
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                organic = data.get("organic", [])
                if organic:
                    url = organic[0].get("link", "https://example.com")
                    return url
            
            return "https://example.com"
            
    except Exception as e:
        return "https://example.com"