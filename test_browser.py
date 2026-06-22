import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        errors = []
        page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(f"PAGE ERROR: {exc}"))
        
        print("Navigating to http://localhost:5174")
        await page.goto("http://localhost:5174", wait_until="networkidle")
        
        print("Filling textarea")
        await page.fill("textarea", "5 days Paris")
        
        print("Clicking submit")
        await page.click("button[type='submit']")
        
        print("Waiting a bit for transition...")
        await page.wait_for_timeout(3000)
        
        print("Errors caught:")
        for err in errors:
            print(err)
            
        await browser.close()

asyncio.run(run())
