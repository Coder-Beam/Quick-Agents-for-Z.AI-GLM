"""
Browser Installer - 自动检测和安装浏览器依赖

功能:
- 检测 Playwright 是否安装
- 检测 Lightpanda 是否安装
- 自动安装缺失的依赖
- 启动时更新第三方支持库

使用:
    from quickagents.browser.installer import ensure_browser_installed, update_dependencies

    # 确保浏览器已安装
    ensure_browser_installed()

    # 更新所有依赖
    update_dependencies()
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BrowserInstaller:
    """
    浏览器依赖安装器

    自动检测和安装:
    - Playwright
    - Lightpanda
    - Chromium
    """

    # Lightpanda下载地址
    LIGHTPANDA_DOWNLOAD_URL = (
        "https://github.com/lightpanda-io/browser/releases/latest/download"
    )

    def __init__(self):
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        self.is_windows = self.system == "windows"
        self.is_mac = self.system == "darwin"
        self.is_linux = self.system == "linux"

    # ==================== Playwright ====================

    def check_playwright_installed(self) -> bool:
        """检查Playwright是否已安装"""
        try:
            import playwright  # noqa: F401

            return True
        except ImportError:
            return False

    def check_chromium_installed(self) -> bool:
        """检查Chromium是否已安装"""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                # 尝试启动Chromium
                browser = p.chromium.launch(headless=True)
                browser.close()
                return True
        except Exception:
            return False

    def install_playwright(self) -> Dict:
        """
        安装Playwright

        Returns:
            安装结果
        """
        result = {
            "playwright_installed": False,
            "chromium_installed": False,
            "errors": [],
        }

        # 1. 安装Playwright Python包
        try:
            print("[Installer] 正在安装 Playwright...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "playwright"],
                check=True,
                capture_output=True,
            )
            result["playwright_installed"] = True
            print("[Installer] Playwright 安装成功")
        except subprocess.CalledProcessError as e:
            result["errors"].append(f"Playwright安装失败: {e}")  # type: ignore[attr-defined]
            return result

        # 2. 安装Chromium浏览器
        try:
            print("[Installer] 正在安装 Chromium 浏览器...")
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
                capture_output=True,
            )
            result["chromium_installed"] = True
            print("[Installer] Chromium 浏览器安装成功")
        except subprocess.CalledProcessError as e:
            result["errors"].append(f"Chromium安装失败: {e}")  # type: ignore[attr-defined]

        return result

    # ==================== Lightpanda ====================

    def check_lightpanda_installed(self) -> Tuple[bool, Optional[str]]:
        """
        检查Lightpanda是否已安装

        Returns:
            (是否安装, 安装路径)
        """
        # 检查PATH中是否有lightpanda
        lightpanda_path = shutil.which("lightpanda")
        if lightpanda_path:
            return True, lightpanda_path

        # 检查常见安装位置
        common_paths = self._get_lightpanda_common_paths()
        for path in common_paths:
            if Path(path).exists():
                return True, str(path)

        return False, None

    def _get_lightpanda_common_paths(self) -> List[str]:
        """获取Lightpanda常见安装路径"""
        paths = []

        if self.is_windows:
            paths.extend(
                [
                    os.path.expandvars(r"%LOCALAPPDATA%\lightpanda\lightpanda.exe"),
                    os.path.expandvars(r"%PROGRAMFILES%\lightpanda\lightpanda.exe"),
                    "C:\\lightpanda\\lightpanda.exe",
                ]
            )
        elif self.is_mac:
            paths.extend(
                [
                    "/usr/local/bin/lightpanda",
                    "/opt/homebrew/bin/lightpanda",
                    os.path.expanduser("~/Applications/lightpanda"),
                ]
            )
        elif self.is_linux:
            paths.extend(
                [
                    "/usr/local/bin/lightpanda",
                    "/usr/bin/lightpanda",
                    os.path.expanduser("~/.local/bin/lightpanda"),
                ]
            )

        return paths

    def get_lightpanda_download_url(self) -> Optional[str]:
        """获取Lightpanda下载URL"""
        if self.is_windows:
            if self.machine in ("amd64", "x86_64"):
                return f"{self.LIGHTPANDA_DOWNLOAD_URL}/lightpanda-windows-amd64.exe"
        elif self.is_mac:
            if self.machine in ("arm64", "aarch64"):
                return f"{self.LIGHTPANDA_DOWNLOAD_URL}/lightpanda-darwin-arm64"
            else:
                return f"{self.LIGHTPANDA_DOWNLOAD_URL}/lightpanda-darwin-amd64"
        elif self.is_linux:
            if self.machine in ("amd64", "x86_64"):
                return f"{self.LIGHTPANDA_DOWNLOAD_URL}/lightpanda-linux-amd64"
            elif self.machine in ("arm64", "aarch64"):
                return f"{self.LIGHTPANDA_DOWNLOAD_URL}/lightpanda-linux-arm64"

        return None

    def install_lightpanda(self) -> Dict:
        """
        安装Lightpanda

        Returns:
            安装结果
        """
        result = {"lightpanda_installed": False, "lightpanda_path": None, "errors": []}  # type: ignore[var-annotated]

        # 检查是否已安装
        installed, path = self.check_lightpanda_installed()
        if installed:
            result["lightpanda_installed"] = True
            result["lightpanda_path"] = path  # type: ignore[assignment]
            return result

        # 获取下载URL
        download_url = self.get_lightpanda_download_url()
        if not download_url:
            result["errors"].append(f"不支持的平台: {self.system}/{self.machine}")  # type: ignore[union-attr]
            return result

        try:
            print("[Installer] 正在下载 Lightpanda...")
            print(f"[Installer] URL: {download_url}")

            # 确定安装路径
            if self.is_windows:
                install_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\lightpanda"))
                executable = install_dir / "lightpanda.exe"
            else:
                install_dir = Path.home() / ".local" / "bin"
                executable = install_dir / "lightpanda"

            # 创建目录
            install_dir.mkdir(parents=True, exist_ok=True)

            # 下载文件
            import urllib.request

            urllib.request.urlretrieve(download_url, executable)

            # 设置可执行权限
            if not self.is_windows:
                os.chmod(executable, 0o755)

            result["lightpanda_installed"] = True
            result["lightpanda_path"] = str(executable)  # type: ignore[assignment]
            print(f"[Installer] Lightpanda 安装成功: {executable}")

        except Exception as e:
            result["errors"].append(f"Lightpanda安装失败: {e}")  # type: ignore[union-attr]

        return result

    # ==================== 统一接口 ====================

    def ensure_installed(self, auto_install: bool = True) -> Dict:
        """
        确保所有依赖已安装

        Args:
            auto_install: 是否自动安装缺失的依赖

        Returns:
            安装状态
        """
        result = {
            "playwright": {"installed": False, "path": None},
            "chromium": {"installed": False},
            "lightpanda": {"installed": False, "path": None},
            "errors": [],
        }

        # 检查Playwright
        result["playwright"]["installed"] = self.check_playwright_installed()  # type: ignore[index]

        # 检查Chromium
        if result["playwright"]["installed"]:  # type: ignore[index]
            result["chromium"]["installed"] = self.check_chromium_installed()  # type: ignore[index]

        # 检查Lightpanda
        installed, path = self.check_lightpanda_installed()
        result["lightpanda"]["installed"] = installed  # type: ignore[index]
        result["lightpanda"]["path"] = path  # type: ignore[index]

        # 自动安装
        if auto_install:
            if (
                not result["playwright"]["installed"]  # type: ignore[index]
                or not result["chromium"]["installed"]  # type: ignore[index]
            ):
                install_result = self.install_playwright()
                result["playwright"]["installed"] = install_result[  # type: ignore[index]
                    "playwright_installed"
                ]
                result["chromium"]["installed"] = install_result["chromium_installed"]  # type: ignore[index]
                result["errors"].extend(install_result["errors"])  # type: ignore[attr-defined]

            if not result["lightpanda"]["installed"]:  # type: ignore[index]
                install_result = self.install_lightpanda()
                result["lightpanda"]["installed"] = install_result[  # type: ignore[index]
                    "lightpanda_installed"
                ]
                result["lightpanda"]["path"] = install_result["lightpanda_path"]  # type: ignore[index]
                result["errors"].extend(install_result["errors"])  # type: ignore[attr-defined]

        return result

    def update_all(self) -> Dict:
        """
        更新所有依赖到最新版本

        Returns:
            更新结果
        """
        result = {"playwright_updated": False, "chromium_updated": False, "errors": []}

        # 更新Playwright
        try:
            print("[Installer] 正在更新 Playwright...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "playwright"],
                check=True,
                capture_output=True,
            )
            result["playwright_updated"] = True
            print("[Installer] Playwright 更新成功")
        except subprocess.CalledProcessError as e:
            result["errors"].append(f"Playwright更新失败: {e}")  # type: ignore[attr-defined]

        # 更新Chromium
        try:
            print("[Installer] 正在更新 Chromium...")
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
                capture_output=True,
            )
            result["chromium_updated"] = True
            print("[Installer] Chromium 更新成功")
        except subprocess.CalledProcessError as e:
            result["errors"].append(f"Chromium更新失败: {e}")  # type: ignore[attr-defined]

        return result


# ==================== 便捷函数 ====================

_installer: Optional[BrowserInstaller] = None


def get_installer() -> BrowserInstaller:
    """获取全局安装器实例"""
    global _installer
    if _installer is None:
        _installer = BrowserInstaller()
    return _installer


def ensure_browser_installed(auto_install: bool = True) -> Dict:
    """
    确保浏览器依赖已安装

    Args:
        auto_install: 是否自动安装

    Returns:
        安装状态
    """
    return get_installer().ensure_installed(auto_install)


def update_dependencies() -> Dict:
    """
    更新所有依赖到最新版本

    Returns:
        更新结果
    """
    return get_installer().update_all()


def check_lightpanda() -> Tuple[bool, Optional[str]]:
    """
    检查Lightpanda是否可用

    Returns:
        (是否可用, 路径)
    """
    return get_installer().check_lightpanda_installed()
