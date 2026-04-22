import asyncio
import pandas as pd
import requests
import time
import os
import base64
from playwright.async_api import async_playwright

#cinfigs
UCSB_ID = "U2Nob29sLTEwNzc="  #base64 encoded id for UCSB
CSV_FILE = "rmp_final_data.csv"
CONCURRENT_PAGES = 5 #limits browser instances to prevent cpu throttling
API_URL = "https://www.ratemyprofessors.com/graphql"
HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# UID
def get_graphql_query(cursor):
    return {
        "query": """
        query TeacherSearchPaginationQuery($count: Int!, $cursor: String, $query: TeacherSearchQuery!) {
          newSearch {pip
            teachers(query: $query, first: $count, after: $cursor) {
              pageInfo { hasNextPage, endCursor }
              edges {
                node {
                  firstName, lastName, avgRating, avgDifficulty, numRatings, 
                  wouldTakeAgainPercent, department, id
                }
              }
            }
          }
        }
        """,
        "variables": { 
            "count": 1000, 
            "cursor": cursor, 
            "query": {"text": "", "schoolID": UCSB_ID, "fallback": True} 
        }
    }

def fetch_base_data():
    all_profs = []
    has_next_page, cursor = True, ""
    print("Stage 1: Fetching all professors (Fixing URLs and Limits)...")
    
    while has_next_page:
        resp = requests.post(API_URL, json=get_graphql_query(cursor), headers=HEADERS)
        data = resp.json()['data']['newSearch']['teachers']
        
        for edge in data['edges']:
            n = edge['node']
            
#fixed professors found
            try:
                raw_id = base64.b64decode(n['id']).decode('utf-8').split('-')[1]
                prof_url = f"https://www.ratemyprofessors.com/professor/{raw_id}"
            except:
                prof_url = "N/A"

            all_profs.append({
                'instructor': f"{n['lastName']}, {n['firstName']}".upper(),
                'rmp_rating': n['avgRating'],
                'rmp_difficulty': n['avgDifficulty'],
                'rmp_num_ratings': n['numRatings'],
                'rmp_take_again': f"{int(n['wouldTakeAgainPercent'])}%" if n['wouldTakeAgainPercent'] > 0 else "N/A",
                'rmp_url': prof_url,
                'rmp_dept': n['department'],
                'rmp_tags': "" 
            })
        
        has_next_page = data['pageInfo']['hasNextPage']
        cursor = data['pageInfo']['endCursor']
        print(f"Collected {len(all_profs)} professors...")
        time.sleep(1)
        
    return pd.DataFrame(all_profs).drop_duplicates(subset=['rmp_url'])

#playwrite
async def get_tags_for_row(browser, row_data, semaphore):
    async with semaphore:
        url = row_data['rmp_url']
        if url == "N/A" or (isinstance(row_data.get('rmp_tags'), str) and len(row_data['rmp_tags']) > 2):
            return row_data

        page = await browser.new_page()
        #optimize, disable images and fonts to speed up load times
        await page.route("**/*", lambda r: r.abort() if r.request.resource_type in ["image", "font"] else r.continue_())
        
        try:
            await page.goto(url, timeout=30000)
            #evaluate script in browser context to find all the unique tags elements that professors have under them
            unique_tags = await page.evaluate("""() => {
                const tagEls = document.querySelectorAll('[class*="Tag-"]');
                const tagsSet = new Set(Array.from(tagEls).map(t => t.innerText.trim()));
                return Array.from(tagsSet).join(", ");
            }""")
            row_data['rmp_tags'] = unique_tags if unique_tags else "None"
        except:
            row_data['rmp_tags'] = "None"
        finally:
            await page.close()
            return row_data

async def main():
    #stage 1 api collection
    df = fetch_base_data()
      #stage 2 of deep scraping with playwrite
    print(f"\nStage 2: Scraping Tags for {len(df)} professors...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(CONCURRENT_PAGES)
        
        rows = df.to_dict('records')
        for i in range(0, len(rows), 50):
            chunk = rows[i : i + 50]
            tasks = [get_tags_for_row(browser, r, semaphore) for r in chunk]
            rows[i : i + 50] = await asyncio.gather(*tasks)
            
            # save progress
            pd.DataFrame(rows).to_csv(CSV_FILE, index=False)
            print(f"💾 Saved chunk {i + len(chunk)}/{len(rows)}")
            
        await browser.close()
    print(f"Success! Total Professors saved: {len(rows)}")

if __name__ == "__main__":
    asyncio.run(main())
