from neo4j import GraphDatabase
from typing import Dict, Optional, List, Tuple, Callable, Any


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def run(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        try:
            with self.driver.session() as session:
                records = session.run(query, parameters or {})
                return self._format_records(records)
        except Exception as e:
            print(f"[Neo4j Error] {e}")
            return []

    def run_in_transaction(self, func: Callable[[Any], Any]) -> Any:
        with self.driver.session() as session:
            return session.execute_write(func)

    @staticmethod
    def _format_records(records) -> List[Dict]:
        result = []
        for record in records:
            item = {}
            for key in record.keys():
                val = record[key]
                item[key] = dict(val) if hasattr(val, "items") else val
            result.append(item)
        return result


class CypherUtils:
    @staticmethod
    def build_where_and_params(var: str, props: Dict, prefix: str = "") -> Tuple[str, Dict]:
        clause = " AND ".join([f"{var}.{k} = ${prefix + k}" for k in props])
        params = {f"{prefix}{k}": v for k, v in props.items()}
        return clause, params

    @staticmethod
    def build_set_clause_and_params(var: str, props: Dict, prefix: str = "") -> Tuple[str, Dict]:
        clause = ", ".join([f"{var}.{k} = ${prefix + k}" for k in props])
        params = {f"{prefix}{k}": v for k, v in props.items()}
        return clause, params


class NodeMatcher:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def create(self, label: str, props: Dict):
        query = f"CREATE (n:{label} $props)"
        return self.client.run(query, {"props": props})

    def find(self, label: str, conditions: Optional[Dict] = None):
        if conditions:
            where, params = CypherUtils.build_where_and_params("n", conditions)
            query = f"MATCH (n:{label}) WHERE {where} RETURN n"
        else:
            query, params = f"MATCH (n:{label}) RETURN n", {}
        return self.client.run(query, params)

    def update(self, label: str, match_props: Dict, update_props: Dict):
        where, where_params = CypherUtils.build_where_and_params("n", match_props, "m_")
        set_clause, set_params = CypherUtils.build_set_clause_and_params("n", update_props, "u_")
        query = f"MATCH (n:{label}) WHERE {where} SET {set_clause}"
        return self.client.run(query, {**where_params, **set_params})

    def delete(self, label: str, conditions: Dict):
        where, params = CypherUtils.build_where_and_params("n", conditions)
        query = f"MATCH (n:{label}) WHERE {where} DETACH DELETE n"
        return self.client.run(query, params)

    def fuzzy_find(self, label: str, field: str, pattern: str):
        query = f"MATCH (n:{label}) WHERE n.{field} CONTAINS $value RETURN n"
        return self.client.run(query, {"value": pattern})


class RelationshipMatcher:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def create(self, from_label: str, from_props: Dict,
                     to_label: str, to_props: Dict,
                     rel_type: str, rel_props: Optional[Dict] = None):
        where_from, params_from = CypherUtils.build_where_and_params("a", from_props, "f_")
        where_to, params_to = CypherUtils.build_where_and_params("b", to_props, "t_")
        query = (
            f"MATCH (a:{from_label}), (b:{to_label}) "
            f"WHERE {where_from} AND {where_to} "
            f"CREATE (a)-[r:{rel_type} $rel_props]->(b)"
        )
        params = {**params_from, **params_to, "rel_props": rel_props or {}}
        return self.client.run(query, params)

    def find(self, from_label: str, to_label: str, rel_type: str, rel_props: Optional[Dict] = None):
        query = f"MATCH (a:{from_label})-[r:{rel_type}]->(b:{to_label})"
        params = {}
        if rel_props:
            where_rel, rel_params = CypherUtils.build_where_and_params("r", rel_props)
            query += f" WHERE {where_rel}"
            params.update(rel_params)
        query += " RETURN a, r, b"
        return self.client.run(query, params)

    def update(self, from_label: str, from_props: Dict,
                     to_label: str, to_props: Dict,
                     rel_type: str, update_props: Dict):
        where_from, params_from = CypherUtils.build_where_and_params("a", from_props, "f_")
        where_to, params_to = CypherUtils.build_where_and_params("b", to_props, "t_")
        set_clause, set_params = CypherUtils.build_set_clause_and_params("r", update_props, "u_")
        query = (
            f"MATCH (a:{from_label})-[r:{rel_type}]->(b:{to_label}) "
            f"WHERE {where_from} AND {where_to} "
            f"SET {set_clause}"
        )
        params = {**params_from, **params_to, **set_params}
        return self.client.run(query, params)

    def delete(self, from_label: str, from_props: Dict,
                     to_label: str, to_props: Dict,
                     rel_type: str):
        where_from, params_from = CypherUtils.build_where_and_params("a", from_props, "f_")
        where_to, params_to = CypherUtils.build_where_and_params("b", to_props, "t_")
        query = (
            f"MATCH (a:{from_label})-[r:{rel_type}]->(b:{to_label}) "
            f"WHERE {where_from} AND {where_to} "
            f"DELETE r"
        )
        params = {**params_from, **params_to}
        return self.client.run(query, params)

if __name__ == "__main__":
    with Neo4jClient("bolt://localhost:7687", "neo4j", "12345678") as client:
        nodes = NodeMatcher(client)
        rels = RelationshipMatcher(client)

        # 创建节点
        # nodes.create("type", {"name": "软件故障"})
        # nodes.create("reason", {"name": "驱动模块异常"})
        nodes.delete("solution", {"name": "更新星历"})

        # # 创建关系
        # rels.create("type", {"name": "软件故障"},
        #             "reason", {"name": "驱动模块异常"},
        #             "BECAUSE", {"weight": 0.7})

        # # 查询模糊匹配
        # results = nodes.fuzzy_find("reason", "name", "驱动")
        # print("模糊匹配结果：", results)
