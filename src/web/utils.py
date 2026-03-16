from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jGraph
from openai import embeddings

from configuration.config import *
class IndexUtil:
    def __init__(self):
        self.graph=Neo4jGraph(
            url=NEO4J_CONFIG["uri"],
            username=NEO4J_CONFIG['auth'][0],
            password=NEO4J_CONFIG['auth'][1]
        )
        #用bge模型生成向量
        #langchain里有huggingface接口，可以直接调用huggingface里的嵌入模型
        self.embeddings_model=HuggingFaceEmbeddings(
            model='BAAI/bge-large-zh-v1.5',
            encode_kwargs={"normalize-embeddings":True}
           )
        #创建全文索引
        #索引名称，针对哪一类实体（比如是sku，spu.....），针对哪个属性创建
        def create_fulltext_index(self,index_name,label,property):
            cypher=f"""
            CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
            FOR(n:{label}) ON EACH[n.property]
            """
            self.graph.query(cypher)

        #创建向量索引
        def create_vector_index(self, index_name, label, source_property,embedding_property):
            #生成嵌入向量，并添加到节点属性中
            embedding_dim=self._add_embedding(label, source_property,embedding_property)
            cypher=f"""
                 CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                FOR (n.{label})
                ON n.{embedding_property}
                OPTIONS {{ indexConfig: {{
                 `vector.dimensions`: {embedding_dim},
                 `vector.similarity_function`: 'cosine'
                }}
                }}
            """
            self.graph.query(cypher)
        def _add_embedding(self,label,source_property,embedding_property):
            cypher=f"""
            MATCH(n:{label})
            RETURN n.{source_property}AS text,id(n) AS id
            """
            results=self.graph.query(cypher)
            docs=[result['text'] for result in results]
            embeddings=self.embedding_model.embed_documents(docs)
            batch=[]
            for result,embedding in zip(results,embeddings):
                item={"id":result['id'],'embedding':embedding}
                batch.append(item)
            cypher=f"""
                UNWIND $batch AS item
                MATCH(n:{label})
                WHERE id(n)=item.id
                SET n.{embedding_property}=item.embdding
            
            """
            self.graph.query(cypher,parmas={"batch":batch})
            return len(embeddings[0])








