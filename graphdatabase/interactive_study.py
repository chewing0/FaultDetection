from neo4j import GraphDatabase
from typing import Dict, Optional, List, Tuple, Callable, Any
import sys

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


def print_menu():
    print("\n=== Neo4j 数据库操作菜单 ===")
    print("1. 创建节点")
    print("2. 查询节点")
    print("3. 更新节点")
    print("4. 删除节点")
    print("5. 模糊查询节点")
    print("6. 创建关系")
    print("7. 查询关系")
    print("8. 更新关系")
    print("9. 删除关系")
    print("0. 退出")
    print("========================")


def get_properties():
    props = {}
    while True:
        key = input("请输入属性名 (直接回车结束): ").strip()
        if not key:
            break
        value = input(f"请输入 {key} 的值: ").strip()
        props[key] = value
    return props


def select_node(nodes: NodeMatcher, label: str) -> Optional[Dict]:
    """从指定标签的节点中选择一个节点"""
    results = nodes.find(label)
    if not results:
        print(f"没有找到 {label} 类型的节点")
        return None
    
    print(f"\n可用的 {label} 节点:")
    for i, node in enumerate(results, 1):
        print(f"{i}. {node['n']}")
    
    while True:
        try:
            choice = int(input(f"\n请选择节点 (1-{len(results)}): "))
            if 1 <= choice <= len(results):
                return results[choice-1]['n']
            print("无效的选择，请重试！")
        except ValueError:
            print("请输入有效的数字！")


def validate_node_type(label: str) -> bool:
    """验证节点类型是否有效"""
    valid_types = {'type', 'reason', 'solution'}
    return label in valid_types


def validate_relationship_type(from_label: str, to_label: str, rel_type: str) -> bool:
    """验证关系类型是否有效"""
    valid_relationships = {
        ('type', 'reason'): {'BECAUSE'},
        ('reason', 'solution'): {'DEAL'}
    }
    return (from_label, to_label) in valid_relationships and rel_type in valid_relationships[(from_label, to_label)]


