"""
ScriptHelper - Windows脚本替代工具

替代 .bat/.ps1/.vbs 脚本，统一使用Python执行。
支持管理员权限检测和自动提权。

使用方式:
    from quickagents.utils.script_helper import ScriptHelper

    # 检测管理员权限
    if ScriptHelper.is_admin():
        ScriptHelper.run_command('netsh advfirewall set ...')
    else:
        # 自动UAC提权
        ScriptHelper.run_as_admin('netsh advfirewall set ...')
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional


class ScriptHelper:
    """
    Windows脚本替代工具

    功能:
    - 文件/目录操作
    - 进程管理
    - 注册表操作
    - 服务管理
    - 网络配置
    - 管理员权限处理
    """

    # ==================== 权限管理 ====================

    @staticmethod
    def is_admin() -> bool:
        """
        检测是否具有管理员权限

        Returns:
            是否为管理员
        """
        if platform.system() != "Windows":
            # Linux/Mac使用root检测
            return os.geteuid() == 0 if hasattr(os, "geteuid") else True

        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def run_as_admin(cmd: str, show_console: bool = True) -> bool:
        """
        以管理员权限运行命令（UAC提权）

        Args:
            cmd: 要执行的命令
            show_console: 是否显示控制台窗口

        Returns:
            是否成功启动
        """
        if platform.system() != "Windows":
            # 非Windows系统使用sudo
            return ScriptHelper.run_command(f"sudo {cmd}")["success"]

        try:
            import ctypes

            # 使用ShellExecuteW触发UAC
            params = cmd
            if not show_console:
                # 使用PowerShell隐藏窗口
                params = f'powershell -WindowStyle Hidden -Command "{cmd}"'

            ctypes.windll.shell32.ShellExecuteW(
                None,  # hwnd
                "runas",  # 请求管理员权限
                "cmd.exe",  # 程序
                f"/c {params}",  # 参数
                None,  # 工作目录
                1 if show_console else 0,  # SW_SHOWNORMAL or SW_HIDE
            )
            return True
        except Exception as e:
            print(f"UAC提权失败: {e}")
            return False

    @staticmethod
    def require_admin(prompt: bool = True) -> bool:
        """
        要求管理员权限，如无权限则提示或提权

        Args:
            prompt: 是否提示用户

        Returns:
            当前是否具有管理员权限
        """
        if ScriptHelper.is_admin():
            return True

        if prompt:
            print("⚠️ 此操作需要管理员权限")
            print("请选择:")
            print("  1. 自动提权（弹出UAC对话框）")
            print("  2. 手动以管理员身份运行")
            print("  3. 取消操作")

            choice = input("请输入选择 (1/2/3): ").strip()

            if choice == "1":
                # 重新以管理员身份运行当前脚本
                ScriptHelper.restart_as_admin()
            elif choice == "2":
                print("请右键点击脚本，选择'以管理员身份运行'")
                sys.exit(1)
            else:
                return False

        return False

    @staticmethod
    def restart_as_admin() -> None:
        """以管理员身份重新运行当前脚本"""
        if platform.system() != "Windows":
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
            return

        import ctypes

        params = " ".join([f'"{arg}"' if " " in arg else arg for arg in sys.argv])

        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            params,
            None,
            1,  # SW_SHOWNORMAL
        )
        sys.exit(0)

    # ==================== 命令执行 ====================

    @staticmethod
    def run_command(
        cmd: str,
        cwd: str = None,
        timeout: int = 60,
        capture: bool = True,
        check: bool = False,
    ) -> Dict:
        """
        执行命令

        Args:
            cmd: 命令字符串
            cwd: 工作目录
            timeout: 超时时间（秒）
            capture: 是否捕获输出
            check: 是否检查返回码

        Returns:
            {
                'success': bool,
                'returncode': int,
                'stdout': str,
                'stderr': str,
                'duration_ms': int
            }
        """
        import time

        start = time.time()

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=capture,
                text=True,
                cwd=cwd,
                timeout=timeout,
                check=check,
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if capture else "",
                "stderr": result.stderr if capture else "",
                "duration_ms": int((time.time() - start) * 1000),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"命令执行超时 ({timeout}秒)",
                "duration_ms": timeout * 1000,
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "returncode": e.returncode,
                "stdout": e.stdout if capture else "",
                "stderr": e.stderr if capture else str(e),
                "duration_ms": int((time.time() - start) * 1000),
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_ms": 0,
            }

    @staticmethod
    def run_powershell(script: str, admin: bool = False) -> Dict:
        """
        执行PowerShell脚本

        Args:
            script: PowerShell脚本内容
            admin: 是否需要管理员权限

        Returns:
            执行结果
        """
        cmd = f'powershell -ExecutionPolicy Bypass -Command "{script}"'

        if admin and not ScriptHelper.is_admin():
            return ScriptHelper.run_as_admin(cmd)

        return ScriptHelper.run_command(cmd)

    # ==================== 文件操作 ====================

    @staticmethod
    def copy_file(src: str, dst: str, overwrite: bool = True) -> bool:
        """复制文件"""
        import shutil

        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        if dst_path.exists() and not overwrite:
            raise FileExistsError(f"目标文件已存在: {dst}")

        # 确保目标目录存在
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)
        return True

    @staticmethod
    def move_file(src: str, dst: str) -> bool:
        """移动文件"""
        import shutil

        shutil.move(src, dst)
        return True

    @staticmethod
    def delete_file(path: str) -> bool:
        """删除文件"""
        Path(path).unlink(missing_ok=True)
        return True

    @staticmethod
    def create_directory(path: str) -> bool:
        """创建目录"""
        Path(path).mkdir(parents=True, exist_ok=True)
        return True

    @staticmethod
    def delete_directory(path: str, recursive: bool = False) -> bool:
        """删除目录"""
        import shutil

        path_obj = Path(path)
        if recursive:
            shutil.rmtree(path_obj, ignore_errors=True)
        else:
            path_obj.rmdir()
        return True

    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]:
        """列出文件"""
        return [str(f) for f in Path(directory).glob(pattern) if f.is_file()]

    # ==================== 进程管理 ====================

    @staticmethod
    def get_process_list() -> List[Dict]:
        """获取进程列表"""
        try:
            import psutil

            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent"]
            ):
                try:
                    processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cpu": proc.info["cpu_percent"],
                            "memory": proc.info["memory_percent"],
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return processes
        except ImportError:
            # psutil未安装，使用subprocess
            if platform.system() == "Windows":
                result = ScriptHelper.run_command("tasklist /fo csv /nh")
                processes = []
                for line in result["stdout"].strip().split("\n"):
                    if line:
                        parts = line.strip('"').split('","')
                        if len(parts) >= 2:
                            processes.append(
                                {
                                    "name": parts[0],
                                    "pid": int(parts[1]) if parts[1].isdigit() else 0,
                                }
                            )
                return processes
            return []

    @staticmethod
    def kill_process(pid: int = None, name: str = None, force: bool = False) -> bool:
        """
        终止进程

        Args:
            pid: 进程ID
            name: 进程名
            force: 是否强制终止
        """
        if pid:
            try:
                import psutil

                proc = psutil.Process(pid)
                proc.kill() if force else proc.terminate()
                return True
            except ImportError:
                if platform.system() == "Windows":
                    cmd = f"taskkill /pid {pid} /f" if force else f"taskkill /pid {pid}"
                    return ScriptHelper.run_command(cmd)["success"]
        elif name:
            if platform.system() == "Windows":
                cmd = f"taskkill /im {name} /f" if force else f"taskkill /im {name}"
                return ScriptHelper.run_command(cmd)["success"]
        return False

    @staticmethod
    def start_process(cmd: str, cwd: str = None, hidden: bool = False) -> Dict:
        """
        启动进程

        Args:
            cmd: 命令
            cwd: 工作目录
            hidden: 是否隐藏窗口
        """
        if platform.system() == "Windows" and hidden:
            # Windows下使用START命令隐藏窗口
            cmd = f'start /b "" {cmd}'

        return ScriptHelper.run_command(cmd, cwd=cwd)

    # ==================== Windows特有功能 ====================

    @staticmethod
    def create_shortcut(
        target: str, shortcut_path: str, description: str = "", arguments: str = ""
    ) -> bool:
        """
        创建快捷方式（仅Windows）

        Args:
            target: 目标路径
            shortcut_path: 快捷方式路径
            description: 描述
            arguments: 参数
        """
        if platform.system() != "Windows":
            raise NotImplementedError("快捷方式仅支持Windows")

        try:
            import win32com.client

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.Description = description
            shortcut.Arguments = arguments
            shortcut.save()
            return True
        except ImportError:
            # 使用PowerShell创建
            ps_script = f'''
            $ws = New-Object -ComObject WScript.Shell
            $s = $ws.CreateShortcut("{shortcut_path}")
            $s.TargetPath = "{target}"
            $s.Description = "{description}"
            $s.Arguments = "{arguments}"
            $s.Save()
            '''
            return ScriptHelper.run_powershell(ps_script)["success"]

    @staticmethod
    def get_registry_value(key: str, subkey: str, value_name: str) -> Optional[str]:
        """
        读取注册表值（仅Windows）

        Args:
            key: 根键 (HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER等)
            subkey: 子键路径
            value_name: 值名称
        """
        if platform.system() != "Windows":
            return None

        try:
            import winreg

            root_keys = {
                "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
                "HKEY_USERS": winreg.HKEY_USERS,
            }

            hkey = root_keys.get(key.upper())
            if not hkey:
                return None

            with winreg.OpenKey(hkey, subkey) as reg_key:
                value, _ = winreg.QueryValueEx(reg_key, value_name)
                return value
        except Exception as e:
            print(f"读取注册表失败: {e}")
            return None

    @staticmethod
    def set_registry_value(
        key: str, subkey: str, value_name: str, value: str, value_type: str = "REG_SZ"
    ) -> bool:
        """
        写入注册表值（仅Windows，可能需要管理员权限）

        Args:
            key: 根键
            subkey: 子键路径
            value_name: 值名称
            value: 值
            value_type: 值类型 (REG_SZ, REG_DWORD, REG_BINARY等)
        """
        if platform.system() != "Windows":
            return False

        try:
            import winreg

            root_keys = {
                "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            }

            value_types = {
                "REG_SZ": winreg.REG_SZ,
                "REG_DWORD": winreg.REG_DWORD,
                "REG_BINARY": winreg.REG_BINARY,
                "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
            }

            hkey = root_keys.get(key.upper())
            vtype = value_types.get(value_type, winreg.REG_SZ)

            if not hkey:
                return False

            with winreg.CreateKey(hkey, subkey) as reg_key:
                winreg.SetValueEx(reg_key, value_name, 0, vtype, value)
            return True
        except PermissionError:
            print("需要管理员权限才能修改此注册表项")
            return False
        except Exception as e:
            print(f"写入注册表失败: {e}")
            return False

    @staticmethod
    def manage_service(service_name: str, action: str) -> bool:
        """
        管理Windows服务

        Args:
            service_name: 服务名
            action: 操作 (start, stop, restart, status)
        """
        if platform.system() != "Windows":
            return False

        actions = {
            "start": "start",
            "stop": "stop",
            "restart": "restart",
            "status": "query",
        }

        if action not in actions:
            return False

        cmd = f'sc {actions[action]} "{service_name}"'
        result = ScriptHelper.run_command(cmd)

        if action == "status":
            return "RUNNING" in result["stdout"]
        return result["success"]

    @staticmethod
    def get_system_info() -> Dict:
        """获取系统信息"""
        info = {
            "os": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        }

        if platform.system() == "Windows":
            try:
                import wmi

                c = wmi.WMI()
                info["cpu"] = c.Win32_Processor()[0].Name
                info["ram"] = (
                    f"{int(c.Win32_ComputerSystem()[0].TotalPhysicalMemory / (1024**3))} GB"
                )
                info["hostname"] = c.Win32_ComputerSystem()[0].Name
            except ImportError:
                # 使用PowerShell获取
                result = ScriptHelper.run_powershell(
                    "Get-CimInstance Win32_ComputerSystem | ConvertTo-Json"
                )
                if result["success"]:
                    import json

                    data = json.loads(result["stdout"])
                    info["hostname"] = data.get("Name", "")

        return info


# 便捷函数
def run_cmd(cmd: str, **kwargs) -> Dict:
    """便捷执行命令"""
    return ScriptHelper.run_command(cmd, **kwargs)


def is_admin() -> bool:
    """便捷检测管理员权限"""
    return ScriptHelper.is_admin()


def require_admin() -> bool:
    """便捷要求管理员权限"""
    return ScriptHelper.require_admin()
