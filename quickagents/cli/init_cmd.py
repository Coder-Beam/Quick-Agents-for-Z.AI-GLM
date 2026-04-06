"""
QuickAgents Init Command - qka init

Initializes QuickAgents in a project directory with all necessary configuration files.

Usage:
    qka init                    # Interactive initialization
    qka init --force            # Overwrite existing files
    qka init --dry-run          # Preview without making changes
    qka init --minimal          # Only essential files (no agents/skills)
    qka init --with-ui-ux       # Include ui-ux-pro-max skill (~410KB)
    qka init --update-config    # Only update config files, preserve data
"""

import os
import sys
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Set
import logging

logger = logging.getLogger(__name__)

# Template directory (inside the pip package)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Files that should NOT be installed (development/runtime files)
EXCLUDE_PATTERNS = [
    "node_modules",
    "__pycache__",
    "*.pyc",
    ".git",
    "bun.lock",
    "package-lock.json",
    ".gitignore",
    "README.md",  # Template READMEs, not user-facing
    "EVOLUTION.md",  # Runtime generated
    "registry.json",  # Runtime generated
    "snapshots",
    "traces",
    "evaluation",
]

# Default skills to install
DEFAULT_SKILLS = [
    "doom-loop-skill",
    "event-reminder-skill",
    "feedback-collector-skill",
    "project-memory-skill",
    "version-alignment-skill",
    "glm-version-sync-skill",
    "yugong-loop-skill",
]

# Optional skills (require --with-* flag)
OPTIONAL_SKILLS = {
    "ui-ux-pro-max": {
        "flag": "--with-ui-ux",
        "description": "UI/UX design assistant (~410KB, for web/mobile projects)",
        "size_kb": 410,
    },
    "browser-devtools-skill": {
        "flag": "--with-browser",
        "description": "Browser automation with Playwright",
        "size_kb": 10,
    },
}


