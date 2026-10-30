import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

output_dir = Path("302-report/images")
output_dir.mkdir(parents=True, exist_ok=True)

async def capture_all_pages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("1. Capturing Sign-in Page...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        # Capture full card
        await page.screenshot(path=str(output_dir / "fig1_login_page.png"), full_page=False)

        print("2. Capturing Student Registration Page...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        reg_nav = page.locator("a:has-text('Student Registration')")
        if await reg_nav.count() > 0:
            await reg_nav.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(output_dir / "fig2_student_registration.png"), full_page=False)

        print("3. Logging into Admin Portal...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.locator("label:has-text('Admin')").click()
        await page.wait_for_timeout(500)
        inputs = await page.locator("input[type='text'], input[type='password']").all()
        if len(inputs) >= 2:
            await inputs[0].fill("admin")
            await inputs[1].fill("admin123")
        await page.locator("button:has-text('Continue')").click()
        await page.wait_for_timeout(4000)
        await page.screenshot(path=str(output_dir / "fig3_admin_overview.png"), full_page=False)

        print("4. Capturing Outbound Advisory & Attendance Dispatch Center...")
        dispatch_nav = page.locator("a:has-text('Recommendations & Predictions Dispatch')")
        if await dispatch_nav.count() > 0:
            await dispatch_nav.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(output_dir / "fig4_advisory_dispatch.png"), full_page=False)

            # Capture Tab 2 of Advisory Dispatch (Automated 6 PM scheduler)
            tab_daily = page.locator("button:has-text('Automated Daily 6:00 PM Dispatcher')")
            if await tab_daily.count() > 0:
                await tab_daily.first.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path=str(output_dir / "fig5_advisory_scheduler.png"), full_page=False)

            # Capture Tab 3 of Attendance Center
            tab_att = page.locator("button:has-text('Section Attendance Notification Center')")
            if await tab_att.count() > 0:
                await tab_att.first.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path=str(output_dir / "fig6_attendance_notifications.png"), full_page=False)

        print("5. Capturing Institutional Analytics...")
        analytics_nav = page.locator("a:has-text('Analytics')")
        if await analytics_nav.count() > 0:
            await analytics_nav.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(output_dir / "fig7_institutional_analytics.png"), full_page=False)

        print("6. Capturing Student Approvals Page...")
        approvals_nav = page.locator("a:has-text('Student Approvals')")
        if await approvals_nav.count() > 0:
            await approvals_nav.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(output_dir / "fig8_student_approvals.png"), full_page=False)

        print("7. Capturing Reports Engine...")
        reports_nav = page.locator("a:has-text('Reports')")
        if await reports_nav.count() > 0:
            await reports_nav.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=str(output_dir / "fig9_reports_engine.png"), full_page=False)

        print("8. Logging into Faculty Portal...")
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
        await page.screenshot(path=str(output_dir / "fig10_faculty_marks_entry.png"), full_page=False)

        # Capturing Classroom Attendance Register tab
        fac_att_tab = page.locator("button:has-text('Session Attendance')")
        if await fac_att_tab.count() > 0:
            await fac_att_tab.first.click()
            await page.wait_for_timeout(2500)
            await page.screenshot(path=str(output_dir / "fig11_faculty_attendance_register.png"), full_page=False)

        # Capturing At-Risk Student Detection tab
        fac_risk_tab = page.locator("button:has-text('At-Risk Student Detection')")
        if await fac_risk_tab.count() > 0:
            await fac_risk_tab.first.click()
            await page.wait_for_timeout(2500)
            await page.screenshot(path=str(output_dir / "fig12_faculty_at_risk_detection.png"), full_page=False)

        print("9. Logging into Student Portal...")
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
        await page.screenshot(path=str(output_dir / "fig13_student_dashboard_overview.png"), full_page=False)

        # Scroll down student dashboard to capture CIE performance & recommendations
        await page.evaluate("window.scrollBy(0, 600)")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(output_dir / "fig14_student_academic_advisory.png"), full_page=False)

        await browser.close()
        print("Successfully captured 14 comprehensive system screenshots in 302-report/images!")

if __name__ == "__main__":
    asyncio.run(capture_all_pages())
