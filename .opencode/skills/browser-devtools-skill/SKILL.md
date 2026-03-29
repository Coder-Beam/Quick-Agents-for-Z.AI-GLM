---
name: browser-devtools-skill
description: |
  浏览器自动化与DevTools集成。
  功能：获取控制台日志、网络请求、性能指标、执行JavaScript、截图。
  
  支持后端：
  - chromium (默认): Playwright + Chromium
  - lightpanda: Playwright + Lightpanda (用户自行安装)
  
  安装:
    pip install quickagents[browser]
    playwright install chromium
  
  使用Lightpanda:
    1. 从 https://lightpanda.io 下载安装
    2. 启动: lightpanda serve --port 9222
    3. 使用: Browser(backend='lightpanda')

license: MIT
allowed-tools:
  - read
  - write
  - edit
  - bash
metadata:
  category: browser
  priority: high
  version: 1.0.0
  localized: true
---

# Browser DevTools Skill

浏览器自动化与DevTools集成，支持Chromium和Lightpanda后端。

## 架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    浏览器自动化架构                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Python API (统一接口):                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  from quickagents import Browser                            │  │
│   │                                                             │  │
│   │  # 默认使用Chromium                                         │  │
│   │  browser = Browser()                                        │  │
│   │                                                             │  │
│   │  # 使用Lightpanda（需先启动lightpanda serve）               │  │
│   │  browser = Browser(backend='lightpanda')                    │  │
│   │                                                             │  │
│   │  # 打开页面                                                 │  │
│   │  page = browser.open('https://example.com')                 │  │
│   │                                                             │  │
│   │  # 获取控制台日志                                           │  │
│   │  console_logs = page.get_console_logs()                     │  │
│   │                                                             │  │
│   │  # 获取网络请求                                             │  │
│   │  network = page.get_network_requests()                      │  │
│   │                                                             │  │
│   │  # 关闭浏览器                                               │  │
│   │  browser.close()                                            │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   底层实现:                                                         │
│   ├── Chromium: Playwright → Chromium CDP                         │
│   └── Lightpanda: Playwright → Lightpanda CDP (port 9222)         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 安装

### 默认安装（Chromium）

```bash
pip install quickagents[browser]
playwright install chromium
```

### 使用Lightpanda

Lightpanda是一个轻量级headless浏览器，比Chrome快11倍，内存少9倍。

```bash
# 1. 从官网下载安装
# https://lightpanda.io

# 2. 启动Lightpanda
lightpanda serve --port 9222

# 3. 在Python中使用
from quickagents import Browser
browser = Browser(backend='lightpanda')
```

## Python API

### 基本使用

```python
from quickagents import Browser

# 创建浏览器实例
browser = Browser()

# 打开页面
page = browser.open('https://example.com')

# 获取控制台日志
console_logs = page.get_console_logs()
for log in console_logs:
    print(f"[{log.type}] {log.message}")

# 获取网络请求
network = page.get_network_requests()
for req in network:
    print(f"[{req.method}] {req.url} - {req.status}")

# 获取性能指标
perf = page.get_performance()
print(perf)

# 关闭浏览器
browser.close()
```

### 使用上下文管理器

```python
from quickagents import Browser

with Browser() as browser:
    page = browser.open('https://example.com')
    console_logs = page.get_console_logs()
    # 自动关闭
```

### 使用Lightpanda

```python
from quickagents import Browser

# 先启动Lightpanda: lightpanda serve --port 9222
browser = Browser(backend='lightpanda')
page = browser.open('https://example.com')
console_logs = page.get_console_logs()
browser.close()
```

## 功能详解

### 1. 控制台日志 (Console)

```python
# 获取所有日志
logs = page.get_console_logs()

# 获取错误日志
errors = page.get_errors()

# 按类型过滤
errors = page.get_console_logs(type_filter='error')
warnings = page.get_console_logs(type_filter='warning')
```

