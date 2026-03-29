"""
QuickAgents Browser - 浏览器自动化模块

架构:
- 默认: Playwright + Chromium
- 可选: Playwright + Lightpanda (用户自行安装)

安装:
    # 默认安装（Playwright + Chromium）
    pip install quickagents[browser]
    playwright install chromium

    # 使用Lightpanda（用户自行安装）
    # 1. 从 https://lightpanda.io 下载安装
    # 2. 启动: lightpanda serve --port 9222
    # 3. 使用: Browser(backend='lightpanda')

使用:
    from quickagents import Browser

    # 默认使用Chromium
    browser = Browser()
    
    # 使用Lightpanda
    browser = Browser(backend='lightpanda')
    
    # 获取控制台日志
    page = browser.open('https://example.com')
    console_logs = page.get_console_logs()
    
    # 关闭
    browser.close()
"""

from .browser import Browser, BrowserBackend, Page, ConsoleLog, NetworkRequest

__all__ = [
    'Browser',
    'BrowserBackend',
    'Page',
    'ConsoleLog',
    'NetworkRequest',
]
