import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

# UCSB ID is 1077
BASE_URL = "https://www.ratemyprofessors.com/search/professors/1077?q=*"

async def extract_visible_data(page):
    """Helper to grab whatever is currently rendered on the screen"""
    # Using the most stable selector for professor cards
    cards = await page.locator('a[href*="/professor/"]').all()
    profs = []
    for card in cards:
        try:
            # Extract Name and Rating
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
    return profs

async def scrape_ucsb_profs():
    async with async_playwright() as p:
        # slow_mo=500 helps the browser stay in sync with the script
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        print("🚀 Navigating to RMP...")
        await page.goto(BASE_URL)

        # 1. Handle Cookie/Privacy Popup
        try:
            await page.wait_for_selector('button:has-text("Close")', timeout=5000)
            await page.click('button:has-text("Close")')
        except:
            pass

        # 2. Wait for data to actually load
        print("⏳ Waiting for professor cards to appear...")
        try:
            await page.wait_for_selector('[class*="CardName__StyledCardName"]', timeout=15000)
        except:
            print("❌ Timeout: No data found. Check your internet or if RMP blocked the IP.")
            await browser.close()
            return

        # 3. The Loop
        limit = 100  # Adjust this: 100 clicks = ~800-1000 professors
        print(f"🖱️ Starting scrape loop (Limit: {limit} clicks)...")
        
        for i in range(1, limit + 1):
            try:
                # Extract and save IMMEDIATELY so we don't lose progress on crash
                current_batch = await extract_visible_data(page)
                
                if current_batch:
                    df = pd.DataFrame(current_batch).drop_duplicates(subset=['instructor'])
                    if not os.path.exists("data"): os.makedirs("data")
                    df.to_csv("data/rmp_ratings.csv", index=False)
                    print(f"✅ [{i}/{limit}] Total professors saved: {len(df)}")
                
                # Try to load more
                show_more = page.locator('button:has-text("Show More")')
                if await show_more.is_visible():
                    await show_more.scroll_into_view_if_needed()
                    await show_more.click()
                    # Wait for new elements to render
                    await asyncio.sleep(2) 
                else:
                    print("🏁 Reached the bottom of the list.")
                    break
                    
            except Exception as e:
                print(f"🛑 Error on loop {i}: {e}")
                break

        print(f"🎉 Scraping complete! Check 'data/rmp_ratings.csv'")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_ucsb_profs())
