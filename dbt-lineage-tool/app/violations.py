import re
import sqlglot
from sqlglot import exp


class ViolationDetector:
    def __init__(self, loader, use_raw=False):
        self.loader = loader
        self.use_raw = use_raw
        # dbt model names (normalized)
        self.dbt_models = self._load_dbt_models()
        # dbt sources (optional)
        self.dbt_sources = self._load_dbt_sources()

    # ----------------------------
    # LOAD MODELS
    # ----------------------------
    def _load_dbt_models(self):
        models = self.loader.get_models()
        # only model names (important)
        return {v["name"] for v in models.values()}

    # ----------------------------
    # LOAD SOURCES
    # ----------------------------
    def _load_dbt_sources(self):
        sources = self.loader.manifest.get("sources", {})
        result = set()
        for _, v in sources.items():
            name = v.get("name")
            if name:
                result.add(name)
        return result

    # ----------------------------
    # RAW SQL ACCESS
    # ----------------------------
    def _get_raw_sql(self, model):
        node = self.loader.manifest["nodes"].get(model)
        if not node:
            return None
        return node.get("raw_code")

    # ----------------------------
    # SQL EXTRACTION (dbt 1.11 safe)
    # ----------------------------
    def _extract_tables(self, sql):
        """Parse SQL and return a set of table identifiers.
        - Strips Jinja ``{{ … }}`` blocks before parsing because ``sqlglot`` cannot handle them.
        - Keeps the full ``schema.table`` name (if present).
        - Removes CTE names so they are not reported as hard‑coded tables.
        """
        if not sql:
            return set()
        # Remove Jinja templating to avoid parse errors
        cleaned_sql = re.sub(r"\{\{.*?\}\}", "", sql, flags=re.DOTALL)
        try:
            parsed = sqlglot.parse_one(cleaned_sql)
            tables = set()
            cte_names = set()
            # collect CTE names to filter them out later
            for cte in parsed.find_all(exp.CTE):
                if isinstance(cte, exp.CTE) and cte.alias:
                    cte_names.add(cte.alias)
            for t in parsed.find_all(exp.Table):
                full_name = t.name
                if full_name in cte_names:
                    continue
                tables.add(full_name)
            return tables
        except Exception:
            # Silently ignore parsing failures – they usually stem from leftover Jinja
            return set()

    # ----------------------------
    # MAIN LOGIC
    # ----------------------------
    def get_violations(self, model, use_raw=None):
        """Return a list of hard‑coded tables for *model*.
        If *use_raw* is True, we analyse the raw (Jinja‑templated) code so
        any direct reference to another dbt model is considered a violation.
        If False (or None), we fall back to the default behaviour which
        expects compiled code where dbt‑managed references are already
        resolved to fully‑qualified names.
        """
        if use_raw is None:
            use_raw = self.use_raw
        sql = self._get_raw_sql(model) if use_raw else self.loader.get_sql(model)
        if not sql:
            return []
        tables = self._extract_tables(sql)
        violations = set()
        for table in tables:
            base_name = table.split('.')[-1]
            is_model = base_name in self.dbt_models
            is_source = base_name in self.dbt_sources
            if use_raw:
                # Any reference to a known model in raw code is a hard‑coded usage
                if is_model:
                    violations.add(table)
                elif not is_model and not is_source:
                    violations.add(table)
            else:
                if not is_model and not is_source:
                    violations.add(table)
        return sorted(list(violations))

    def find_hardcoded_tables(self):
        """Return a mapping of model name → list of hard‑coded tables detected.
        Iterates over every model in the manifest and uses ``get_violations``
        (raw mode) to collect tables that are not dbt‑managed.
        """
        results = {}
        for model in self.loader.get_models().keys():
            violations = self.get_violations(model, use_raw=True)
            if violations:
                results[model] = violations
        return results
