# utils_playwright_async.py

async def safe_text(element, selector):
    """
    Async versjon av safe_text:
    - bruker await element.query_selector
    - bruker await handle.inner_text
    """
    try:
        handle = await element.query_selector(selector)
        if not handle:
            return ""
        txt = await handle.inner_text()
        return txt.strip() if txt else ""
    except Exception:
        return ""


async def safe_goto(page, url, retries=3, timeout=10000):
    """
    Async versjon av safe_goto:
    - bruker await page.goto
    - retry ved feil
    """
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"[WARN] safe_goto feilet (forsøk {attempt}/{retries}): {e}")
            await page.wait_for_timeout(300)

    return False