**ConsoleLog对象**:
```python
@dataclass
class ConsoleLog:
    type: str          # log, warn, error, info, debug
    message: str       # 日志内容
    timestamp: float   # 时间戳
    url: str           # 来源URL
    line: int          # 行号
    column: int        # 列号
```

### 2. 网络请求 (Network)

```python
# 获取所有请求
requests = page.get_network_requests()

# 按状态码过滤
failed = page.get_network_requests(status_filter=404)
success = page.get_network_requests(status_filter=200)

# 按方法过滤
post_requests = page.get_network_requests(method_filter='POST')

# 按URL过滤
api_requests = page.get_network_requests(url_filter='/api/')
```

**NetworkRequest对象**:
```python
@dataclass
class NetworkRequest:
    request_id: str
    url: str
    method: str
    status: int
    mime_type: str
    resource_type: str
    request_time: float
    response_time: float
    duration_ms: float
    request_headers: Dict
    response_headers: Dict
```

### 3. 性能指标 (Performance)

```python
perf = page.get_performance()
# 返回 PerformanceMetric 列表
```

### 4. 执行JavaScript

```python
# 执行JavaScript并获取结果
title = page.evaluate('document.title')
print(title)

# 复杂操作
result = page.evaluate('''
    () => {
        return {
            title: document.title,
            url: window.location.href,
            cookies: document.cookie
        }
    }
''')
print(result)
```

### 5. 截图

```python
# 截取可见区域
page.screenshot('screenshot.png')

# 截取整页
page.screenshot('full-page.png', full_page=True)
```

### 6. 页面操作

```python
# 等待元素
page.wait_for_selector('#content', timeout=5000)

# 点击
page.click('#button')

# 填充输入框
page.fill('#input', 'Hello World')

# 获取内容
html = page.get_content()
title = page.get_title()
url = page.get_url()
```

### 7. Cookie管理

```python
# 设置Cookie
page.set_cookie({'name': 'session', 'value': 'abc123'})

# 获取Cookie
cookies = page.get_cookies()
```

## 使用场景

### 调试前端错误

```python
from quickagents import Browser

with Browser() as browser:
    page = browser.open('https://myapp.com')
    
    # 等待页面加载
    page.wait_for_selector('#app')
    
    # 检查控制台错误
    errors = page.get_errors()
    if errors:
        print("发现前端错误:")
        for err in errors:
            print(f"  {err.url}:{err.line} - {err.message}")
```

### API请求分析

```python
from quickagents import Browser

with Browser() as browser:
    page = browser.open('https://myapp.com/dashboard')
    
    # 等待数据加载
    time.sleep(3)
    
    # 分析API请求
    api_requests = [r for r in page.get_network_requests() 
                    if r.resource_type in ('xhr', 'fetch')]
    
    print("API请求分析:")
    for req in api_requests:
        print(f"  {req.method} {req.url}")
        print(f"    状态: {req.status}")
        print(f"    耗时: {req.duration_ms:.2f}ms")
        
        if req.status >= 400:
            print(f"    [错误] 请求失败")
```

### 性能分析

```python
from quickagents import Browser

with Browser() as browser:
    page = browser.open('https://myapp.com')
    
    # 获取性能指标
    perf = page.get_performance()
    
    print("性能指标:")
    for metric in perf:
        print(f"  {metric.name}: {metric.value:.2f}{metric.unit}")
```

## 注意事项

1. **首次使用需要安装浏览器**:
   ```bash
   playwright install chromium
   ```

2. **Lightpanda需要单独安装**:
   - 从 https://lightpanda.io 下载
   - 启动: `lightpanda serve --port 9222`

3. **资源管理**:
   - 使用 `with` 语句确保浏览器正确关闭
   - 或手动调用 `browser.close()`

4. **异步操作**:
   - 页面加载是异步的，可能需要等待
   - 使用 `wait_for_selector` 等待元素出现

---

*版本: 1.0.0 | 创建时间: 2026-03-29*
