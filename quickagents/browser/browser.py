"""
Browser - 浏览器自动化核心实现

支持后端:
- chromium (默认): Playwright + Chromium
- lightpanda: Playwright + Lightpanda (用户自行安装)

功能:
- 打开页面
- 获取控制台日志 (DevTools Console)
- 获取网络请求 (Network)
- 获取性能指标 (Performance)
- 执行JavaScript
- 截图
- PDF生成
- Cookie管理

使用方式:
    from quickagents import Browser

    # 默认使用Chromium
    browser = Browser()
    
    # 使用Lightpanda（需先启动lightpanda serve）
    browser = Browser(backend='lightpanda')
    
    # 打开页面
    page = browser.open('https://example.com')
    
    # 等待页面加载
    time.sleep(2)  # 等待2秒后检查是否有控制台日志
    console_logs = page.get_console_logs()
    print(f"控制台日志数量: {len(console_logs)}")
            
            for log in console_logs:
                print(f"  [{log.type}] {log.message[:100]}")
    
    # 获取网络请求
    network = page.get_network_requests()
    print(f"网络请求数量: {len(network)}")
            
            for req in network:
                print(f"  [{req.method}] {req.url}")
                print(f"    状态: {req.status}")
                print(f"    耗时: {req.duration_ms:.2f}ms")
    
    # 关闭浏览器
    browser.close()
"""

import subprocess
import time
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class BrowserBackend(Enum):
    """浏览器后端类型"""
    CHROMIUM = "chromium"
    LIGHTPANDA = "lightpanda"


