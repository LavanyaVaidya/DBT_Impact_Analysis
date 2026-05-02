import sqlglot
from sqlglot import exp


class ViolationDetector:
    def __init__(self, loader):
        self.loader = loader

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
    # EXTRACT TABLES FROM SQL
    # ----------------------------
    def _extract_tables(self, sql):
        if not sql:
            return set()

        try:
            parsed = sqlglot.parse_one(sql)

            tables = set()

            for t in parsed.find_all(exp.Table):
                # normalize schema.table → table
                tables.add(t.name.split(".")[-1])

            return tables

        except Exception as e:
            print(f"[VIOLATION PARSE ERROR]: {e}")
            return set()

    # ----------------------------
    # MAIN LOGIC
    # ----------------------------
    def get_violations(self, model):
        sql = self.loader.get_sql(model)

        if not sql:
            return []

        tables = self._extract_tables(sql)

        violations = set()

        for table in tables:

            is_model = table in self.dbt_models
            is_source = table in self.dbt_sources

            # violation = not dbt-managed
            if not is_model and not is_source:
                violations.add(table)

        return sorted(list(violations))