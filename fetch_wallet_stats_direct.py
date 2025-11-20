#!/usr/bin/env python3.11
"""
Fetch wallet statistics using curl_cffi (TLS fingerprint impersonation)
Bypasses Vercel protection without needing a full browser

This is the faster, simpler method that doesn't require X11/Xvfb.

Usage:
    python3.11 fetch_wallet_stats_direct.py <wallet_file> [start_index] [batch_size]

Example:
    python3.11 fetch_wallet_stats_direct.py wallets.json 0 100
"""
import json
import sys
import os
from curl_cffi import requests

def fetch_wallet_stats(address):
    """Fetch statistics for a single wallet"""
    try:
        # Use curl_cffi with Chrome TLS fingerprint impersonation
        session = requests.Session(impersonate="chrome120")

        # CRITICAL: API blocks Chrome user-agent but allows curl
        headers = {
            'User-Agent': 'curl/7.81.0',
            'Accept': '*/*'
        }

        url = f'https://scavenger.prod.gd.midnighttge.io/statistics/{address}'

        response = session.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return {'address': address, 'solutions': 0, 'night': 0}

        data = response.json()

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
        return {'address': address, 'solutions': 0, 'night': 0, 'error': str(e)}

def main():
    """Main function to fetch wallet statistics in batches"""
    # Check for required arguments
    if len(sys.argv) < 2:
        print("Usage: python3.11 fetch_wallet_stats_direct.py <wallet_file> [start_index] [batch_size]")
        print("\nExample:")
        print("  python3.11 fetch_wallet_stats_direct.py wallets.json 0 100")
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

    print(f"\nFetching statistics for {len(batch_wallets)} wallets...")
    wallet_stats = []
    successful = 0

    for i, wallet in enumerate(batch_wallets):
        # Support both {'address': '...'} and plain string formats
        address = wallet if isinstance(wallet, str) else wallet['address']
        global_index = start_index + i

        # Fetch stats
        stats = fetch_wallet_stats(address)
        wallet_stats.append(stats)

        if stats['solutions'] > 0 or stats['night'] > 0:
            successful += 1
            print(f"  ✓ {address[:20]}... - {stats['solutions']} solutions, {stats['night']:.4f} NIGHT")

        if (i + 1) % 10 == 0:
            print(f"  Progress: {global_index + 1}/{len(wallets)} ({successful} with earnings)")

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
    print(f"  python3.11 fetch_wallet_stats_direct.py {wallet_file} {start_index + batch_size} {batch_size}")

if __name__ == '__main__':
    main()
