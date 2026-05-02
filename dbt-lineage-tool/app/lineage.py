import sqlglot
from sqlglot import exp
from collections import defaultdict
from app.violations import ViolationDetector


class LineageEngine:
    def __init__(self, loader):
        self.loader = loader

        # model-level graph: upstream → downstream
        self.graph = defaultdict(set)

        # reverse graph for fast traversal
        self.reverse_graph = defaultdict(set)

    def build(self):
        models = self.loader.get_models()

        print(f"[LINEAGE] Total models found: {len(models)}")

        for model in models:
            node = models[model]

            # ----------------------------
            # 1. PRIMARY SOURCE: dbt dependency graph (CORRECT WAY)
            # ----------------------------
            depends_on = node.get("depends_on", {}).get("nodes", [])

            for upstream in depends_on:
                self.graph[upstream].add(model)
                self.reverse_graph[model].add(upstream)

            # ----------------------------
            # 2. OPTIONAL: SQL fallback (only for extra edges)
            # ----------------------------
            sql = self.loader.get_sql(model)

            if not sql or "{{" in sql:
                continue

            try:
                parsed = sqlglot.parse_one(sql)

                tables = parsed.find_all(exp.Table)

                for table in tables:
                    upstream_model = table.name

                    # avoid noise like schema.table mismatches
                    if upstream_model:
                        self.graph[upstream_model].add(model)
                        self.reverse_graph[model].add(upstream_model)

            except Exception as e:
                print(f"[LINEAGE] SQL parse error in {model}: {e}")

        print(f"[LINEAGE] Graph built with {len(self.graph)} nodes")

        # -------------------------------------------------
        # 3. HARD‑CODED TABLE DETECTION
        # -------------------------------------------------
        # Use ViolationDetector in raw‑SQL mode to find tables that are
        # referenced as literal strings instead of dbt refs. Those
        # tables are added as upstream nodes so that downstream impact
        # includes them.
        # Build a lookup from model base name to full manifest identifier
        name_to_key = {v["name"]: k for k, v in self.loader.get_models().items()}
        detector = ViolationDetector(self.loader, use_raw=True)
        for model_key in self.loader.get_models().keys():
            hardcoded = detector.get_violations(model_key, use_raw=True)
            for table in hardcoded:
                # Resolve to full model identifier if it matches a known dbt model
                upstream_key = name_to_key.get(table, table)
                self.graph[upstream_key].add(model_key)
                self.reverse_graph[model_key].add(upstream_key)

    def subgraph_edges(self, model):
        """Return a dict of edges (upstream -> downstream) for the sub‑graph reachable from *model*.
        The result includes both direct and indirect connections, preserving the true DAG structure.
        """
        # First get all reachable nodes using the existing downstream traversal
        reachable = set(self.downstream(model))
        # Include the starting model itself so we capture its outgoing edges
        reachable.add(model)
        edges = {}
        for upstream in reachable:
            downs = self.graph.get(upstream, set())
            # Keep only downstream nodes that are also in the reachable set
            filtered = {d for d in downs if d in reachable}
            if filtered:
                edges[upstream] = list(filtered)
        return edges


    def downstream(self, model, column=None):
        """
        Model-level impact (stable + production-safe)
        """
        visited = set()
        stack = [model]
        while stack:
            current = stack.pop()
            for downstream in self.graph.get(current, []):
                if downstream not in visited:
                    visited.add(downstream)
                    stack.append(downstream)
        return list(visited)
    def upstream(self, model):
        """
        Optional reverse lineage (useful for debugging)
        """
        visited = set()
        stack = [model]
        while stack:
            current = stack.pop()
            for upstream in self.reverse_graph.get(current, []):
                if upstream not in visited:
                    visited.add(upstream)
                    stack.append(upstream)
        return list(visited)