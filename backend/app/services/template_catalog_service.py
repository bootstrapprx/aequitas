"""
Template Catalog Service

Loads the enriched master chart JSON as a read-only catalog for optional account selection.
This does not mutate the database or require the enriched chart to be seeded.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "enriched_master_chart.json"
TYPE_MAP = {"Header": "H", "Detail": "D", "H": "H", "D": "D"}


def _normalize_tags(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


@lru_cache(maxsize=1)
def _load_catalog_accounts() -> Tuple[Dict[str, Any], ...]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catalog file not found at {CATALOG_PATH}")

    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        raw_accounts = json.load(handle)

    normalized: List[Dict[str, Any]] = []
    code_to_header_id: Dict[str, str] = {}
    code_to_first_id: Dict[str, str] = {}

    for index, row in enumerate(raw_accounts):
        code = str(row.get("code", "")).strip()
        if not code:
            continue

        parent_code = row.get("parent_code") or None
        account_type = TYPE_MAP.get(row.get("type"), "D")
        tags = _normalize_tags(row.get("tags"))
        account_id = f"{code}::{account_type}::{index}"

        if code not in code_to_first_id:
            code_to_first_id[code] = account_id
        if account_type == "H":
            code_to_header_id[code] = account_id

        normalized.append(
            {
                "id": account_id,
                "code": code,
                "description": row.get("description") or "",
                "long_description": row.get("long_description") or None,
                "type": account_type,
                "category": row.get("category") or "",
                "parent_code": parent_code,
                "parent_id": None,
                "normal_balance": row.get("normal_balance") or None,
                "fs_mapping": row.get("fs_mapping") or None,
                "cash_flow_classification": row.get("cash_flow_classification") or None,
                "notes": row.get("notes") or None,
                "start_date": row.get("start_date") or None,
                "end_date": row.get("end_date") or None,
                "tags": tags,
            }
        )

    id_to_parent_id: Dict[str, Optional[str]] = {}
    for account in normalized:
        parent_code = account.get("parent_code")
        parent_id = None
        if parent_code:
            parent_id = code_to_header_id.get(parent_code) or code_to_first_id.get(parent_code)
        if parent_id == account["id"]:
            parent_id = None
        account["parent_id"] = parent_id
        id_to_parent_id[account["id"]] = parent_id

    level_map: Dict[str, int] = {}
    visiting: Set[str] = set()

    def resolve_level(account_id: str) -> int:
        if account_id in level_map:
            return level_map[account_id]
        if account_id in visiting:
            return 1
        visiting.add(account_id)
        parent = id_to_parent_id.get(account_id)
        if not parent or parent not in id_to_parent_id:
            level = 1
        else:
            level = resolve_level(parent) + 1
        visiting.remove(account_id)
        level_map[account_id] = level
        return level

    for account in normalized:
        account["level"] = resolve_level(account["id"])

    normalized.sort(key=lambda acc: acc["code"])
    return tuple(normalized)


class TemplateCatalogService:
    """Provides read-only access to the template account catalog."""

    def get_accounts(self) -> List[Dict[str, Any]]:
        return [dict(account) for account in _load_catalog_accounts()]

    def get_account_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        for account in _load_catalog_accounts():
            if account.get("code") == code:
                return dict(account)
        return None

    def get_account_by_id(self, catalog_id: str) -> Optional[Dict[str, Any]]:
        for account in _load_catalog_accounts():
            if account.get("id") == catalog_id:
                return dict(account)
        return None

    def build_tree(self, accounts: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        nodes: Dict[str, Dict[str, Any]] = {}
        for account in accounts:
            node = dict(account)
            node["children"] = []
            nodes[node["id"]] = node

        roots: List[Dict[str, Any]] = []
        for node in nodes.values():
            parent_id = node.get("parent_id")
            if parent_id and parent_id in nodes:
                nodes[parent_id]["children"].append(node)
            else:
                roots.append(node)

        for node in nodes.values():
            node["children"].sort(key=lambda child: child["code"])
        roots.sort(key=lambda root: root["code"])
        return roots

    def get_stats(self, accounts: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        accounts_list = list(accounts)
        codes = {account.get("code") for account in accounts_list}
        missing_parents = sorted(
            {
                account.get("code")
                for account in accounts_list
                if account.get("parent_code") and account.get("parent_code") not in codes
            }
        )
        max_depth = max((account.get("level", 1) for account in accounts_list), default=0)
        header_count = sum(1 for account in accounts_list if account.get("type") == "H")
        detail_count = len(accounts_list) - header_count

        return {
            "total_accounts": len(accounts_list),
            "header_count": header_count,
            "detail_count": detail_count,
            "max_depth": max_depth,
            "orphans": len(missing_parents),
            "missing_parents": missing_parents,
            "needs_rebuild": False,
        }
