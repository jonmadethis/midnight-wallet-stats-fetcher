# THIS SCRIPT IS NO LONGER FUNCTIONING. THE MIDNIGHT SCAVENGER MINE HAS ENDED. YOU CAN PROBABLY USE IT AS A REFERENCE FOR OTHER MIDNIGHT SCAVENGER MINE CLONES


# Midnight Wallet Statistics Fetcher

Fetch wallet statistics from the Midnight Scavenger Hunt API. This is a standalone, distributable package that works on any system.

## Two Methods Available

1. **fetch_wallet_stats_direct.py** - Fast method using curl_cffi (recommended)
2. **fetch_wallet_stats.py** - Browser-based method using Playwright (slower, more robust)

## System Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **Operating System**: Linux, macOS, or Windows
- **RAM**: 512MB minimum (2GB+ recommended for browser method)
- **Disk Space**: 500MB for dependencies

### Additional Requirements for Browser Method
- **Xvfb**: Required on headless Linux servers (for virtual display)
  - Ubuntu/Debian: `sudo apt-get install xvfb`
  - CentOS/RHEL: `sudo yum install xorg-x11-server-Xvfb`
  - Not needed on desktop systems or macOS

## Quick Start (Automated Setup)

Run the automated setup script:

```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. Check Python version
2. Install all Python dependencies
3. Install Playwright browsers
4. Verify Xvfb availability (for headless servers)

## Manual Installation

If you prefer manual installation or the setup script fails:

### Step 1: Install Python Dependencies

```bash
pip3.11 install -r requirements.txt
```

This installs:
- `curl-cffi` - For the direct method (TLS fingerprint impersonation)
- `playwright` - For the browser method (full browser automation)

### Step 2: Install Playwright Browsers (Browser Method Only)

```bash
python3.11 -m playwright install chromium
```

### Step 3: Install Xvfb (Headless Servers Only)

Only needed if running the browser method on a server without a display:

```bash
# Ubuntu/Debian
sudo apt-get install xvfb

# CentOS/RHEL
sudo yum install xorg-x11-server-Xvfb
```

## Package Contents

This package includes all necessary files:

- `fetch_wallet_stats_direct.py` - Fast curl_cffi implementation
- `fetch_wallet_stats.py` - Browser-based implementation
- `browser_api_client_async.py` - Browser automation library (dependency)
- `example_wallets.json` - Example wallet file template
- `requirements.txt` - Python dependencies
- `setup.sh` - Automated installation script
- `README.md` - This file

## Wallet File Format

Create a JSON file with your wallet addresses. Two formats are supported:

### Format 1: Array of Objects (recommended)
```json
[
  {
    "address": "addr11234567890123456789012345678901234567890"
  },
  {
    "address": "addr1abcdefabcdefabcdefabcdefabcdefabcdefabcd"
  }
]
```

### Format 2: Array of Strings
```json
[
  "addr11234567890123456789012345678901234567890",
  "addr1abcdefabcdefabcdefabcdefabcdefabcdefabcd"
]
```

See `example_wallets.json` for a template.

## Usage

### Direct Method (Fast)

Fetch statistics for all wallets:
```bash
python3.11 fetch_wallet_stats_direct.py wallets.json
```

Fetch statistics in batches:
```bash
# Process wallets 0-99
python3.11 fetch_wallet_stats_direct.py wallets.json 0 100

# Process wallets 100-199
python3.11 fetch_wallet_stats_direct.py wallets.json 100 100

# Process wallets 200-299
python3.11 fetch_wallet_stats_direct.py wallets.json 200 100
```

### Browser Method (Slower, More Robust)

Requires X11 display server (use xvfb-run on headless servers):

```bash
# On systems with display
python3.11 fetch_wallet_stats.py wallets.json

# On headless servers
xvfb-run -a python3.11 fetch_wallet_stats.py wallets.json

# Process in batches
xvfb-run -a python3.11 fetch_wallet_stats.py wallets.json 0 100
```

## Command Line Arguments

```
python3.11 fetch_wallet_stats_direct.py <wallet_file> [start_index] [batch_size]
```

- **wallet_file** (required): Path to JSON file containing wallet addresses
- **start_index** (optional): Index of first wallet to process (default: 0)
- **batch_size** (optional): Number of wallets to process (default: 100)

## Output

The script creates a batch output file:
```
wallet_stats_batch_<start>_<end>.json
```

Example output format:
```json
[
  {
    "address": "addr11234567890123456789012345678901234567890",
    "solutions": 42,
    "night": 123.4567
  },
  {
    "address": "addr1abcdefabcdefabcdefabcdefabcdefabcdefabcd",
    "solutions": 0,
    "night": 0
  }
]
```

The script displays progress and a summary:
```
✓ Batch statistics saved to wallet_stats_batch_0_100.json
  Wallets with earnings: 15/100
  Total Solutions: 1234
  Total NIGHT: 5678.9012
```

## Processing Large Wallet Lists

For large lists, process in batches to avoid rate limiting:

```bash
# Process 500 wallets in 5 batches of 100
for i in 0 100 200 300 400; do
    python3.11 fetch_wallet_stats_direct.py wallets.json $i 100
    sleep 5
done
```

## Troubleshooting

### Direct Method Issues

If you get 403 errors:
- The API may have changed its protection
- Try the browser method instead

### Browser Method Issues

If you get display errors:
- Use `xvfb-run -a` on headless servers
- Ensure Playwright is installed: `playwright install chromium`

### Rate Limiting

If you're getting timeouts or errors:
- Reduce batch size (e.g., 50 instead of 100)
- Add delays between batches
- The browser method includes automatic rate limiting

## Distribution

This package is completely self-contained and can be distributed as-is. Simply:

1. Copy the entire `wallet-stats` directory to any system
2. Run `./setup.sh` to install dependencies
3. Create your wallet file and start fetching statistics

No additional files or configuration needed!

## API Endpoint

The scripts query:
```
https://scavenger.prod.gd.midnighttge.io/statistics/{address}
```

Response includes:
- `local.crypto_receipts` - Number of solutions submitted
- `local.night_allocation` - NIGHT tokens earned (in stars, night divided by 1,000,000)