def main():
    # 连接数据库
    uri = input("请输入Neo4j数据库URI (默认: bolt://localhost:7687): ").strip() or "bolt://localhost:7687"
    user = input("请输入用户名 (默认: neo4j): ").strip() or "neo4j"
    password = input("请输入密码: ").strip()

    try:
        with Neo4jClient(uri, user, password) as client:
            nodes = NodeMatcher(client)
            rels = RelationshipMatcher(client)

            while True:
                print_menu()
                choice = input("请选择操作 (0-9): ").strip()

                if choice == "0":
                    print("感谢使用，再见！")
                    break

                elif choice == "1":  # 创建节点
                    label = input("请输入节点标签 (type/reason/solution): ").strip()
                    if not validate_node_type(label):
                        print("无效的节点类型！必须是 type、reason 或 solution")
                        continue
                    print("请输入节点属性:")
                    props = get_properties()
                    result = nodes.create(label, props)
                    print("创建结果:", result)

                elif choice == "2":  # 查询节点
                    label = input("请输入节点标签 (type/reason/solution): ").strip()
                    if not validate_node_type(label):
                        print("无效的节点类型！必须是 type、reason 或 solution")
                        continue
                    print("请输入查询条件 (直接回车查询所有):")
                    conditions = get_properties()
                    result = nodes.find(label, conditions if conditions else None)
                    print("查询结果:", result)

                elif choice == "3":  # 更新节点
                    label = input("请输入节点标签 (type/reason/solution): ").strip()
                    if not validate_node_type(label):
                        print("无效的节点类型！必须是 type、reason 或 solution")
                        continue
                    print("请输入匹配条件:")
                    match_props = get_properties()
                    print("请输入要更新的属性:")
                    update_props = get_properties()
                    result = nodes.update(label, match_props, update_props)
                    print("更新结果:", result)

                elif choice == "4":  # 删除节点
                    label = input("请输入节点标签 (type/reason/solution): ").strip()
                    if not validate_node_type(label):
                        print("无效的节点类型！必须是 type、reason 或 solution")
                        continue
                    print("请输入删除条件:")
                    conditions = get_properties()
                    result = nodes.delete(label, conditions)
                    print("删除结果:", result)

                elif choice == "5":  # 模糊查询
                    label = input("请输入节点标签 (type/reason/solution): ").strip()
                    if not validate_node_type(label):
                        print("无效的节点类型！必须是 type、reason 或 solution")
                        continue
                    field = input("请输入要查询的字段名: ").strip()
                    pattern = input("请输入查询模式: ").strip()
                    result = nodes.fuzzy_find(label, field, pattern)
                    print("查询结果:", result)

                elif choice == "6":  # 创建关系
                    print("\n可用的关系类型:")
                    print("1. type -> reason (BECAUSE)")
                    print("2. reason -> solution (DEAL)")
                    rel_choice = input("请选择关系类型 (1-2): ").strip()
                    
                    if rel_choice == "1":
                        from_label, to_label, rel_type = "type", "reason", "BECAUSE"
                    elif rel_choice == "2":
                        from_label, to_label, rel_type = "reason", "solution", "DEAL"
                    else:
                        print("无效的选择！")
                        continue

                    # 选择起始节点
                    from_node = select_node(nodes, from_label)
                    if not from_node:
                        continue

                    # 选择目标节点
                    to_node = select_node(nodes, to_label)
                    if not to_node:
                        continue

                    print("请输入关系属性 (直接回车跳过):")
                    rel_props = get_properties()
                    
                    result = rels.create(from_label, from_node, to_label, to_node, rel_type, rel_props if rel_props else None)
                    print("创建结果:", result)

                elif choice == "7":  # 查询关系
                    print("\n可用的关系类型:")
                    print("1. type -> reason (BECAUSE)")
                    print("2. reason -> solution (DEAL)")
                    rel_choice = input("请选择关系类型 (1-2): ").strip()
                    
                    if rel_choice == "1":
                        from_label, to_label, rel_type = "type", "reason", "BECAUSE"
                    elif rel_choice == "2":
                        from_label, to_label, rel_type = "reason", "solution", "DEAL"
                    else:
                        print("无效的选择！")
                        continue

                    print("请输入关系属性 (直接回车跳过):")
                    rel_props = get_properties()
                    result = rels.find(from_label, to_label, rel_type, rel_props if rel_props else None)
                    print("查询结果:", result)

                elif choice == "8":  # 更新关系
                    print("\n可用的关系类型:")
                    print("1. type -> reason (BECAUSE)")
                    print("2. reason -> solution (DEAL)")
                    rel_choice = input("请选择关系类型 (1-2): ").strip()
                    
                    if rel_choice == "1":
                        from_label, to_label, rel_type = "type", "reason", "BECAUSE"
                    elif rel_choice == "2":
                        from_label, to_label, rel_type = "reason", "solution", "DEAL"
                    else:
                        print("无效的选择！")
                        continue

                    # 选择起始节点
                    from_node = select_node(nodes, from_label)
                    if not from_node:
                        continue

                    # 选择目标节点
                    to_node = select_node(nodes, to_label)
                    if not to_node:
                        continue

                    print("请输入要更新的关系属性:")
                    update_props = get_properties()
                    result = rels.update(from_label, from_node, to_label, to_node, rel_type, update_props)
                    print("更新结果:", result)

                elif choice == "9":  # 删除关系
                    print("\n可用的关系类型:")
                    print("1. type -> reason (BECAUSE)")
                    print("2. reason -> solution (DEAL)")
                    rel_choice = input("请选择关系类型 (1-2): ").strip()
                    
                    if rel_choice == "1":
                        from_label, to_label, rel_type = "type", "reason", "BECAUSE"
                    elif rel_choice == "2":
                        from_label, to_label, rel_type = "reason", "solution", "DEAL"
                    else:
                        print("无效的选择！")
                        continue

                    # 选择起始节点
                    from_node = select_node(nodes, from_label)
                    if not from_node:
                        continue

                    # 选择目标节点
                    to_node = select_node(nodes, to_label)
                    if not to_node:
                        continue

                    result = rels.delete(from_label, from_node, to_label, to_node, rel_type)
                    print("删除结果:", result)

                else:
                    print("无效的选择，请重试！")

                input("\n按回车键继续...")

    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 