"""
QuickAgents Browser - 浏览器自动化模块 (v2.4.0)

架构:
- 默认: Playwright + Lightpanda (强制安装)
- 回退: Playwright + Chromium (自动回退)
- 启动时自动检测和安装依赖

安装:
    pip install quickagents
    # 首次使用时会自动安装 Playwright + Lightpanda

使用:
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
    
    # 更新依赖
    from quickagents.browser import update_all_dependencies
    update_all_dependencies()
"""

from .browser import (
    Browser, BrowserBackend, Page, ConsoleLog, NetworkRequest,
    PerformanceMetric
)
from .installer import (
    ensure_browser_installed,
    update_dependencies,
    check_lightpanda,
    BrowserInstaller,
    get_installer
)

__all__ = [
    # Browser core
    'Browser',
    'BrowserBackend',
    'Page',
    'ConsoleLog',
    'NetworkRequest',
    'PerformanceMetric',
    # Installer
    'ensure_browser_installed',
    'update_dependencies',
    'check_lightpanda',
    'BrowserInstaller',
    'get_installer',
    'update_all_dependencies',
]
