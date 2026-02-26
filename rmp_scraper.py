import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

BASE_URL = "https://www.ratemyprofessors.com/search/professors/1077?q=*"

async def scrape_ucsb_profs():
    if not os.path.exists("data"): os.makedirs("data")
    csv_path = "data/rmp_search_results.csv"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("🚀 Navigating to RMP...")
        await page.goto(BASE_URL)
        await asyncio.sleep(3) # Initial load buffer

        limit = 100 
        for i in range(1, limit + 1):
            try:
                # 1. SCRAPE EVERYTHING CURRENTLY ON SCREEN
                cards = await page.locator('a[href*="/professor/"]').all()
                profs = []
                for card in cards:
                    try:
                        name = await card.locator('[class*="CardName__StyledCardName"]').inner_text(timeout=500)
                        rating = await card.locator('[class*="CardNumRating__CardNumRatingNumber"]').inner_text(timeout=500)
                        rel_url = await card.get_attribute("href")
                        profs.append({
                            "instructor": name.strip().upper(),
                            "rmp_rating": rating.strip(),
                            "rmp_url": f"https://www.ratemyprofessors.com{rel_url}"
                        })
                    except: continue

                # 2. AUTO-SAVE TO CSV IMMEDIATELY
                if profs:
                    df = pd.DataFrame(profs).drop_duplicates(subset=['rmp_url'])
                    df.to_csv(csv_path, index=False)
                    print(f"💾 Autosaved {len(df)} professors (Loop {i})")

                # 3. CLICK SHOW MORE
                show_more = page.locator('button:has-text("Show More")')
                if await show_more.is_visible():
                    await show_more.scroll_into_view_if_needed()
                    await show_more.click()
                    await asyncio.sleep(2.5) # Wait for cards to populate
                else:
                    print("🏁 Reached the end of the list.")
                    break
            except Exception as e:
                print(f"⚠️ Loop interrupted: {e}")
                break

        await browser.close()
        print(f"🎉 Done! Final file: {csv_path}")

if __name__ == "__main__":
    asyncio.run(scrape_ucsb_profs())