class InitCommand:
    """QuickAgents initialization command."""

    def __init__(
        self,
        project_dir: Path = None,
        force: bool = False,
        dry_run: bool = False,
        minimal: bool = False,
        with_ui_ux: bool = False,
        with_browser: bool = False,
        update_config_only: bool = False,
    ):
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.force = force
        self.dry_run = dry_run
        self.minimal = minimal
        self.with_ui_ux = with_ui_ux
        self.with_browser = with_browser
        self.update_config_only = update_config_only

        self.templates_dir = TEMPLATES_DIR
        self.installed_files: List[str] = []
        self.skipped_files: List[str] = []
        self.backup_dir: Optional[Path] = None

    def run(self) -> bool:
        """Execute the initialization."""
        from .. import __version__

        print("=" * 60)
        print(f"QuickAgents v{__version__} - Project Initialization")
        print("=" * 60)
        print()

        # 1. Validate templates directory exists
        if not self.templates_dir.exists():
            print(f"[FAIL] Templates directory not found: {self.templates_dir}")
            print("  Please reinstall quickagents: pip install --force-reinstall quickagents")
            return False

        # 2. Check project directory state
        state = self._analyze_project_state()
        self._print_project_state(state)

        # 3. Create backup if needed
        if state["has_existing"] and not self.dry_run:
            self._create_backup()

        # 4. Install files
        if self.dry_run:
            print("\n[DRY-RUN] Preview mode - no changes will be made\n")

        success = self._install_all(state)

        # 5. Initialize database
        if success and not self.dry_run:
            self._initialize_database()

        # 6. Print summary
        self._print_summary()

        return success

    def _analyze_project_state(self) -> Dict:
        """Analyze the current state of the project directory."""
        opencode_dir = self.project_dir / ".opencode"
        agents_md = self.project_dir / "AGENTS.md"
        opencode_json = self.project_dir / "opencode.json"
        docs_dir = self.project_dir / "Docs"

        return {
            "is_empty": not any(self.project_dir.iterdir()) if self.project_dir.exists() else True,
            "has_existing": opencode_dir.exists() or agents_md.exists(),
            "has_opencode": opencode_dir.exists(),
            "has_agents_md": agents_md.exists(),
            "has_opencode_json": opencode_json.exists(),
            "has_docs": docs_dir.exists(),
            "is_git_repo": (self.project_dir / ".git").exists(),
        }

    def _print_project_state(self, state: Dict):
        """Print the current project state."""
        print(f"Project Directory: {self.project_dir}")
        print(f"  Git Repository: {'Yes' if state['is_git_repo'] else 'No'}")
        print(f"  Existing .opencode: {'Yes' if state['has_opencode'] else 'No'}")
        print(f"  Existing AGENTS.md: {'Yes' if state['has_agents_md'] else 'No'}")
        print()

        if state["has_existing"] and not self.force:
            print("[WARN] Existing QuickAgents configuration detected!")
            print("  Use --force to overwrite existing files")
            print("  Use --update-config to only update config files")
            print()

    def _create_backup(self):
        """Create backup of existing configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_dir / ".quickagents" / "backups" / f"init_{timestamp}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup .opencode directory
        opencode_src = self.project_dir / ".opencode"
        if opencode_src.exists():
            shutil.copytree(opencode_src, self.backup_dir / ".opencode", dirs_exist_ok=True)

        # Backup AGENTS.md
        agents_src = self.project_dir / "AGENTS.md"
        if agents_src.exists():
            shutil.copy2(agents_src, self.backup_dir / "AGENTS.md")

        # Backup opencode.json
        json_src = self.project_dir / "opencode.json"
        if json_src.exists():
            shutil.copy2(json_src, self.backup_dir / "opencode.json")

        print(f"[BACKUP] Created: {self.backup_dir}")

    def _install_all(self, state: Dict) -> bool:
        """Install all necessary files."""
        try:
            # Root files
            self._install_root_files()

            # .opencode directory
            if not self.minimal:
                self._install_opencode_structure()

            # Docs directory
            self._install_docs_templates()

            # Optional skills
            if self.with_ui_ux:
                self._install_optional_skill("ui-ux-pro-max")
            if self.with_browser:
                self._install_optional_skill("browser-devtools-skill")

            return True
        except Exception as e:
            logger.exception("Installation failed")
            print(f"\n[FAIL] Installation error: {e}")
            return False

    def _install_root_files(self):
        """Install root-level files (AGENTS.md, opencode.json)."""
        # AGENTS.md
        src = self.templates_dir / "AGENTS.md"
        dst = self.project_dir / "AGENTS.md"

        if dst.exists() and not self.force:
            self.skipped_files.append(str(dst))
            print(f"  [SKIP] AGENTS.md (exists, use --force to overwrite)")
        else:
            if self.dry_run:
                print(f"  [WOULD CREATE] AGENTS.md")
            else:
                shutil.copy2(src, dst)
                self.installed_files.append(str(dst))
                print(f"  [OK] AGENTS.md")

        # opencode.json
        src = self.templates_dir / "opencode.json"
        dst = self.project_dir / "opencode.json"

        if dst.exists() and not self.force:
            self.skipped_files.append(str(dst))
            print(f"  [SKIP] opencode.json (exists)")
        else:
            if self.dry_run:
                print(f"  [WOULD CREATE] opencode.json")
            else:
                shutil.copy2(src, dst)
                self.installed_files.append(str(dst))
                print(f"  [OK] opencode.json")

    def _install_opencode_structure(self):
        """Install the .opencode directory structure."""
        print("\n[.opencode/] Installing structure...")

        opencode_dst = self.project_dir / ".opencode"

        # Install each component
        components = [
            ("agents", "Agents"),
            ("commands", "Commands"),
            ("hooks", "Hooks"),
            ("config", "Config"),
            ("plugins", "Plugins"),
            ("memory", "Memory"),
            ("skills", "Skills"),
        ]

        for comp_dir, comp_name in components:
            self._install_component(comp_dir, comp_name)

    def _install_component(self, comp_dir: str, comp_name: str):
        """Install a single component directory."""
        src_dir = self.templates_dir / "opencode" / comp_dir
        dst_dir = self.project_dir / ".opencode" / comp_dir

        if not src_dir.exists():
            print(f"  [SKIP] {comp_name} (not in templates)")
            return

        # Special handling for skills
        if comp_dir == "skills":
            self._install_skills()
            return

        if self.dry_run:
            file_count = sum(1 for _ in src_dir.rglob("*") if _.is_file())
            print(f"  [WOULD CREATE] {comp_name}/ ({file_count} files)")
            return

        # Create directory and copy files
        dst_dir.mkdir(parents=True, exist_ok=True)

        for item in src_dir.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(src_dir)
                dst_file = dst_dir / rel_path

                # Skip excluded patterns
                if any(pattern in str(item) for pattern in EXCLUDE_PATTERNS):
                    continue

                dst_file.parent.mkdir(parents=True, exist_ok=True)

                if dst_file.exists() and not self.force:
                    self.skipped_files.append(str(dst_file))
                else:
                    shutil.copy2(item, dst_file)
                    self.installed_files.append(str(dst_file))

        file_count = sum(1 for _ in dst_dir.rglob("*") if _.is_file())
        print(f"  [OK] {comp_name}/ ({file_count} files)")

    def _install_skills(self):
        """Install skills with selection logic."""
        print("\n[.opencode/skills/] Installing skills...")

        dst_skills_dir = self.project_dir / ".opencode" / "skills"
        src_skills_dir = self.templates_dir / "opencode" / "skills"

        if self.dry_run:
            print(f"  Default skills: {len(DEFAULT_SKILLS)}")
            if self.with_ui_ux:
                print(f"  Optional: ui-ux-pro-max")
            return

        dst_skills_dir.mkdir(parents=True, exist_ok=True)

        # Install default skills
        for skill_name in DEFAULT_SKILLS:
            src = src_skills_dir / skill_name
            dst = dst_skills_dir / skill_name

            if src.exists():
                if dst.exists() and not self.force:
                    print(f"    [SKIP] {skill_name} (exists)")
                else:
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    print(f"    [OK] {skill_name}")
            else:
                print(f"    [WARN] {skill_name} not found in templates")

    def _install_optional_skill(self, skill_name: str):
        """Install an optional skill."""
        print(f"\n[Optional] Installing {skill_name}...")

        src = self.templates_dir / "skills-optional" / skill_name
        dst = self.project_dir / ".opencode" / "skills" / skill_name

        if not src.exists():
            print(f"  [FAIL] {skill_name} not found in templates")
            return

        if self.dry_run:
            file_count = sum(1 for _ in src.rglob("*") if _.is_file())
            print(f"  [WOULD CREATE] {skill_name}/ ({file_count} files)")
            return

        if dst.exists():
            shutil.rmtree(dst)

        shutil.copytree(src, dst)
        file_count = sum(1 for _ in dst.rglob("*") if _.is_file())
        print(f"  [OK] {skill_name}/ ({file_count} files)")

    def _install_docs_templates(self):
        """Install Docs/ directory templates."""
        print("\n[Docs/] Installing templates...")

        src_docs = self.templates_dir / "docs"
        dst_docs = self.project_dir / "Docs"

        if self.dry_run:
            file_count = sum(1 for _ in src_docs.rglob("*") if _.is_file())
            print(f"  [WOULD CREATE] Docs/ ({file_count} files)")
            return

        dst_docs.mkdir(parents=True, exist_ok=True)

        for item in src_docs.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(src_docs)
                dst_file = dst_docs / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)

                if dst_file.exists() and not self.force:
                    self.skipped_files.append(str(dst_file))
                else:
                    shutil.copy2(item, dst_file)
                    self.installed_files.append(str(dst_file))

        file_count = sum(1 for _ in dst_docs.rglob("*") if _.is_file())
        print(f"  [OK] Docs/ ({file_count} files)")

    def _initialize_database(self):
        """Initialize the UnifiedDB."""
        print("\n[Database] Initializing...")

        try:
            from ..core.unified_db import UnifiedDB

            db_path = self.project_dir / ".quickagents" / "unified.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

            db = UnifiedDB(str(db_path))

            # Set initial memory
            from ..core.memory import MemoryType

            db.set_memory("project.name", self.project_dir.name, MemoryType.FACTUAL)
            db.set_memory("project.path", str(self.project_dir), MemoryType.FACTUAL)
            db.set_memory(
                "project.initialized",
                datetime.now().isoformat(),
                MemoryType.FACTUAL,
            )

            db.close()
            print(f"  [OK] Database: {db_path}")

        except Exception as e:
            print(f"  [WARN] Database initialization failed: {e}")
            print("  You can initialize manually: qka init-db")

    def _print_summary(self):
        """Print installation summary."""
        from .. import __version__

        print("\n" + "=" * 60)
        print("Installation Summary")
        print("=" * 60)
        print(f"  Files installed: {len(self.installed_files)}")
        print(f"  Files skipped: {len(self.skipped_files)}")

        if self.backup_dir:
            print(f"  Backup location: {self.backup_dir}")

        if self.dry_run:
            print("\n[DRY-RUN] No changes were made.")
            print("  Remove --dry-run to execute installation.")
        else:
            print("\n[OK] QuickAgents initialized successfully!")
            print()
            print("  Next steps:")
            print("    1. Review AGENTS.md for project-specific instructions")
            print("    2. Configure models in .opencode/config/models.json")
            print("    3. Start using QuickAgents: 启动QuickAgent")

        print()


def cmd_init(args):
    """CLI entry point for qka init command."""
    project_dir = getattr(args, "project_dir", None)
    force = getattr(args, "force", False)
    dry_run = getattr(args, "dry_run", False)
    minimal = getattr(args, "minimal", False)
    with_ui_ux = getattr(args, "with_ui_ux", False)
    with_browser = getattr(args, "with_browser", False)
    update_config = getattr(args, "update_config", False)

    cmd = InitCommand(
        project_dir=Path(project_dir) if project_dir else None,
        force=force,
        dry_run=dry_run,
        minimal=minimal,
        with_ui_ux=with_ui_ux,
        with_browser=with_browser,
        update_config_only=update_config,
    )

    success = cmd.run()
    sys.exit(0 if success else 1)
