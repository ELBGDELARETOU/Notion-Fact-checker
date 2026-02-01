from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.environ["NOTION_API_KEY"])
DATABASE_ID = os.environ["DATABASE_ID"]

def get_page_to_verify():
    """
    récupère les pages dont le statut est To verify.
    """
    response = notion.databases.query(database_id=DATABASE_ID)
    pages = response.get("results", [])
    to_verify = []

    for page in pages:
        status_prop = page["properties"].get("Fact-checking")
        if status_prop and status_prop["type"] == "status":
            status = status_prop.get("status")
            if status and status.get("name") == "To verify":
                to_verify.append(page)

    return to_verify


def get_page_content(page):
    """
    récupère uniquement le contenu à fact-checker.
    """
    prop = page["properties"].get("Contenu")
    if prop and prop["type"] == "rich_text":
        return " ".join(rt["plain_text"] for rt in prop["rich_text"])
    return ""

def updates_page_status(page_id: str, status: str, source: str = None, explanation: str = ""):
    """
    met à jour le statut, la source et l’explication d’une page.
    """
    
    notion.pages.update(
        page_id=page_id,
        properties={
            "Fact-checking": {
                "status": {"name": status}
            },
            "Source": (
                {"url": source}
                if source else
                {"url": None}
            ),
            "Explanation": {
                "rich_text": (
                    [{"type": "text", "text": {"content": explanation}}]
                    if explanation else []
                )
            }
        }
    )

