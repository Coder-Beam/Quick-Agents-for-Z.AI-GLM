"""
Synonym table for keyword matching between Chinese requirements and code.

Maps Chinese business terms to English code naming conventions.
"""

from typing import Dict, List, Tuple, Optional
import re


class SynonymTable:
    """Bilingual synonym lookup for requirement-code matching."""

    def __init__(self):
        self._table: Dict[str, List[str]] = {}
        self._reverse: Dict[str, List[str]] = {}
        self._abbr: Dict[str, str] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        defaults: List[Tuple[str, List[str]]] = [
            ("用户", ["user", "account", "member", "customer"]),
            ("认证", ["auth", "authenticate", "authentication", "login", "signin"]),
            ("登录", ["login", "signin", "sign_in", "log_in"]),
            ("登出", ["logout", "signout", "sign_out", "log_out"]),
            ("注册", ["register", "signup", "sign_up", "create_user"]),
            ("权限", ["permission", "auth", "acl", "access"]),
            ("角色", ["role", "rbac"]),
            ("密码", ["password", "passwd", "pwd", "credential"]),
            ("令牌", ["token", "jwt", "session"]),
            ("订单", ["order", "purchase", "transaction"]),
            ("支付", ["payment", "pay", "checkout", "billing"]),
            ("商品", ["product", "item", "goods", "merchandise"]),
            ("购物车", ["cart", "basket", "shopping_cart"]),
            ("库存", ["inventory", "stock", "warehouse"]),
            ("搜索", ["search", "query", "find", "lookup"]),
            ("通知", ["notification", "notify", "alert", "message"]),
            ("配置", ["config", "configuration", "setting", "preference"]),
            ("日志", ["log", "logger", "logging", "audit"]),
            ("缓存", ["cache", "redis", "memoize"]),
            ("导入", ["import", "load", "ingest"]),
            ("导出", ["export", "download", "generate"]),
            ("验证", ["validate", "verify", "check", "validation"]),
            ("删除", ["delete", "remove", "destroy", "erase"]),
            ("更新", ["update", "modify", "edit", "patch", "put"]),
            ("创建", ["create", "add", "insert", "new", "post"]),
            ("查询", ["query", "search", "find", "get", "fetch", "list"]),
            ("状态", ["status", "state", "phase", "stage"]),
            ("类型", ["type", "category", "kind", "class"]),
            ("列表", ["list", "array", "collection", "items"]),
            ("详情", ["detail", "info", "view", "show", "get"]),
            ("上传", ["upload", "attach", "file"]),
            ("下载", ["download", "export", "save"]),
            ("审批", ["approve", "review", "audit", "workflow"]),
            ("报表", ["report", "dashboard", "chart", "analytics"]),
            ("接口", ["api", "endpoint", "route", "controller"]),
            ("模型", ["model", "entity", "schema", "domain"]),
            ("服务", ["service", "handler", "manager", "provider"]),
            ("数据", ["data", "record", "entry", "row"]),
            ("文件", ["file", "document", "attachment", "resource"]),
            ("时间", ["time", "date", "timestamp", "datetime"]),
            ("金额", ["amount", "price", "cost", "fee", "money"]),
            ("数量", ["quantity", "count", "num", "amount", "total"]),
            ("地址", ["address", "location", "addr"]),
            ("邮箱", ["email", "mail", "mailbox"]),
            ("手机", ["phone", "mobile", "cellphone", "tel"]),
            ("姓名", ["name", "username", "fullname", "nickname"]),
        ]
        for cn, en_list in defaults:
            self._table[cn] = en_list
            for en in en_list:
                self._reverse.setdefault(en, []).append(cn)

        abbreviations = {
            "RBAC": "role_based_access_control",
            "RBAC": "rbac",
            "API": "api",
            "REST": "rest",
            "CRUD": "crud",
            "JWT": "jwt",
            "JSON": "json",
            "XML": "xml",
            "ORM": "orm",
            "MVC": "mvc",
            "DTO": "dto",
            "VO": "vo",
            "DAO": "dao",
            "SSL": "ssl",
            "TLS": "tls",
            "OAuth": "oauth",
            "SSO": "sso",
            "UUID": "uuid",
            "URL": "url",
            "URI": "uri",
            "HTML": "html",
            "CSS": "css",
            "SQL": "sql",
            "DDL": "ddl",
            "DML": "dml",
        }
        self._abbr = abbreviations

    def lookup(self, term: str) -> List[str]:
        """Look up synonyms for a term (Chinese or English)."""
        results: List[str] = []
        term_lower = term.lower().strip()

        if term in self._table:
            results.extend(self._table[term])

        if term_lower in self._reverse:
            results.extend(self._reverse[term_lower])

        if term.upper() in self._abbr:
            expanded = self._abbr[term.upper()]
            results.append(expanded)

        return list(dict.fromkeys(results))

    def match_score(self, chinese_term: str, english_name: str) -> float:
        """Calculate match score between a Chinese term and English code name."""
        synonyms = self.lookup(chinese_term)
        if not synonyms:
            return 0.0

        en_lower = english_name.lower()
        for syn in synonyms:
            if en_lower == syn:
                return 1.0
            if syn in en_lower or en_lower in syn:
                return 0.8

        for syn in synonyms:
            if self._partial_match(syn, en_lower):
                return 0.6

        return 0.0

    @staticmethod
    def _partial_match(pattern: str, text: str) -> bool:
        parts = re.split(r'[_\s]+', pattern)
        return any(p in text for p in parts if len(p) >= 3)

    def add_synonym(self, chinese: str, english: str) -> None:
        self._table.setdefault(chinese, []).append(english.lower())
        self._reverse.setdefault(english.lower(), []).append(chinese)

    def add_custom_terms(self, term_map: Dict[str, List[str]]) -> None:
        for cn, en_list in term_map.items():
            for en in en_list:
                self.add_synonym(cn, en)
