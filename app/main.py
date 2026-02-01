import asyncio
from app import agents, notion

async def run_fact_check():
    """
    fonction principale
    """
    pages = notion.get_page_to_verify()

    if not pages:
        return

    print(f"Page(s) founded : {len(pages)}")
    
    for page in pages:
        page_id = page["id"]
        print(f"\nPage ID : {page_id}")
        
        text = notion.get_page_content(page)

        if not text.strip():
            print("Contenu vide, ignoré")
            continue

        print(f"Content : {text[:100]}...")
        
        result = await agents.check_statement(text)
        
        print(f"Verdict : {result['verdict']}")
        print(f"Source : {result.get('source', 'N/A')}")
        
        status = verdict_to_status(result["verdict"])
        source_url = result.get("source")
        
        notion.updates_page_status(
            page_id,
            status=status,
            source=source_url,
            explanation=result.get("explanation", "")
        )
        
        print(f"Page mise à jour : {status}")


def verdict_to_status(verdict: str) -> str:
    """
    change le status selon les verifications 
    """
    if verdict == "true":
        return "Verified"
    elif verdict == "false":
        return "Error"
    else:
        return "Error"


async def main_loop():
    """
    Boucle infinie qui vérifie Notion toutes les 30 secondes
    """

    print("""
            FACT-CHECKER
    ============================
    Verify Notion evry 30 secondes
        Press Ctrl+C to stop
    """)
    
    try:
        while True:
            await run_fact_check()
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nfact-checker stops")
    except Exception as e:
        print(f"\nErreur : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nBye")
