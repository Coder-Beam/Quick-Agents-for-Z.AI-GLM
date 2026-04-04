"""
Browser - 浏览器自动化核心实现 (v2.4.0)

架构变更:
- 默认使用 Lightpanda (轻量级headless浏览器)
- 强制安装 Playwright + Lightpanda
- 启动时自动检测和安装
- 支持更新第三方依赖

使用方式:
    from quickagents import Browser

    # 默认使用Lightpanda（自动安装）
    browser = Browser()

    # 回退到Chromium
    browser = Browser(fallback_to_chromium=True)

    # 打开页面
    page = browser.open('https://example.com')

    # 获取控制台日志
    console_logs = page.get_console_logs()

    # 关闭浏览器
    browser.close()
"""

import time
import socket
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from .installer import ensure_browser_installed, check_lightpanda, update_dependencies


class BrowserBackend(Enum):
    """浏览器后端类型"""

    LIGHTPANDA = "lightpanda"  # 默认
    CHROMIUM = "chromium"  # 回退选项


@dataclass
class ConsoleLog:
    """控制台日志条目"""

    type: str  # log, warn, error, info, debug
    message: str  # 日志内容
    timestamp: float  # 时间戳
    url: str = ""  # 来源URL
    line: int = 0  # 行号
    column: int = 0  # 列号


@dataclass
class NetworkRequest:
    """网络请求记录"""

    request_id: str
    url: str
    method: str
    status: int
    mime_type: str = ""
    resource_type: str = ""
    request_time: float = 0
    response_time: float = 0
    duration_ms: float = 0
    request_headers: Dict = field(default_factory=dict)
    response_headers: Dict = field(default_factory=dict)
    request_body: str = ""
    response_body: str = ""


@dataclass
class PerformanceMetric:
    """性能指标"""

    name: str
    value: float
    unit: str = "ms"


class Page:
    """页面对象"""

    def __init__(self, playwright_page, url: str):
        self._page = playwright_page
        self.url = url
        self._console_logs: List[ConsoleLog] = []
        self._network_requests: List[NetworkRequest] = []
        self._setup_listeners()

    def _setup_listeners(self):
        """设置事件监听器"""

        def on_console(msg):
            log = ConsoleLog(
                type=msg.type,
                message=msg.text,
                timestamp=time.time(),
                url=msg.location.get("url", ""),
                line=msg.location.get("lineNumber", 0),
                column=msg.location.get("columnNumber", 0),
            )
            self._console_logs.append(log)

        self._page.on("console", on_console)

        def on_request(request):
            req = NetworkRequest(
                request_id=request.headers.get("x-request-id", ""),
                url=request.url,
                method=request.method,
                status=0,
                resource_type=request.resource_type,
                request_time=time.time(),
            )
            self._network_requests.append(req)

        def on_response(response):
            for req in self._network_requests:
                if req.url == response.url and req.status == 0:
                    req.status = response.status
                    req.response_time = time.time()
                    req.duration_ms = (req.response_time - req.request_time) * 1000
                    req.mime_type = response.headers.get("content-type", "")
                    req.response_headers = dict(response.headers)
                    break

        self._page.on("request", on_request)
        self._page.on("response", on_response)

    def get_console_logs(self, log_type: str = None) -> List[ConsoleLog]:
        """获取控制台日志"""
        if log_type:
            return [log for log in self._console_logs if log.type == log_type]
        return self._console_logs.copy()

    def get_errors(self) -> List[ConsoleLog]:
        """获取错误日志"""
        return [log for log in self._console_logs if log.type in ("error", "warning")]

    def get_network_requests(self, resource_type: str = None) -> List[NetworkRequest]:
        """获取网络请求"""
        if resource_type:
            return [
                req
                for req in self._network_requests
                if req.resource_type == resource_type
            ]
        return self._network_requests.copy()

    def get_api_requests(self) -> List[NetworkRequest]:
        """获取API请求"""
        return [
            req
            for req in self._network_requests
            if req.resource_type in ("xhr", "fetch")
        ]

    def get_performance(self) -> List[PerformanceMetric]:
        """获取性能指标"""
        try:
            timing = self._page.evaluate("""() => {
                const t = performance.timing;
                return {
                    dns: t.domainLookupEnd - t.domainLookupStart,
                    tcp: t.connectEnd - t.connectStart,
                    request: t.responseStart - t.requestStart,
                    response: t.responseEnd - t.responseStart,
                    dom: t.domComplete - t.domInteractive,
                    load: t.loadEventEnd - t.navigationStart
                };
            }""")

            return [
                PerformanceMetric(name=k, value=v, unit="ms") for k, v in timing.items()
            ]
        except Exception:
            return []

    def evaluate(self, script: str) -> Any:
        """执行JavaScript"""
        return self._page.evaluate(script)

    def screenshot(self, path: str, full_page: bool = False) -> str:
        """截图"""
        self._page.screenshot(path=path, full_page=full_page)
        return path

    def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """等待元素"""
        try:
            self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    def click(self, selector: str) -> bool:
        """点击元素"""
        try:
            self._page.click(selector)
            return True
        except Exception:
            return False

    def fill(self, selector: str, value: str) -> bool:
        """填充输入框"""
        try:
            self._page.fill(selector, value)
            return True
        except Exception:
            return False

    def get_content(self) -> str:
        """获取页面HTML"""
        return self._page.content()

    def get_title(self) -> str:
        """获取页面标题"""
        return self._page.title()

    def close(self):
        """关闭页面"""
        self._page.close()