@dataclass
class ConsoleLog:
    """控制台日志条目"""
    type: str          # log, warn, error, info, debug
    message: str       # 日志内容
    timestamp: float   # 时间戳
    url: str = ""      # 来源URL
    line: int = 0      # 行号
    column: int = 0    # 列号


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
    """
    页面对象
    
    管理单个页面的操作
    """
    
    def __init__(self, playwright_page, url: str):
        self._page = playwright_page
        self.url = url
        self._console_logs: List[ConsoleLog] = []
        self._network_requests: List[NetworkRequest] = []
        self._setup_listeners()
    
    def _setup_listeners(self):
        """设置事件监听器"""
        # 监听控制台日志
        def on_console(msg):
            log = ConsoleLog(
                type=msg.type,
                message=msg.text,
                timestamp=time.time(),
                url=msg.location.get('url', ''),
                line=msg.location.get('lineNumber', 0),
                column=msg.location.get('columnNumber', 0)
            )
            self._console_logs.append(log)
        
        self._page.on('console', on_console)
        
        # 监听网络请求
        def on_request(request):
            req = NetworkRequest(
                request_id=request.headers.get('x-request-id', ''),
                url=request.url,
                method=request.method,
                status=0,
                resource_type=request.resource_type,
                request_time=time.time()
            )
            self._network_requests.append(req)
        
        def on_response(response):
            # 找到对应的请求并更新状态
            for req in self._network_requests:
                if req.url == response.url:
                    req.status = response.status
                    req.response_time = time.time()
                    req.duration_ms = (req.response_time - req.request_time) * 1000
                    req.mime_type = response.headers.get('content-type', '')
                    req.response_headers = dict(response.headers)
        
        self._page.on('request', on_request)
        self._page.on('response', on_response)
    
    def get_console_logs(self, url_filter: str = None,
                 type_filter: str = None) -> List[ConsoleLog]:
        """
        获取控制台日志
        
        Args:
            url_filter: URL过滤（可选）
            type_filter: 类型过滤（可选）
        
        Returns:
            控制台日志列表
        """
        logs = self._console_logs.copy()
        
        if url_filter:
            logs = [log for log in logs if url_filter in log.url]
        
        if type_filter:
            logs = [log for log in logs if log.type in type_filter]
        
        return logs
    
    def get_network_requests(self, url_filter: str = None,
                      status_filter: int = None,
                      method_filter: str = None) -> List[NetworkRequest]:
        """
        获取网络请求
        
        Args:
            url_filter: URL过滤（可选）
            status_filter: 状态码过滤（可选）
            method_filter: HTTP方法过滤（可选）
        
        Returns:
            网络请求列表
        """
        requests = self._network_requests.copy()
        
        if url_filter:
            requests = [req for req in requests if url_filter in req.url]
        
        if status_filter is not None:
            requests = [req for req in requests if req.status == status_filter]
        
        if method_filter:
            requests = [req for req in requests if req.method == method_filter]
        
        return requests
    
    def get_performance(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            性能指标字典
        """
        metrics = {}
        
        try:
                # 使用Playwright的性能API
                perf_entries = self._page.evaluate('performance.getEntries()')
                
                for entry in perf_entries:
                    metrics[entry['name']] = PerformanceMetric(
                        name=entry['name'],
                        value=entry['startTime'] if 'startTime' in entry else entry.get('value', 00),
                        unit='ms'
                    )
        except Exception:
            pass
        
        return metrics
    
    def evaluate(self, script: str) -> Any:
        """
        执行JavaScript并返回结果
        
        Args:
            script: JavaScript代码
        
        Returns:
            执行结果
        """
        return self._page.evaluate(script)
    
    def screenshot(self, path: str, full_page: bool = False) -> str:
        """
        截图
        
        Args:
            path: 保存路径
            full_page: 是否全页面（默认False）
        """
        return self._page.screenshot(path=path, full_page=full_page)
    
    def get_content(self) -> str:
        """获取页面HTML内容"""
        return self._page.content()
    
    def get_title(self) -> str:
        """获取页面标题"""
        return self._page.title()
    
    def get_url(self) -> str:
        """获取当前URL"""
        return self._page.url
    
    def set_cookie(self, cookies: Dict[str, str]) -> None:
        """
        设置Cookie
        
        Args:
            cookies: Cookie字典
        """
        self._context.add_cookies(cookies)
    
    def get_cookies(self) -> Dict[str, str]:
        """获取所有Cookie"""
        return self._context.cookies()
    
    def clear_console_logs(self) -> None:
        """清空控制台日志缓存"""
        self._console_logs.clear()
    
    def clear_network_requests(self) -> None:
        """清空网络请求缓存"""
        self._network_requests.clear()


class Browser:
    """
    浏览器自动化管理器
    
    支持后端:
    - chromium (默认): Playwright + Chromium
    - lightpanda: Playwright + Lightpanda (用户自行安装)
    
    使用方式:
        from quickagents import Browser
        
        # 默认使用Chromium
        browser = Browser()
        
        # 使用Lightpanda
        browser = Browser(backend='lightpanda')
        
        # 打开页面
        page = browser.open('https://example.com')
        
        # 获取控制台日志
        console_logs = page.get_console_logs()
        
        # 关闭
        browser.close()
    """
    
    def __init__(self, backend: str = 'chromium', headless: bool = True,
                 lightpanda_host: str = 'localhost',
                 lightpanda_port: int = 9222,
                 lightpanda_timeout: int = 30000):
        """
        初始化浏览器
        
        Args:
            backend: 后端类型 ('chromium' 或 'lightpanda')
            headless: 是否无头模式（默认True）
            lightpanda_host: Lightpanda主机（默认localhost）
            lightpanda_port: Lightpanda端口（默认9222）
            lightpanda_timeout: Lightpanda连接超时（默认30秒）
        """
        self.backend = backend
        self.headless = headless
        self.lightpanda_host = lightpanda_host
        self.lightpanda_port = lightpanda_port
        self.lightpanda_timeout = lightpanda_timeout
        
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._pages: List[Page] = []
        
        self._init_browser()
    
    def _init_browser(self) -> None:
        """初始化浏览器"""
        try:
            from playwright.sync_api import sync_playwright, Browser as PwBrowser
            from playwright.sync_api._generated import Page as PwPage
        except ImportError:
            raise ImportError(
                "Playwright未安装。请使用: pip install quickagents[browser]"
            )
        
        if self.backend == 'lightpanda':
            self._init_lightpanda()
        else:
            self._init_chromium()
    
    def _init_chromium(self) -> None:
        """初始化Chromium浏览器"""
        self._playwright = sync_playwright()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context()
    
    def _init_lightpanda(self) -> None:
        """初始化Lightpanda浏览器"""
        # 检查Lightpanda是否可用
        if not self._check_lightpanda_available():
            raise RuntimeError(
                f"Lightpanda不可用。请确保Lightpanda已安装并运行:\n"
                安装: 从 https://lightpanda.io 下载
                启动: lightpanda serve --port {self.lightpanda_port}
                等待: 等待Lightpanda启动（约5秒）
                然后: Browser(backend='lightpanda')
                """
            )
        
        # 连接到Lightpanda CDP
        try:
                self._playwright = sync_playwright()
                # 使用CDP连接到Lightpanda
                self._browser = self._playwright.chromium.connect_over_cdp(
                    endpoint_url=f"http://{self.lightpanda_host}:{self.lightpanda_port}"
                )
                self._context = self._browser.new_context()
            except Exception as e:
                raise RuntimeError(f"无法连接到Lightpanda: {e}")
    
    def _check_lightpanda_available(self) -> bool:
        """检查Lightpanda是否可用"""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
                result = sock.connect_ex((self.lightpanda_host, self.lightpanda_port))
                sock.close()
                return True
            except:
                return False
    
    def open(self, url: str, wait_until: str = 'load',
                timeout: int = 30000) -> Page:
        """
        打开页面
        
        Args:
            url: 页面URL
            wait_until: 等待加载状态 ('load', 'domcontentloaded', 'networkidle')
            timeout: 超时时间（毫秒）
        
        Returns:
            Page对象
        """
        if not self._context:
            raise RuntimeError("浏览器未初始化")
        
        playwright_page = self._context.new_page()
        page.goto(url, timeout=timeout, wait_until=wait_until)
        
        qa_page = Page(playwright_page, url)
        self._pages.append(qa_page)
        
        return qa_page
    
    def new_page(self) -> Page:
        """创建空白页面"""
        if not self._context:
            raise RuntimeError("浏览器未初始化")
        
        playwright_page = self._context.new_page()
        return Page(playwright_page, 'about:blank')
    
    def get_pages(self) -> List[Page]:
        """获取所有页面"""
        return self._pages.copy()
    
    def close(self) -> None:
        """关闭浏览器"""
        if self._browser:
            self._browser.close()
        
        if self._playwright:
            self._playwright.stop()
        
        self._pages.clear()
    
    def __enter__(self):
        """上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭浏览器"""
        self.close()
