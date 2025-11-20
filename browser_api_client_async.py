#!/usr/bin/env python3.11
"""
Hybrid Browser-based API client using Playwright + curl_cffi
Uses browser for session establishment and cookie extraction
Uses curl_cffi.requests for POST with Chrome TLS fingerprint impersonation
"""
from playwright.async_api import async_playwright
import json
import asyncio
import threading
from concurrent.futures import Future
from curl_cffi import requests


class AsyncBrowserAPIClient:
    """
    Async API client using real Chrome browser
    """

    def __init__(self, playwright_instance, headless=False):
        """
        Initialize browser (async)
        Args:
            playwright_instance: The async playwright instance
            headless: False = visible browser (better for bypassing detection)
        """
        self.playwright = playwright_instance
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

        # Hybrid approach: browser for session, curl_cffi for POST with Chrome TLS
        # curl_cffi impersonates Chrome's TLS fingerprint to bypass Vercel detection
        self.session = requests.Session(impersonate="chrome120")  # Chrome 120 TLS fingerprint
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
        })

        # COOKIE INJECTION: Load cookies from file if available (bypasses MAXIMUM bot detection)
        self._load_injected_cookies()

        self.last_submit_time = 0  # Track last submission for rate limiting
        self.last_cookie_refresh = 0  # Track last cookie refresh
        self.submission_count = 0  # Count submissions since last refresh

    def _load_injected_cookies(self):
        """Load cookies from .browser_cookies file to bypass Vercel/Cloudflare protection"""
        import os
        cookie_file = '.browser_cookies'

        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookie_string = f.read().strip()

                if cookie_string:
                    # Parse cookie string and set individual cookies in session
                    # Format: "name1=value1; name2=value2; name3=value3"
                    for cookie_pair in cookie_string.split('; '):
                        if '=' in cookie_pair:
                            name, value = cookie_pair.split('=', 1)
                            self.session.cookies.set(
                                name=name,
                                value=value,
                                domain='.midnight.gd',
                                path='/',
                            )

                    # ALSO set as Cookie header for maximum compatibility
                    self.session.headers.update({'Cookie': cookie_string})

                    print(f"  [Cookie Injection] ✓ Loaded cookies from {cookie_file}")
                    print(f"  [Cookie Injection] ✓ Using REAL browser cookies - bot detection bypassed")
                    return True
            except Exception as e:
                print(f"  [Cookie Injection] ✗ Failed to load cookies: {e}")

        print(f"  [Cookie Injection] ℹ No cookie file found - will use browser cookies")
        print(f"  [Cookie Injection] ℹ To bypass maximum protection:")
        print(f"  [Cookie Injection] ℹ   1. Open https://sm.midnight.gd in browser")
        print(f"  [Cookie Injection] ℹ   2. F12 → Console → Type: copy(document.cookie)")
        print(f"  [Cookie Injection] ℹ   3. Paste into: {cookie_file}")
        return False

    async def start(self):
        """Start the browser"""
        # Launch Chromium with settings to avoid detection
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        # Create context with real browser settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

        # Create page
        self.page = await self.context.new_page()

        # Hide webdriver property (anti-detection)
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # CRITICAL: Visit main site first to establish session with Vercel
        # This sets up cookies and browser fingerprint
        try:
            await self.page.goto('https://sm.midnight.gd/', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)  # Let session establish

            # Extract cookies from browser and copy to requests.Session
            await self._extract_cookies()

            import time
            self.last_cookie_refresh = time.time()
        except:
            pass  # If main site fails, continue - API might still work

        return self

    async def _extract_cookies(self):
        """Extract cookies from browser context and copy to requests.Session"""
        try:
            # Get cookies from browser context
            cookies = await self.context.cookies()

            # Clear old cookies from session
            self.session.cookies.clear()

            # Copy cookies to requests.Session
            for cookie in cookies:
                self.session.cookies.set(
                    name=cookie['name'],
                    value=cookie['value'],
                    domain=cookie.get('domain', 'sm.midnight.gd'),
                    path=cookie.get('path', '/'),
                )

            print(f"  [Cookie Refresh] Extracted {len(cookies)} cookies from browser")
        except Exception as e:
            print(f"  [Cookie Refresh] Failed to extract cookies: {e}")

    async def refresh_cookies(self):
        """Refresh browser session and cookies by revisiting main site"""
        try:
            import time
            await self.page.goto('https://sm.midnight.gd/', wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(0.5)

            # Re-extract cookies
            await self._extract_cookies()

            self.last_cookie_refresh = time.time()
            self.submission_count = 0
        except Exception as e:
            print(f"  [Cookie Refresh] Failed: {e}")

    async def get_challenge(self):
        """
        Fetch challenge from API
        Returns: dict with challenge data or None
        """
        try:
            # Navigate to API endpoint
            response = await self.page.goto(
                'https://sm.midnight.gd/api/challenge',
                wait_until='networkidle',
                timeout=30000
            )

            # Check if we got blocked - retry once on 429
            if response.status == 429:
                await asyncio.sleep(5)
                response = await self.page.goto(
                    'https://sm.midnight.gd/api/challenge',
                    wait_until='networkidle',
                    timeout=30000
                )

            # After retry, check status
            if response.status != 200:
                return None

            # Get page content and parse JSON
            try:
                pre = await self.page.query_selector('pre')
                if pre:
                    json_text = await pre.inner_text()
                    data = json.loads(json_text)
                    return data

                body = await self.page.query_selector('body')
                if body:
                    json_text = await body.inner_text()
                    data = json.loads(json_text)
                    return data

            except Exception:
                return None

        except Exception:
            return None

    def _wait_for_global_rate_limit(self):
        """
        Thread-safe global rate limiter - ensures minimum delay between ANY submissions from server
        This runs synchronously in executor to properly handle threading locks
        """
        import time
        with AsyncBrowserPool._global_submit_lock:
            current_time = time.time()
            time_since_last = current_time - AsyncBrowserPool._global_last_submit

            if time_since_last < AsyncBrowserPool.GLOBAL_SUBMIT_DELAY:
                wait_time = AsyncBrowserPool.GLOBAL_SUBMIT_DELAY - time_since_last
                print(f"[Global Rate Limit] Waiting {wait_time:.1f}s before submission...")
                time.sleep(wait_time)

            AsyncBrowserPool._global_last_submit = time.time()

    async def submit_solution(self, address, challenge_id, nonce):
        """
        Submit solution to API using Playwright's page.request API
        This sends ALL browser headers automatically, bypassing Vercel detection
        Returns: dict with status and data, or error status
        """
        try:
            import time

            # Cookie refresh: every 50 submissions OR every 5 minutes
            # Browser revisits site to refresh cookies and prevent stale sessions
            current_time = time.time()
            time_since_refresh = current_time - self.last_cookie_refresh
            if self.submission_count >= 50 or time_since_refresh >= 300:
                await self.refresh_cookies()

            # GLOBAL rate limiting: Ensure minimum delay between ANY submissions from entire server
            # This prevents bursts of simultaneous submissions from triggering IP-based rate limits
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._wait_for_global_rate_limit)

            # Per-browser rate limiting: ensure at least 10s between submissions per browser
            # This prevents multiple workers on same browser from triggering 429s
            time_since_last = current_time - self.last_submit_time
            if time_since_last < 10.0:
                await asyncio.sleep(10.0 - time_since_last)

            self.last_submit_time = time.time()
            self.submission_count += 1

            url = f'https://sm.midnight.gd/api/solution/{address}/{challenge_id}/{nonce}'

            # Use page.evaluate with fetch() - this executes in the REAL browser context
            # with all cookies, headers, and JavaScript state exactly like a real user
            response_data = await self.page.evaluate('''async (url) => {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/plain, */*',
                    },
                    body: JSON.stringify({})
                });

                const status = response.status;
                let data = null;

                try {
                    const text = await response.text();
                    if (text) {
                        data = JSON.parse(text);
                    }
                } catch (e) {
                    // Non-JSON response, that's ok
                }

                return { status, data };
            }''', url)

            status = response_data['status']

            # Parse response based on status
            if status in [200, 201]:
                return {'status': 'accepted', 'data': response_data.get('data')}
            elif status == 429:
                return {'status': 'failed', 'code': 429}
            elif status == 400:
                return {'status': 'failed', 'code': 400}
            elif status == 404:
                return {'status': 'failed', 'code': 404}
            elif status == 504:
                return {'status': 'failed', 'code': 504}
            else:
                return {'status': 'failed', 'code': status}

        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

    async def close(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except:
            pass


class AsyncBrowserPool:
    """
    Thread-safe async browser pool that runs in dedicated event loop
    Workers can call sync methods from any thread
    """

    # GLOBAL rate limiter shared across ALL browser pool instances
    _global_last_submit = 0
    _global_submit_lock = threading.Lock()
    GLOBAL_SUBMIT_DELAY = 10.0  # Minimum seconds between ANY submissions from this server (increased due to site-wide rate limiting)

    def __init__(self, num_browsers=1, headless=False):
        """
        Initialize async browser pool
        Args:
            num_browsers: Number of browser instances
            headless: Whether to run headless
        """
        self.num_browsers = num_browsers
        self.headless = headless
        self.browsers = []
        self.current_index = 0
        self.lock = asyncio.Lock()

        # Event loop runs in dedicated thread
        self.loop = None
        self.thread = None
        self.playwright = None
        self.ready = threading.Event()
        self.shutdown = False

        print(f"Initializing async browser pool with {num_browsers} browser(s)...")

        # Start event loop in dedicated thread
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

        # Wait for initialization
        self.ready.wait(timeout=30)
        print(f"✓ Async browser pool ready")

    def _run_event_loop(self):
        """Run event loop in dedicated thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Initialize browsers
        self.loop.run_until_complete(self._initialize_browsers())

        # Signal ready
        self.ready.set()

        # Keep loop running
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    async def _initialize_browsers(self):
        """Initialize all browser instances (async)"""
        self.playwright = await async_playwright().start()

        for i in range(self.num_browsers):
            browser = AsyncBrowserAPIClient(self.playwright, headless=self.headless)
            await browser.start()
            self.browsers.append(browser)
            print(f"  Browser {i+1}/{self.num_browsers} ready")

    async def _get_next_browser(self):
        """Get next browser in round-robin (async, with lock)"""
        async with self.lock:
            browser = self.browsers[self.current_index]
            self.current_index = (self.current_index + 1) % self.num_browsers
            return browser

    def _run_async(self, coro):
        """
        Run async coroutine from sync context
        Returns: Future that will contain the result
        """
        if self.shutdown:
            raise RuntimeError("Browser pool is shut down")

        future = Future()

        def callback():
            try:
                task = asyncio.ensure_future(coro, loop=self.loop)
                task.add_done_callback(lambda t: future.set_result(t.result()) if not t.exception() else future.set_exception(t.exception()))
            except Exception as e:
                future.set_exception(e)

        self.loop.call_soon_threadsafe(callback)
        return future

    # Sync methods for workers to call

    def get_challenge(self):
        """Fetch challenge (sync wrapper for async method)"""
        async def _do_get_challenge():
            browser = await self._get_next_browser()
            return await browser.get_challenge()

        future = self._run_async(_do_get_challenge())
        return future.result(timeout=45)  # Wait up to 45 seconds

    def submit_solution(self, address, challenge_id, nonce):
        """Submit solution (sync wrapper for async method)"""
        async def _do_submit_solution():
            browser = await self._get_next_browser()
            return await browser.submit_solution(address, challenge_id, nonce)

        future = self._run_async(_do_submit_solution())
        try:
            return future.result(timeout=180)  # 3 minute timeout for global rate limiting
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"{type(e).__name__}: {str(e) if str(e) else 'No error message'}")

    def close_all(self):
        """Close all browsers (sync)"""
        if self.shutdown:
            return

        async def _do_close_all():
            for i, browser in enumerate(self.browsers):
                try:
                    await browser.close()
                    print(f"  Browser {i+1} closed")
                except Exception as e:
                    print(f"  Error closing browser {i+1}: {e}")

            if self.playwright:
                await self.playwright.stop()

        if self.loop and self.loop.is_running():
            future = self._run_async(_do_close_all())
            try:
                future.result(timeout=10)
            except:
                pass

            # Set shutdown flag AFTER closing
            self.shutdown = True
            self.loop.call_soon_threadsafe(self.loop.stop)


def test():
    """Test the async browser pool"""
    print("="*80)
    print("Testing Async Browser Pool")
    print("="*80)

    # Create pool
    pool = AsyncBrowserPool(num_browsers=1, headless=False)

    print("\n1. Fetching challenge...")
    challenge = pool.get_challenge()

    if challenge and 'challenge' in challenge and challenge.get('code') == 'active':
        print(f"\n✅ SUCCESS! Got challenge:")
        print(f"   Challenge ID: {challenge['challenge']['challenge_id']}")
        print(f"   Difficulty: {challenge['challenge']['difficulty']}")
        print(f"   Challenge Number: {challenge['challenge']['challenge_number']}")
        print(f"\n✅ Async browser pool works!")
    else:
        print(f"\n❌ Failed to get challenge")
        print(f"   Response: {challenge}")

    pool.close_all()

    print("\n" + "="*80)
    print("✓ Test complete - ready for production use")
    print("="*80)


if __name__ == '__main__':
    test()
