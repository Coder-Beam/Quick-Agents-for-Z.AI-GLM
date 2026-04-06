"""
ProjectDetector - 本地项目类型检测

通过文件模式匹配检测项目类型、技术栈、框架。
完全本地化，0 Token消耗。

使用方式:
    detector = ProjectDetector('/path/to/project')
    info = detector.detect()
    print(info.type)        # 'python', 'node', 'rust', ...
    print(info.languages)   # ['python', 'typescript']
    print(info.frameworks)  # ['fastapi', 'vue']
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class ProjectInfo:
    """项目检测结果"""

    path: str
    type: str = "unknown"
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    build_tools: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    has_tests: bool = False
    has_ci: bool = False
    has_docker: bool = False
    confidence: float = 0.0
    markers_found: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "path": self.path,
            "type": self.type,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "build_tools": self.build_tools,
            "package_managers": self.package_managers,
            "databases": self.databases,
            "has_tests": self.has_tests,
            "has_ci": self.has_ci,
            "has_docker": self.has_docker,
            "confidence": self.confidence,
            "markers_found": self.markers_found,
        }


# 文件标记 → 项目类型/语言映射
_FILE_MARKERS = {
    # Python
    "pyproject.toml": {"type": "python", "lang": "python", "build": "poetry/setuptools"},
    "setup.py": {"type": "python", "lang": "python", "build": "setuptools"},
    "setup.cfg": {"type": "python", "lang": "python", "build": "setuptools"},
    "requirements.txt": {"type": "python", "lang": "python", "pkg": "pip"},
    "Pipfile": {"type": "python", "lang": "python", "pkg": "pipenv"},
    "poetry.lock": {"type": "python", "lang": "python", "build": "poetry"},
    "uv.lock": {"type": "python", "lang": "python", "build": "uv"},
    "manage.py": {"type": "python", "lang": "python", "framework": "django"},
    # Node.js / JavaScript / TypeScript
    "package.json": {"type": "node", "lang": "javascript", "pkg": "npm"},
    "pnpm-lock.yaml": {"type": "node", "lang": "javascript", "pkg": "pnpm"},
    "yarn.lock": {"type": "node", "lang": "javascript", "pkg": "yarn"},
    "bun.lockb": {"type": "node", "lang": "javascript", "pkg": "bun"},
    ".nvmrc": {"type": "node", "lang": "javascript"},
    # Rust
    "Cargo.toml": {"type": "rust", "lang": "rust", "build": "cargo"},
    "Cargo.lock": {"type": "rust", "lang": "rust", "build": "cargo"},
    # Go
    "go.mod": {"type": "go", "lang": "go", "build": "go-modules"},
    "go.sum": {"type": "go", "lang": "go"},
    # Java / JVM
    "pom.xml": {"type": "java", "lang": "java", "build": "maven"},
    "build.gradle": {"type": "java", "lang": "java", "build": "gradle"},
    "build.gradle.kts": {"type": "java", "lang": "kotlin", "build": "gradle"},
    # C# / .NET
    "*.csproj": {"type": "dotnet", "lang": "csharp", "build": "msbuild"},
    "*.sln": {"type": "dotnet", "lang": "csharp", "build": "msbuild"},
    # Ruby
    "Gemfile": {"type": "ruby", "lang": "ruby", "pkg": "bundler"},
    # PHP
    "composer.json": {"type": "php", "lang": "php", "pkg": "composer"},
    # Swift / Apple
    "Package.swift": {"type": "swift", "lang": "swift", "build": "spm"},
    # Docker
    "Dockerfile": {"type": "container", "docker": True},
    "docker-compose.yml": {"type": "container", "docker": True},
    "docker-compose.yaml": {"type": "container", "docker": True},
    # CI
    ".github/workflows": {"ci": "github-actions"},
    ".gitlab-ci.yml": {"ci": "gitlab-ci"},
    "Jenkinsfile": {"ci": "jenkins"},
    ".circleci": {"ci": "circleci"},
}

# package.json 中的依赖 → 框架映射
_NPM_FRAMEWORKS = {
    "react": "react",
    "react-dom": "react",
    "vue": "vue",
    "@vue/cli-service": "vue",
    "nuxt": "nuxt",
    "@angular/core": "angular",
    "@sveltejs/kit": "sveltekit",
    "svelte": "svelte",
    "next": "nextjs",
    "express": "express",
    "fastify": "fastify",
    "nestjs": "nestjs",
    "@hono/node-server": "hono",
    "electron": "electron",
    "tailwindcss": "tailwind",
    "@chakra-ui/react": "chakra-ui",
    "@mui/material": "material-ui",
}

# pyproject.toml / requirements.txt 中的依赖 → 框架映射
_PYTHON_FRAMEWORKS = {
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "sanic": "sanic",
    "starlette": "starlette",
    "tornado": "tornado",
    "aiohttp": "aiohttp",
    "celery": "celery",
    "sqlalchemy": "sqlalchemy",
    "pydantic": "pydantic",
    "scrapy": "scrapy",
    "streamlit": "streamlit",
    "gradio": "gradio",
}

# 数据库标记
_DB_MARKERS = {
    "prisma": "prisma",
    "drizzle-orm": "drizzle",
    "mongoose": "mongodb",
    "sequelize": "sequelize",
    "typeorm": "typeorm",
    "prisma": "postgresql",
    "alembic": "postgresql",
    "redis": "redis",
    "mongodb": "mongodb",
}


class ProjectDetector:
    """
    本地项目类型检测器

    通过文件模式匹配检测项目类型、技术栈、框架。
    完全基于文件系统操作，不需要LLM，0 Token消耗。

    使用方式:
        detector = ProjectDetector('/path/to/project')
        info = detector.detect()
    """

    def __init__(self, project_path: str = "."):
        """
        初始化检测器

        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path).resolve()

    def detect(self) -> ProjectInfo:
        """
        执行项目检测

        Returns:
            ProjectInfo 项目信息
        """
        info = ProjectInfo(path=str(self.project_path))
        score = 0

        # 1. 扫描标记文件
        for marker, attrs in _FILE_MARKERS.items():
            marker_path = self.project_path / marker
            if marker_path.exists():
                info.markers_found[marker] = str(marker_path)

                if "type" in attrs and info.type == "unknown":
                    info.type = attrs["type"]
                    score += 30

                if "lang" in attrs and attrs["lang"] not in info.languages:
                    info.languages.append(attrs["lang"])
                    score += 10

                if "build" in attrs and attrs["build"] not in info.build_tools:
                    info.build_tools.append(attrs["build"])
                    score += 5

                if "pkg" in attrs and attrs["pkg"] not in info.package_managers:
                    info.package_managers.append(attrs["pkg"])
                    score += 5

                if "framework" in attrs and attrs["framework"] not in info.frameworks:
                    info.frameworks.append(attrs["framework"])
                    score += 10

                if attrs.get("docker"):
                    info.has_docker = True
                    score += 5

                if attrs.get("ci"):
                    info.has_ci = True
                    score += 5

        # 2. 检测 .csproj / .sln (glob模式)
        if not info.markers_found:
            csproj_files = list(self.project_path.glob("*.csproj"))
            sln_files = list(self.project_path.glob("*.sln"))
            if csproj_files or sln_files:
                info.type = "dotnet"
                info.languages.append("csharp")
                info.build_tools.append("msbuild")
                score += 30

        # 3. 分析 package.json (Node.js框架)
        pkg_json = self.project_path / "package.json"
        if pkg_json.exists():
            info = self._analyze_package_json(pkg_json, info, score)

        # 4. 分析 pyproject.toml (Python框架)
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            info = self._analyze_pyproject(pyproject, info)

        # 5. 检测 requirements.txt
        reqs = self.project_path / "requirements.txt"
        if reqs.exists():
            info = self._analyze_requirements(reqs, info)

        # 6. 检测测试目录
        info.has_tests = self._detect_tests()

        # 7. 检测TypeScript
        if (self.project_path / "tsconfig.json").exists():
            if "typescript" not in info.languages:
                info.languages.append("typescript")
            score += 10

        # 8. 计算置信度
        info.confidence = min(1.0, score / 100)

        # 去重
        info.languages = list(dict.fromkeys(info.languages))
        info.frameworks = list(dict.fromkeys(info.frameworks))
        info.build_tools = list(dict.fromkeys(info.build_tools))
        info.package_managers = list(dict.fromkeys(info.package_managers))

        return info

    def _analyze_package_json(self, pkg_json: Path, info: ProjectInfo, score: int = 0) -> ProjectInfo:
        """分析package.json检测框架"""
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            for dep_name in deps:
                # 检测框架
                if dep_name in _NPM_FRAMEWORKS:
                    fw = _NPM_FRAMEWORKS[dep_name]
                    if fw not in info.frameworks:
                        info.frameworks.append(fw)

                # 检测数据库
                if dep_name in _DB_MARKERS:
                    db = _DB_MARKERS[dep_name]
                    if db not in info.databases:
                        info.databases.append(db)

            # 检测TypeScript
            if "typescript" in deps or (self.project_path / "tsconfig.json").exists():
                if "typescript" not in info.languages:
                    info.languages.append("typescript")

        except (json.JSONDecodeError, OSError):
            pass

        return info

    def _analyze_pyproject(self, pyproject: Path, info: ProjectInfo) -> ProjectInfo:
        """分析pyproject.toml检测框架"""
        try:
            content = pyproject.read_text(encoding="utf-8")
            for dep_marker, fw_name in _PYTHON_FRAMEWORKS.items():
                if dep_marker in content.lower():
                    if fw_name not in info.frameworks:
                        info.frameworks.append(fw_name)
        except OSError:
            pass

        return info

    def _analyze_requirements(self, reqs: Path, info: ProjectInfo) -> ProjectInfo:
        """分析requirements.txt检测框架"""
        try:
            content = reqs.read_text(encoding="utf-8").lower()
            for dep_marker, fw_name in _PYTHON_FRAMEWORKS.items():
                if dep_marker in content:
                    if fw_name not in info.frameworks:
                        info.frameworks.append(fw_name)
        except OSError:
            pass

        return info

    def _detect_tests(self) -> bool:
        """检测测试目录/文件"""
        test_markers = [
            "tests",
            "test",
            "spec",
            "__tests__",
            "pytest.ini",
            "jest.config.js",
            "jest.config.ts",
            "vitest.config.ts",
            "karma.conf.js",
        ]
        for marker in test_markers:
            if (self.project_path / marker).exists():
                return True

        # 检测测试文件
        for pattern in ["test_*.py", "*_test.py", "*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js"]:
            if list(self.project_path.rglob(pattern))[:1]:
                return True

        return False


# 全局实例
_global_detector: Optional[ProjectDetector] = None


def get_project_detector(project_path: str = ".") -> ProjectDetector:
    """获取全局项目检测器"""
    global _global_detector
    if _global_detector is None:
        _global_detector = ProjectDetector(project_path)
    return _global_detector


def detect_project(project_path: str = ".") -> ProjectInfo:
    """便捷函数：检测项目类型"""
    return ProjectDetector(project_path).detect()
