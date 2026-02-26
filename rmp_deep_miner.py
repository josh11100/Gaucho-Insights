import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

async def mine_professor_details(browser, url):
    # Use a specific mobile-user agent (RMP often loads faster/simpler on mobile)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
    )
    page = await context.new_page()
    
    # SPEED HACK: Block everything except the essential HTML and Scripts
    await page.route("**/*", lambda route: route.abort() 
        if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
        else route.continue_())

    data = {"rmp_tags": "None", "rmp_difficulty": "N/A", "rmp_take_again": "N/A"}
    
    try:
        # 1. Navigate - 'wait_until' is now irrelevant because we blocked the junk
        await page.goto(url, timeout=20000)
        
        # 2. Hard sleep - sometimes the simplest way is the best
        await asyncio.sleep(1.5) 

        # 3. Stats Grab
        stats = await page.locator('[class*="FeedbackNumber"]').all_inner_texts()
        if len(stats) >= 2:
            data["rmp_take_again"] = stats[0]
            data["rmp_difficulty"] = stats[1]

        # 4. TAG GRAB: Look for the text inside any bubble-like element
        # RMP uses many different class names, so we look for the text pattern
        all_text = await page.evaluate("() => document.body.innerText")
        
        # List of known RMP tag keywords to find in the bulk text
        rmp_tag_list = [
            "Tough Grader", "Good Feedback", "Respected", "Lecture Heavy", 
            "Test Heavy", "Amazing Lectures", "Hilarious", "Caring", 
            "Extra Credit", "Group Projects", "Accessible", "Pop Quizzes", 
            "Many Papers", "Clear Grading", "Participation Matters", "Inspirational"
        ]
        
        found = [tag for tag in rmp_tag_list if tag.lower() in all_text.lower()]
        
        if found:
            data["rmp_tags"] = ", ".join(found)
        else:
            # Fallback to specific CSS if the text-scrape failed
            tags = await page.locator('[class*="TagBubble"]').all_inner_texts()
            if tags:
                data["rmp_tags"] = ", ".join(list(set(tags)))

    except Exception as e:
        print(f"   ⚠️ Failed {url[-5:]}: {e}")
    
    await page.close()
    await context.close()
    return data
    
async def main():
    # FORCE LOAD from the search results to start fresh
    input_csv = "data/rmp_search_results.csv"
    output_csv = "data/rmp_final_data.csv"

    if not os.path.exists(input_csv):
        print(f"❌ {input_csv} not found! Run the first scraper first.")
        return

    df = pd.read_csv(input_csv)
    # We are going to process the first 10 rows ONLY to test
    # Change this line:
# test_limit = 10 

# To this:
    test_limit = len(df) 
    print(f"⛏️ Starting FULL mine for all {test_limit} professors...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        results = []
        for i, row in df.head(test_limit).iterrows():
            print(f"[{i+1}/{test_limit}] Mining: {row['instructor']}")
            details = await mine_professor_details(browser, row['rmp_url'])
            
            # Combine original info with new mined info
            combined = {**row.to_dict(), **details}
            results.append(combined)
            
            # Save every time for safety
            pd.DataFrame(results).to_csv(output_csv, index=False)

        await browser.close()
        print(f"🎉 TEST COMPLETE. Check {output_csv}")

if __name__ == "__main__":
    asyncio.run(main())