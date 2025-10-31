"""Browser orchestration using Playwright."""
from playwright.sync_api import sync_playwright, Page, Browser as PWBrowser, BrowserContext
import os
import time
from typing import Optional, Dict, List


class Browser:
    """Playwright-based browser automation wrapper."""
    
    def __init__(self, headless: bool = True, timeout_ms: int = 12000, record_har: bool = False):
        """Initialize browser configuration.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout_ms: Default timeout in milliseconds
            record_har: Whether to record HAR file
        """
        self.headless = headless
        self.timeout = timeout_ms
        self.record_har = record_har
        self.pw = None
        self.browser: Optional[PWBrowser] = None
        self.ctx: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.har_path: Optional[str] = None

    def __enter__(self):
        """Start browser context."""
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=self.headless)
        
        ctx_options = {}
        if self.record_har and self.har_path:
            ctx_options['record_har_path'] = self.har_path
            
        self.ctx = self.browser.new_context(**ctx_options)
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(self.timeout)
        return self

    def __exit__(self, *exc):
        """Clean up browser resources."""
        if self.ctx:
            self.ctx.close()
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()

    def set_har_path(self, path: str):
        """Set HAR recording path before entering context."""
        self.har_path = path

    def goto(self, url: str):
        """Navigate to URL."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        self.page.goto(url, wait_until='domcontentloaded')

    def wait_network_idle(self, idle_ms: int = 2000):
        """Wait for network to be idle."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        # Use the idle_ms as the total timeout for network idle state
        self.page.wait_for_load_state('networkidle', timeout=max(idle_ms, self.timeout))

    def screenshot(self, path: str, full_page: bool = True):
        """Capture screenshot.
        
        Args:
            path: File path to save screenshot
            full_page: Whether to capture full page or just viewport
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.page.screenshot(path=path, full_page=full_page)

    def dump_dom(self, path: str):
        """Dump page DOM to file.
        
        Args:
            path: File path to save DOM content
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
        html = self.page.content()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

    def get_title(self) -> str:
        """Get page title."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        return self.page.title()

    def get_url(self) -> str:
        """Get current URL."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        return self.page.url

    def find_click(self, selectors: List[Dict[str, str]]) -> Dict[str, str]:
        """Try multiple selector strategies to find and click element.
        
        Args:
            selectors: List of selector strategies to try, each with 'strategy' and 'query'
            
        Returns:
            The selector that successfully worked
            
        Raises:
            RuntimeError: If no selector strategy succeeded
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
            
        attempts = []
        for sel in selectors:
            try:
                st = sel['strategy']
                q = sel['query']
                
                if st == 'aria':
                    el = self.page.get_by_role("link", name=q)
                elif st == 'text':
                    el = self.page.get_by_text(q, exact=False)
                elif st == 'css':
                    el = self.page.locator(q).first
                elif st == 'xpath':
                    el = self.page.locator(f"xpath={q}").first
                else:
                    attempts.append({'strategy': st, 'query': q, 'ok': False, 'error': 'Unknown strategy'})
                    continue
                
                # Ensure element is visible and clickable
                el.scroll_into_view_if_needed()
                el.click(timeout=5000)
                
                attempts.append({'strategy': st, 'query': q, 'ok': True})
                return sel
                
            except Exception as e:
                attempts.append({'strategy': st, 'query': q, 'ok': False, 'error': str(e)})
                continue
        
        raise RuntimeError(f'No selector strategy succeeded. Attempts: {attempts}')

    def extract_selector_info(self, selectors: List[Dict[str, str]]) -> Dict:
        """Extract information about elements matching selectors.
        
        Args:
            selectors: List of selector strategies
            
        Returns:
            Dict with selector information and matching elements
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")
            
        results = []
        for sel in selectors:
            try:
                st = sel['strategy']
                q = sel['query']
                
                if st == 'aria':
                    el = self.page.get_by_role("link", name=q)
                elif st == 'text':
                    el = self.page.get_by_text(q, exact=False)
                elif st == 'css':
                    el = self.page.locator(q).first
                elif st == 'xpath':
                    el = self.page.locator(f"xpath={q}").first
                else:
                    continue
                
                # Get element info if it exists
                if el.count() > 0:
                    outer_html = el.first.evaluate("el => el.outerHTML")
                    results.append({
                        'strategy': st,
                        'query': q,
                        'found': True,
                        'outer_html': outer_html[:200]  # Truncate for readability
                    })
                else:
                    results.append({
                        'strategy': st,
                        'query': q,
                        'found': False
                    })
                    
            except Exception as e:
                results.append({
                    'strategy': st,
                    'query': q,
                    'found': False,
                    'error': str(e)
                })
        
        return {'selectors': results}
