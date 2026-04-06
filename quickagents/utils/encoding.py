"""
Encoding Configuration - 统一编码配置

QuickAgents 全局使用 UTF-8 编码（无BOM）

编码策略:
- 文件读写: UTF-8
- 终端输出: UTF-8
- JSON处理: UTF-8
- SQLite存储: UTF-8

跨平台兼容:
- Windows: 通过环境变量和sys配置强制UTF-8
- macOS/Linux: 默认UTF-8，无需特殊处理

支持的字符:
- 中文: ✅ 所有汉字（包括生僻字）
- 英文: ✅ 完美支持
- Emoji: ✅ 完美支持
- 日韩文: ✅ 完美支持
- 特殊符号: ✅ 完美支持
"""

from typing import Optional
import sys
import os
import locale
import logging

logger = logging.getLogger(__name__)

# 统一编码配置
DEFAULT_ENCODING = "utf-8"
FALLBACK_ENCODING = "utf-8"  # 不使用GBK等
ERRORS_HANDLER = "replace"  # 遇到无法解码的字符时替换


def configure_utf8():
    """
    配置全局UTF-8编码

    应在程序启动时调用此函数
    """
    # 1. 设置Python默认编码
    if sys.version_info >= (3, 0):
        # Python 3 默认就是UTF-8，但确保stdout/stderr正确
        if sys.platform == "win32":
            # Windows需要特殊处理
            try:
                # 尝试设置控制台为UTF-8模式
                import ctypes

                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)  # UTF-8 code page
                kernel32.SetConsoleCP(65001)
            except Exception as e:
                logger.debug("Failed to set Windows console to UTF-8 code page: %s", e)
            os.environ["PYTHONIOENCODING"] = "utf-8"
            os.environ["PYTHONUTF8"] = "1"

    # 2. 重新配置stdout/stderr
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors=ERRORS_HANDLER)
            sys.stderr.reconfigure(encoding="utf-8", errors=ERRORS_HANDLER)
        except AttributeError as e:
            logger.debug("sys.stdout.reconfigure not available (Python < 3.7): %s", e)

    # 3. 设置locale
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        logger.debug("Failed to set locale")


def safe_decode(content: bytes, encoding: Optional[str] = None) -> str:
    """
    安全解码字节数据

    Args:
        content: 字节数据
        encoding: 指定编码（默认尝试UTF-8，失败则用fallback）

    Returns:
        解码后的字符串
    """
    if encoding:
        try:
            return content.decode(encoding, errors=ERRORS_HANDLER)
        except Exception as e:
            logger.debug("Failed to decode with encoding '%s': %s", encoding, e)

    # 优先尝试UTF-8
    try:
        return content.decode("utf-8", errors=ERRORS_HANDLER)
    except UnicodeDecodeError as e:
        logger.debug("Failed to decode as UTF-8, trying fallback encodings: %s", e)

    # 尝试常见编码
    for enc in ["utf-8-sig", "gb18030", "gbk", "gb2312", "latin-1"]:
        try:
            return content.decode(enc, errors=ERRORS_HANDLER)
        except UnicodeDecodeError:
            continue

    # 最后使用replacement字符
    return content.decode("utf-8", errors="replace")


def safe_encode(content: str, encoding: str = DEFAULT_ENCODING) -> bytes:
    """
    安全编码字符串

    Args:
        content: 字符串
        encoding: 目标编码（默认UTF-8）

    Returns:
        编码后的字节数据
    """
    return content.encode(encoding, errors=ERRORS_HANDLER)


def read_file_utf8(file_path: str) -> str:
    """
    以UTF-8编码读取文件

    自动处理BOM，自动尝试fallback编码
    """
    with open(file_path, "rb") as f:
        content = f.read()

    # 检测并移除BOM
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]  # 移除UTF-8 BOM
    elif content.startswith(b"\xff\xfe"):
        content = content[2:]  # 移除UTF-16 LE BOM
        return content.decode("utf-16-le", errors=ERRORS_HANDLER)
    elif content.startswith(b"\xfe\xff"):
        content = content[2:]  # 移除UTF-16 BE BOM
        return content.decode("utf-16-be", errors=ERRORS_HANDLER)

    return safe_decode(content)


def write_file_utf8(file_path: str, content: str) -> None:
    """
    以UTF-8编码写入文件（无BOM）
    """
    # 确保目录存在
    import os

    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    # 写入UTF-8无BOM
    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def get_terminal_encoding() -> str:
    """
    获取终端编码
    """
    # 检查环境变量
    if "PYTHONIOENCODING" in os.environ:
        return os.environ["PYTHONIOENCODING"]

    # 检查stdout编码
    if hasattr(sys.stdout, "encoding") and sys.stdout.encoding:
        return sys.stdout.encoding

    # 检查locale
    try:
        loc = locale.getpreferredencoding()
        if loc:
            return loc
    except Exception as e:
        logger.debug("Failed to get preferred encoding from locale: %s", e)

    # 默认UTF-8
    return "utf-8"


def is_utf8_terminal() -> bool:
    """
    检查终端是否支持UTF-8
    """
    encoding = get_terminal_encoding()
    return "utf" in encoding.lower()


# 程序启动时自动配置
if __name__ != "__main__":
    # 作为模块导入时自动配置
    configure_utf8()
