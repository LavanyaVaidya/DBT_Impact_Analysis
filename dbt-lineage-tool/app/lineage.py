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

    def subgraph_edges(self, model, column=None):
        """
        Builds the visual graph edges based on the specific column filter.
        """
        reachable = set(self.downstream(model, column))
        reachable.add(model)
        
        edges = {}
        for upstream in reachable:
            downs = self.graph.get(upstream, set())
            # Only keep edges that exist within our filtered reachable set
            filtered = {d for d in downs if d in reachable}
            if filtered:
                edges[upstream] = list(filtered)
        return edges

    def downstream(self, model_key, column=None):
        """
        Calculates downstream impact with CTE-aware column and star analysis.
        """
        visited = set()
        stack = [model_key]
        impacted_nodes = []
        
        target_col = column.lower() if column else None
        # Extract base name (e.g., 'model.project.a' -> 'a')
        source_model_name = model_key.split('.')[-1].lower()

        print(f"\n{'='*80}")
        print(f"ANALYSIS: [{model_key}] | Column: [{column}]")
        print(f"{'='*80}")

        while stack:
            current_node = stack.pop()
            # The name of the node we are currently checking for as an upstream
            current_upstream_name = current_node.split('.')[-1].lower()
            
            downstream_models = self.graph.get(current_node, [])

            for ds_key in downstream_models:
                if ds_key in visited:
                    continue

                print(f"\n[ANALYZING] {ds_key}")

                if not target_col:
                    print(f"  --> MATCH: Model-level change.")
                    visited.add(ds_key)
                    impacted_nodes.append(ds_key)
                    stack.append(ds_key)
                    continue

                sql = self.loader.get_sql(ds_key)
                if not sql:
                    continue

                try:
                    parsed = sqlglot.parse_one(sql)
                    
                    # --- CHECK A: Explicit Column Usage ---
                    column_usage_found = False
                    for col in parsed.find_all(exp.Column):
                        if col.name.lower() == target_col:
                            c_table = col.table.lower() if col.table else ""
                            # Match if table-less or specifically matching current upstream
                            if not c_table or c_table == current_upstream_name:
                                column_usage_found = True
                                break

                    # --- CHECK B: Scope-Aware Star Selection (*) ---
                    star_impact = False
                    for star in parsed.find_all(exp.Star):
                        # Find the SELECT statement wrapping this star
                        parent_select = star.find_ancestor(exp.Select)
                        
                        if parent_select:
                            # Look at what tables this specific SELECT/CTE is pulling from
                            tables_in_scope = [t.name.lower() for t in parent_select.find_all(exp.Table)]
                            
                            print(f"    [DEBUG] Found Star. Scope Tables: {tables_in_scope}")
                            
                            # If this scope (CTE or subquery) uses our upstream model, the * is a match
                            if current_upstream_name in tables_in_scope:
                                print(f"    [DEBUG] Match: Star pulls from upstream '{current_upstream_name}'")
                                star_impact = True
                                break
                        
                        # Fallback for prefixed stars like 'level4_a.*'
                        parent_col = star.parent
                        if isinstance(parent_col, exp.Column) and parent_col.table.lower() == current_upstream_name:
                            star_impact = True
                            break

                    if column_usage_found or star_impact:
                        reason = "Column Match" if column_usage_found else "Star Match"
                        print(f"  --> RESULT: MATCH ({reason})")
                        visited.add(ds_key)
                        impacted_nodes.append(ds_key)
                        stack.append(ds_key)
                    else:
                        print(f"  --> RESULT: NO MATCH")

                except Exception as e:
                    print(f"  --> [ERROR] Parsing failed: {e}. Defaulting to impacted.")
                    visited.add(ds_key)
                    impacted_nodes.append(ds_key)
                    stack.append(ds_key)

        return impacted_nodes