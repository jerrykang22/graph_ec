from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jGraph

# 确保导入了你的配置
from configuration import config


def create_full_text_index(graph, index, label, property):
    # 加上 IF NOT EXISTS 避免重复创建报错
    cypher = f"""
    CREATE FULLTEXT INDEX {index} IF NOT EXISTS
    FOR (n:{label})
    ON EACH [n.{property}]
    """
    graph.query(cypher)


def create_embedding_index(
        graph,
        index,
        label,
        property,
        embedding_property,
        embedding_model,
        embedding_dim,
        batch_size=100
):
    # 1. 查询需要生成 embedding 的节点（将废弃的 id(n) 替换为 elementId(n) 消除黄字警告）
    query = f"""
    MATCH (n:{label})
    WHERE n.{property} IS NOT NULL
    RETURN elementId(n) as node_id, n.{property} as text
    """
    nodes = graph.query(query)

    # 2. 批量生成 embedding 并更新节点
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i + batch_size]
        texts = [record['text'] for record in batch]
        embeddings = embedding_model.embed_documents(texts)  # HuggingFace 批量生成 embedding

        for record, emb in zip(batch, embeddings):
            # 同样使用 elementId(n) 更新节点
            update_query = f"""
            MATCH (n)
            WHERE elementId(n) = $node_id
            SET n.{embedding_property} = $embedding
            """
            graph.query(update_query, {'node_id': record['node_id'], 'embedding': emb})

    print(f"已为 {len(nodes)} 个 {label} 节点生成 embedding。")

    # 3. 创建向量索引（加上 IF NOT EXISTS 避免重复创建报错）
    cypher_index = f"""
    CREATE VECTOR INDEX {index} IF NOT EXISTS
    FOR (n:{label})
    ON (n.{embedding_property})
    OPTIONS {{indexConfig:{{
        `vector.dimensions`: {embedding_dim},
        `vector.similarity_function`: 'cosine'
        }}
    }}
    """
    graph.query(cypher_index)
    print(f"向量索引 '{index}' 处理完毕。")


def drop_all_indexes(graph):
    indexes = graph.query("show indexes where type in ['VECTOR','FULLTEXT']")
    indexes = [index['name'] for index in indexes]
    for index in indexes:
        graph.query(f"drop index {index}")
    print("已清理所有旧的 VECTOR 和 FULLTEXT 索引。")


if __name__ == '__main__':
    print("正在连接数据库...")
    # 1. 传入配置，建立连接
    graph = Neo4jGraph(
        url=config.NEO4J_CONFIG['uri'],
        username=config.NEO4J_CONFIG['auth'][0],
        password=config.NEO4J_CONFIG['auth'][1]
    )

    # 2. 清理历史遗留的、错误的空索引（强烈建议执行这一步清空重来）
    drop_all_indexes(graph)

    print("正在创建全文索引...")
    # 3. 创建全文索引（严格按照数据库 Schema 的真实拼写和大小写！）
    create_full_text_index(graph, "spu_full_text_index", "SPU", "name")
    create_full_text_index(graph, "trademark_full_text_index", "Tradmark", "name")  # 修正：Tradmark
    create_full_text_index(graph, "category3_full_text_index", "category3", "name")  # 修正：category3
    create_full_text_index(graph, "category2_full_text_index", "category2", "name")  # 修正：category2
    create_full_text_index(graph, "category1_full_text_index", "category1", "name")  # 修正：category1

    print("正在加载 Embedding 模型（可能需要几秒钟）...")
    # 4. 初始化模型
    model_name = "BAAI/bge-small-zh-v1.5"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}
    embedding_model = HuggingFaceEmbeddings(
        model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
    )

    print("开始为节点生成 Embedding 并建立向量索引...")
    # 5. 生成向量并创建索引（同样严格区分大小写！）
    create_embedding_index(graph, "spu_embedding_index", "SPU", "name", "embedding", embedding_model, 512)
    create_embedding_index(graph, "trademark_embedding_index", "Tradmark", "name", "embedding", embedding_model, 512)
    create_embedding_index(graph, "category3_embedding_index", "category3", "name", "embedding", embedding_model, 512)
    create_embedding_index(graph, "category2_embedding_index", "category2", "name", "embedding", embedding_model, 512)
    create_embedding_index(graph, "category1_embedding_index", "category1", "name", "embedding", embedding_model, 512)

    print("\n🎉 所有操作执行完毕！你的 GraphRAG 底层知识库已经就绪！")