class Browser:
    """
    浏览器自动化管理器 (v2.4.0)

    默认使用Lightpanda，自动安装依赖。

    使用方式:
        from quickagents import Browser

        # 默认使用Lightpanda（自动安装）
        browser = Browser()

        # 回退到Chromium
        browser = Browser(fallback_to_chromium=True)

        # 打开页面
        page = browser.open('https://example.com')

        # 获取控制台日志
        console_logs = page.get_console_logs()

        # 关闭
        browser.close()
    """

    LIGHTPANDA_PORT = 9222

    def __init__(
        self,
        backend: str = "lightpanda",
        fallback_to_chromium: bool = True,
        auto_install: bool = True,
        headless: bool = True,
    ):
        """
        初始化浏览器

        Args:
            backend: 后端类型 ('lightpanda' 或 'chromium')
            fallback_to_chromium: 如果Lightpanda不可用，是否回退到Chromium
            auto_install: 是否自动安装依赖
            headless: 是否无头模式
        """
        self.preferred_backend = backend
        self.fallback_to_chromium = fallback_to_chromium
        self.auto_install = auto_install
        self.headless = headless

        self._playwright = None
        self._browser = None
        self._context = None
        self._pages: List[Page] = []
        self._actual_backend: Optional[BrowserBackend] = None

        # 确保依赖已安装
        if auto_install:
            self._ensure_dependencies()

        # 初始化浏览器
        self._init_browser()

    def _ensure_dependencies(self):
        """确保依赖已安装"""
        print("[Browser] 检查浏览器依赖...")
        result = ensure_browser_installed(auto_install=True)

        if result["errors"]:
            print(f"[Browser] 安装警告: {result['errors']}")

        if not result["playwright"]["installed"]:
            raise RuntimeError("Playwright安装失败")

    def _init_browser(self):
        """初始化浏览器"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright未安装。请运行: pip install playwright && playwright install chromium"
            )

        self._playwright = sync_playwright().start()

        # 尝试使用Lightpanda
        if self.preferred_backend == "lightpanda":
            if self._try_lightpanda():
                self._actual_backend = BrowserBackend.LIGHTPANDA
                print("[Browser] 使用 Lightpanda 后端")
                return

            # 回退到Chromium
            if self.fallback_to_chromium:
                print("[Browser] Lightpanda不可用，回退到 Chromium")
                self._init_chromium()
                self._actual_backend = BrowserBackend.CHROMIUM
                return
            else:
                raise RuntimeError("Lightpanda不可用且禁用了回退")

        # 直接使用Chromium
        self._init_chromium()
        self._actual_backend = BrowserBackend.CHROMIUM
        print("[Browser] 使用 Chromium 后端")

    def _try_lightpanda(self) -> bool:
        """尝试连接Lightpanda"""
        # 检查Lightpanda是否可用
        installed, path = check_lightpanda()
        if not installed:
            print("[Browser] Lightpanda未安装")
            return False

        # 检查端口是否开放
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", self.LIGHTPANDA_PORT))
        sock.close()

        if result != 0:
            print(f"[Browser] Lightpanda服务未启动 (端口 {self.LIGHTPANDA_PORT})")
            print("[Browser] 请先启动: lightpanda serve --port 9222")
            return False

        # 尝试连接
        try:
            self._browser = self._playwright.chromium.connect_over_cdp(
                f"http://localhost:{self.LIGHTPANDA_PORT}"
            )
            self._context = self._browser.new_context()
            return True
        except Exception as e:
            print(f"[Browser] 连接Lightpanda失败: {e}")
            return False

    def _init_chromium(self):
        """初始化Chromium"""
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context()

    @property
    def backend(self) -> str:
        """获取实际使用的后端"""
        return self._actual_backend.value if self._actual_backend else "unknown"

    def open(self, url: str, wait_until: str = "load", timeout: int = 30000) -> Page:
        """打开页面"""
        if not self._context:
            raise RuntimeError("浏览器未初始化")

        playwright_page = self._context.new_page()
        playwright_page.goto(url, timeout=timeout, wait_until=wait_until)

        qa_page = Page(playwright_page, url)
        self._pages.append(qa_page)

        return qa_page

    def new_page(self) -> Page:
        """创建空白页面"""
        if not self._context:
            raise RuntimeError("浏览器未初始化")

        playwright_page = self._context.new_page()
        return Page(playwright_page, "about:blank")

    def get_pages(self) -> List[Page]:
        """获取所有页面"""
        return self._pages.copy()

    def close(self):
        """关闭浏览器"""
        for page in self._pages:
            try:
                page.close()
            except Exception:
                pass

        if self._context:
            self._context.close()

        if self._browser:
            self._browser.close()

        if self._playwright:
            self._playwright.stop()

        self._pages.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def update_all_dependencies() -> Dict:
    """
    更新所有浏览器依赖到最新版本

    Returns:
        更新结果
    """
    return update_dependencies()
