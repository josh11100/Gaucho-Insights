import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

# UCSB ID is 1077
BASE_URL = "https://www.ratemyprofessors.com/search/professors/1077?q=*"

async def scrape_ucsb_profs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🚀 Starting Gaucho Scraper...")
        await page.goto(BASE_URL)

        # Close initial popup
        try:
            await page.wait_for_selector('button:has-text("Close")', timeout=5000)
            await page.click('button:has-text("Close")')
        except:
            pass

        # --- SETTINGS ---
        limit = 40  # Stop after 40 "Show More" clicks (~320 professors)
        save_every = 5 # Export to CSV every 5 clicks just in case
        
        print(f"🖱️ Scrolling... will auto-stop after {limit} clicks.")

        for i in range(1, limit + 1):
            try:
                show_more = page.locator('button:has-text("Show More")')
                if await show_more.is_visible():
                    await show_more.scroll_into_view_if_needed()
                    await show_more.click()
                    print(f"   [{i}/{limit}] Clicked Show More...")
                    await asyncio.sleep(1.2) # Wait for cards to load
                else:
                    print("🏁 Reached the end of the list.")
                    break
                
                # Autosave Progress
                if i % save_every == 0:
                    await extract_and_save(page, is_partial=True)
                    
            except Exception as e:
                print(f"⚠️ Loop interrupted: {e}")
                break

        # Final extraction
        await extract_and_save(page, is_partial=False)
        await browser.close()

async def extract_and_save(page, is_partial=False):
    """Helper function to grab data and write to CSV"""
    cards = await page.locator('a[class*="TeacherCard__StyledTeacherCard"]').all()
    profs = []
    
    for card in cards:
        try:
            name = await card.locator('[class*="CardName__StyledCardName"]').inner_text()
            rating = await card.locator('[class*="CardNumRating__CardNumRatingNumber"]').inner_text()
            dept = await card.locator('[class*="CardDepartment__StyledCardDepartment"]').inner_text()
            
            profs.append({
                "instructor": name.strip().upper(),
                "rmp_rating": rating.strip(),
                "rmp_dept": dept.strip()
            })
        except:
            continue

    if not os.path.exists("data"):
        os.makedirs("data")

    df = pd.DataFrame(profs).drop_duplicates(subset=['instructor'])
    filename = "data/rmp_ratings_partial.csv" if is_partial else "data/rmp_ratings.csv"
    df.to_csv(filename, index=False)
    
    status = "Autosaved (Partial)" if is_partial else "Final Save"
    print(f"💾 {status}: {len(df)} professors found.")

if __name__ == "__main__":
    asyncio.run(scrape_ucsb_profs())
