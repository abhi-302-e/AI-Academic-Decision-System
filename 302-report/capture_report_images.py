import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

output_dir = Path("302-report/images")
output_dir.mkdir(parents=True, exist_ok=True)

async def capture_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("1. Capturing Sign-In Page...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(output_dir / "fig1_login_page.png"), full_page=False)

        print("2. Logging into Admin Portal...")
        # Select Admin radio
        await page.locator("label:has-text('Admin')").click()
        await page.wait_for_timeout(500)
        # Fill credentials
        inputs = await page.locator("input[type='text'], input[type='password']").all()
        if len(inputs) >= 2:
            await inputs[0].fill("admin")
            await inputs[1].fill("admin123")
        await page.locator("button:has-text('Continue')").click()
        await page.wait_for_timeout(4000)
        await page.screenshot(path=str(output_dir / "fig2_admin_dashboard.png"), full_page=False)

        print("3. Capturing Recommendations & Predictions Dispatch...")
        dispatch_nav = page.locator("span:has-text('Recommendations & Predictions Dispatch'), a:has-text('Recommendations & Predictions Dispatch')")
        if await dispatch_nav.count() > 0:
            await dispatch_nav.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(output_dir / "fig3_advisory_dispatch.png"), full_page=False)

        print("4. Capturing Analytics Page...")
        analytics_nav = page.locator("span:has-text('Analytics'), a:has-text('Analytics')")
        if await analytics_nav.count() > 0:
            await analytics_nav.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(output_dir / "fig4_analytics.png"), full_page=False)

        print("5. Logging into Faculty Portal...")
        # Clear cookies/state for fresh login
        await context.clear_cookies()
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.locator("label:has-text('Faculty')").click()
        await page.wait_for_timeout(500)
        inputs = await page.locator("input[type='text'], input[type='password']").all()
        if len(inputs) >= 2:
            await inputs[0].fill("SCHED0001")
            await inputs[1].fill("faculty@123")
        await page.locator("button:has-text('Continue')").click()
        await page.wait_for_timeout(4000)
        await page.screenshot(path=str(output_dir / "fig5_faculty_marks_entry.png"), full_page=False)

        print("6. Logging into Student Portal...")
        await context.clear_cookies()
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.locator("label:has-text('Student')").click()
        await page.wait_for_timeout(500)
        inputs = await page.locator("input[type='text'], input[type='password']").all()
        if len(inputs) >= 2:
            await inputs[0].fill("26STU0001")
            await inputs[1].fill("student@123")
        await page.locator("button:has-text('Continue')").click()
        await page.wait_for_timeout(4000)
        await page.screenshot(path=str(output_dir / "fig6_student_dashboard.png"), full_page=False)

        await browser.close()
        print("All screenshots captured successfully in 302-report/images!")

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
