import asyncio
import pandas as pd
from playwright.async_api import async_playwright

# UCSB School ID on RateMyProfessors is 1077
BASE_URL = "https://www.ratemyprofessors.com/search/professors/1077?q=*"

async def scrape_ucsb_profs():
    async with async_playwright() as p:
        # 1. Launch Browser
        browser = await p.chromium.launch(headless=False) # Set to False so you can watch it work
        page = await browser.new_page()
        print("Searching RMP for UCSB Professors...")
        
        await page.goto(BASE_URL)

        # 2. Handle Cookies/Privacy Popups if they appear
        try:
            await page.click('button:has-text("Close")', timeout=5000)
        except:
            pass

        # 3. Infinite Scroll / "Show More" 
        # RMP uses a "Show More" button. We need to click it until it's gone.
        print("Loading all professors (this may take a minute)...")
        while True:
            try:
                show_more_button = page.locator('button:has-text("Show More")')
                if await show_more_button.is_visible():
                    await show_more_button.click()
                    await asyncio.sleep(1) # Wait for content to load
                else:
                    break
            except:
                break

        # 4. Extract Data
        profs = []
        cards = await page.locator('[class*="TeacherCard__StyledTeacherCard"]').all()
        
        for card in cards:
            name = await card.locator('[class*="CardName__StyledCardName"]').inner_text()
            rating = await card.locator('[class*="CardNumRating__CardNumRatingNumber"]').inner_text()
            dept = await card.locator('[class*="CardDepartment__StyledCardDepartment"]').inner_text()
            # Difficulty and "Take Again" are usually in a secondary sub-text
            meta = await card.locator('[class*="CardNumRating__CardNumRatingCount"]').all_inner_texts()
            
            profs.append({
                "instructor": name.upper(), # Upper case to match your CSV
                "rmp_rating": rating,
                "rmp_dept": dept
            })

        # 5. Save to CSV
        df = pd.DataFrame(profs)
        df.to_csv("data/rmp_ratings.csv", index=False)
        print(f"Success! Saved {len(df)} professors to data/rmp_ratings.csv")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_ucsb_profs())
