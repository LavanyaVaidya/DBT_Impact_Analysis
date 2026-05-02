import json
from sqlglot import parse_one, exp


class ManifestLoader:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    # ----------------------------
    # MODELS
    # ----------------------------
    def get_models(self):
        return {
            k: v for k, v in self.manifest["nodes"].items()
            if v.get("resource_type") == "model"
        }

    # ----------------------------
    # SQL EXTRACTION (dbt 1.11 safe)
    # ----------------------------
    def get_sql(self, model):
        node = self.manifest["nodes"].get(model)

        if not node:
            return None

        return (
            node.get("compiled_code")
            or node.get("compiled_sql")
            or node.get("raw_code")
            or node.get("raw_sql")
        )

    # ----------------------------
    # COLUMN EXTRACTION (FIXED)
    # ----------------------------
    def get_columns(self, model):
        node = self.manifest["nodes"].get(model)

        # 1. Use dbt-defined columns if available
        if node and node.get("columns"):
            cols = list(node["columns"].keys())
            if cols:
                return cols

        # 2. Fallback: SQL parsing
        sql = self.get_sql(model)

        if not sql:
            return []

        try:
            parsed = parse_one(sql)
            cols = set()

            for select in parsed.find_all(exp.Select):

                # ----------------------------
                # CASE 1: SELECT *
                # ----------------------------
                if any(isinstance(e, exp.Star) for e in select.expressions):
                    for table in parsed.find_all(exp.Table):
                        ref_model = table.name

                        ref_node = self.manifest["nodes"].get(ref_model)

                        if ref_node and ref_node.get("columns"):
                            cols.update(ref_node["columns"].keys())

                    continue

                # ----------------------------
                # CASE 2: normal projections
                # ----------------------------
                for proj in select.expressions:

                    # id, name, amount
                    if isinstance(proj, exp.Column):
                        cols.add(proj.name)

                    # aliases (amount_twice etc.)
                    elif proj.alias:
                        cols.add(proj.alias)

            return sorted(cols)

        except Exception as e:
            print(f"[COLUMN ERROR] {model}: {e}")
            return []