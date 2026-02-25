import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

BASE_URL = "https://www.ratemyprofessors.com/search/professors/1077?q=*"

async def extract_visible_data(page):
    # This selector is very specific to RMP's current layout
    cards = await page.locator('a[href*="/professor/"]').all()
    profs = []
    for card in cards:
        try:
            # Look for the name and rating inside the card
            name = await card.locator('[class*="CardName__StyledCardName"]').inner_text()
            rating = await card.locator('[class*="CardNumRating__CardNumRatingNumber"]').inner_text()
            
            profs.append({
                "instructor": name.strip().upper(),
                "rmp_rating": rating.strip()
            })
        except:
            continue
    return profs

async def scrape_ucsb_profs():
    async with async_playwright() as p:
        # Launching with a slow_mo so we don't outrun the website
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        print("🚀 Navigating to RMP...")
        await page.goto(BASE_URL)

        # Wait for the first professor to actually appear on screen
        print("⏳ Waiting for cards to appear...")
        try:
            await page.wait_for_selector('[class*="CardName__StyledCardName"]', timeout=15000)
        except:
            print("❌ Timeout: No professors appeared. Is the page blank?")
            await browser.close()
            return

        limit = 200 # Let's keep it small to ensure it finishes
        for i in range(1, limit + 1):
            try:
                # Extract what we see RIGHT NOW
                current_batch = await extract_visible_data(page)
                
                if current_batch:
                    df = pd.DataFrame(current_batch).drop_duplicates(subset=['instructor'])
                    if not os.path.exists("data"): os.makedirs("data")
                    df.to_csv("data/rmp_ratings.csv", index=False)
                    print(f"✅ [{i}/{limit}] Saved {len(df)} professors...")
                else:
                    print(f"⚠️ [{i}/{limit}] No data seen on screen yet...")

                # Try to load more
                show_more = page.locator('button:has-text("Show More")')
                if await show_more.is_visible():
                    await show_more.click()
                    await asyncio.sleep(2) # Give it time to load new cards
                else:
                    break
            except Exception as e:
                print(f"🛑 Stopped at loop {i}: {e}")
                break

        print(f"🏁 Final file updated in data/rmp_ratings.csv")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_ucsb_profs())
