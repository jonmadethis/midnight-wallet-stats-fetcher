#!/usr/bin/env python3.11
"""
Fetch wallet statistics from Midnight API using AsyncBrowserAPIClient
Uses the same bypass technique as the miners

Usage:
    python3.11 fetch_wallet_stats.py <wallet_file> [start_index] [batch_size]

Example:
    python3.11 fetch_wallet_stats.py wallets.json 0 100
"""
import json
import asyncio
import sys
import os
from browser_api_client_async import AsyncBrowserPool

async def fetch_wallet_stats_with_browser(pool, address):
    """Fetch statistics for a single wallet using browser pool"""
    try:
        # Use the browser pool's async method directly
        from concurrent.futures import Future

        # Create async task to fetch via browser
        async def _fetch():
            browser = await pool._get_next_browser()

            # Navigate to statistics page
            url = f'https://scavenger.prod.gd.midnighttge.io/statistics/{address}'

            # Set extra headers to bypass Vercel protection
            await browser.page.set_extra_http_headers({
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Upgrade-Insecure-Requests': '1',
            })

            response = await browser.page.goto(url, wait_until='networkidle', timeout=15000)

            # Debug: print first response status
            if not hasattr(_fetch, '_status_printed'):
                print(f"  [Debug] Status: {response.status} for {address[:20]}...")
                _fetch._status_printed = True

            if response.status != 200:
                return {'address': address, 'solutions': 0, 'night': 0}

            # Parse JSON
            try:
                pre = await browser.page.query_selector('pre')
                if pre:
                    json_text = await pre.inner_text()
                    data = json.loads(json_text)

                    # Extract stats
                    local = data.get('local', {})
                    solutions = local.get('crypto_receipts', 0)
                    night_raw = local.get('night_allocation', 0)
                    night = night_raw / 1_000_000

                    return {
                        'address': address,
                        'solutions': solutions,
                        'night': night
                    }
                else:
                    # No <pre> tag found, try getting body text
                    body = await browser.page.query_selector('body')
                    if body:
                        json_text = await body.inner_text()
                        data = json.loads(json_text)

                        # Extract stats
                        local = data.get('local', {})
                        solutions = local.get('crypto_receipts', 0)
                        night_raw = local.get('night_allocation', 0)
                        night = night_raw / 1_000_000

                        return {
                            'address': address,
                            'solutions': solutions,
                            'night': night
                        }
            except Exception as e:
                # Debug: print first error to see what's going wrong
                if not hasattr(fetch_wallet_stats_with_browser, '_error_printed'):
                    print(f"  [Debug] Parse error: {e}")
                    fetch_wallet_stats_with_browser._error_printed = True

            return {'address': address, 'solutions': 0, 'night': 0}

        # Run the fetch
        future = pool._run_async(_fetch())
        return future.result(timeout=30)

    except Exception as e:
        print(f"  Error fetching {address[:20]}...: {e}")
        return {'address': address, 'solutions': 0, 'night': 0}

def main():
    """Main function to fetch all wallet statistics in batches"""
    # Check for required arguments
    if len(sys.argv) < 2:
        print("Usage: python3.11 fetch_wallet_stats.py <wallet_file> [start_index] [batch_size]")
        print("\nExample:")
        print("  python3.11 fetch_wallet_stats.py wallets.json 0 100")
        sys.exit(1)

    wallet_file = sys.argv[1]
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    # Check if wallet file exists
    if not os.path.exists(wallet_file):
        print(f"Error: Wallet file '{wallet_file}' not found")
        sys.exit(1)

    print(f"Loading wallets from {wallet_file}...")

    try:
        with open(wallet_file, 'r') as f:
            wallets = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in wallet file: {e}")
        sys.exit(1)

    print(f"Found {len(wallets)} wallets")
    print(f"Processing batch: wallets {start_index} to {min(start_index + batch_size, len(wallets))}")

    # Slice wallets for this batch
    batch_wallets = wallets[start_index:start_index + batch_size]

    if not batch_wallets:
        print("No wallets to process in this batch")
        return

    # Create browser pool with 3 browsers for faster fetching
    print("Starting browser pool...")
    pool = AsyncBrowserPool(num_browsers=3, headless=True)

    print(f"\nFetching statistics for {len(batch_wallets)} wallets...")
    wallet_stats = []
    successful = 0

    for i, wallet in enumerate(batch_wallets):
        # Support both {'address': '...'} and plain string formats
        address = wallet if isinstance(wallet, str) else wallet['address']
        global_index = start_index + i

        # Fetch stats using browser pool
        stats = asyncio.run(fetch_wallet_stats_with_browser(pool, address))
        wallet_stats.append(stats)

        if stats['solutions'] > 0 or stats['night'] > 0:
            successful += 1
            print(f"  ✓ {address[:20]}... - {stats['solutions']} solutions, {stats['night']:.4f} NIGHT")

        if (i + 1) % 10 == 0:
            print(f"  Progress: {global_index + 1}/{len(wallets)} ({successful} with earnings)")

        # Rate limiting
        if (i + 1) % 5 == 0:
            asyncio.run(asyncio.sleep(1))

    # Close browser pool
    pool.close_all()

    # Save results for this batch
    output_file = f'wallet_stats_batch_{start_index}_{start_index + len(batch_wallets)}.json'
    with open(output_file, 'w') as f:
        json.dump(wallet_stats, f, indent=2)

    total_solutions = sum(w['solutions'] for w in wallet_stats)
    total_night = sum(w['night'] for w in wallet_stats)

    print(f"\n✓ Batch statistics saved to {output_file}")
    print(f"  Wallets with earnings: {successful}/{len(batch_wallets)}")
    print(f"  Total Solutions: {total_solutions}")
    print(f"  Total NIGHT: {total_night:.4f}")
    print(f"\nTo process next batch, run:")
    print(f"  xvfb-run -a python3.11 fetch_wallet_stats.py {wallet_file} {start_index + batch_size} {batch_size}")

if __name__ == '__main__':
    main()
