import argparse
import asyncio
import os
from playwright.async_api import async_playwright
from utils_dates import parse_date_from_page, within_range, parse_cli_date
from utils_files import (
    ensure_directories,
    load_config,
    load_all_postliste,
    merge_and_save_sharded,
    atomic_write,
)
from scraper_core_async import hent_side_async

DEFAULT_CONFIG_FILE = "../config/config.json"
FILTERED_FILE = "../../data/postliste_filtered.json"


async def scrape_single_page(context, page_num, per_page, start_date, end_date, semaphore, index, total_pages):
    """
    Scraper én side i egen page (SPA-sikker), filtrerer på dato-range og returnerer liste med dokumenter.
    Logger også progress: 'Scraper side X av Y'.
    """
    print(f"[INFO] Scraper side {index} av {total_pages} (page_num={page_num})")

    async with semaphore:
        page = await context.new_page()
        try:
            docs = await hent_side_async(
                page_num=page_num,
                page=page,
                per_page=per_page,
                timeout=10_000,
                retries=5,
            )
        finally:
            await page.close()

        if not docs:
            print(f"[INFO] Ingen dokumenter (eller feil) på side {page_num}")
            return []

        filtered = []
        for d in docs:
            parsed_date = parse_date_from_page(d.get("dato"))
            if within_range(parsed_date, start_date, end_date):
                filtered.append(d)

        print(f"[INFO] Side {page_num}: {len(filtered)} dokumenter innenfor dato-range")
        return filtered


async def run_scrape_async(start_date=None, end_date=None, config_path=DEFAULT_CONFIG_FILE, mode="publish"):
    print(f"[INFO] Starter ASYNC PARALLELL scraper_dates i modus='{mode}'…")

    ensure_directories()
    cfg = load_config(config_path)

    start_page = int(cfg.get("start_page", 1))
    max_pages = int(cfg.get("max_pages", 100))
    per_page = int(cfg.get("per_page", 100))
    step = 1 if max_pages > start_page else -1

    # Antall sider som faktisk skal scrapes
    total_pages = abs(max_pages - start_page) + 1

    print("[INFO] Konfigurasjon:")
    print(f"       start_page  = {start_page}")
    print(f"       max_pages   = {max_pages}")
    print(f"       step        = {step}")
    print(f"       total_pages = {total_pages}")
    print(f"       per_page    = {per_page}")
    print(f"       start_date  = {start_date}")
    print(f"       end_date    = {end_date}")

    all_docs = []

    # Dynamisk concurrency basert på CPU
    cpu_count = os.cpu_count() or 2
    # Litt konservativ: ikke mer enn 8, ikke mindre enn 2, og ikke over (cpu_count - 1)
    CONCURRENCY = min(8, max(2, cpu_count - 1))

    print(f"[INFO] CPU-kjerner: {cpu_count}, bruker CONCURRENCY={CONCURRENCY}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
            ],
        )

        context = await browser.new_context()

        # Resource-blocking: behold CSS/JS, blokker kun tunge ting
        async def block_resources(route):
            if route.request.resource_type in ["image", "media"]:
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_resources)

        semaphore = asyncio.Semaphore(CONCURRENCY)

        tasks = []
        # Vi vil ha stabil index 1..total_pages uavhengig av step-retning
        for idx, page_num in enumerate(range(start_page, max_pages + step, step), start=1):
            tasks.append(
                scrape_single_page(
                    context=context,
                    page_num=page_num,
                    per_page=per_page,
                    start_date=start_date,
                    end_date=end_date,
                    semaphore=semaphore,
                    index=idx,
                    total_pages=total_pages,
                )
            )

        # Kjør alle sidene parallelt
        results = await asyncio.gather(*tasks)

        # Flatten resultatene
        for batch in results:
            all_docs.extend(batch)

        await context.close()
        await browser.close()

    print(f"[INFO] Totalt hentet {len(all_docs)} dokumenter innenfor dato-range.")
    atomic_write(FILTERED_FILE, all_docs)

    if mode == "publish":
        existing_dict, _ = load_all_postliste()
        merge_and_save_sharded(existing_dict, all_docs)
        print("[INFO] Oppdatert shard-basert hoveddatasett.")
    else:
        print("[INFO] FULL-modus: Oppdaterer ikke hoveddatasettet")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG_FILE)
    parser.add_argument("--mode", default="publish", choices=["full", "publish"])
    parser.add_argument("start_date", nargs="?")
    parser.add_argument("end_date", nargs="?")

    args = parser.parse_args()

    start_date = parse_cli_date(args.start_date) if args.start_date else None
    end_date = parse_cli_date(args.end_date) if args.end_date else start_date

    asyncio.run(
        run_scrape_async(
            start_date=start_date,
            end_date=end_date,
            config_path=args.config,
            mode=args.mode,
        )
    )


if __name__ == "__main__":
    main()
