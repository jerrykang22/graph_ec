from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jGraph, Neo4jVector
from neo4j_graphrag.types import SearchType

from configuration import config
from configuration.config import *
class ChatService:
    def __init__(self):
        self.graph = Neo4jGraph(
            url=NEO4J_CONFIG["uri"],
            username=NEO4J_CONFIG['auth'][0],
            password=NEO4J_CONFIG['auth'][1]
        )
        self.embeddings_model = HuggingFaceEmbeddings(
            model='BAAI/bge-large-zh-v1.5',
            encode_kwargs={"normalize-embeddings": True}
        )

        self.llm=ChatDeepSeek(model='deepseek-chat',api_key=API_KEY)
        self.neo4j_vectors={
            'SPU':Neo4jVector.from_existing_index(
             url=config.NEO4J_CONFIG['uri'],
             username=config.NEO4J_CONFIG['user'],
             password=config.NEO4J_CONFIG['password'],
             embedding=self.embeddings,
             index_name='spu_embedding_index',
             keyword_index_name='spu_full_text_index',
             search_type=SearchType.HYBRID
            ),
            'BaseTrademark': Neo4jVector.from_existing_index(
             url = config.NEO4J_CONFIG['uri'],
             username = config.NEO4J_CONFIG['user'],
             password = config.NEO4J_CONFIG['password'],
             embedding = self.embeddings,
             index_name = 'trademark_embedding_index',
             keyword_index_name = 'trademark_full_text_index',
             search_type = SearchType.HYBRID
             ),
            'Category3': Neo4jVector.from_existing_index(
             url = config.NEO4J_CONFIG['uri'],
             username = config.NEO4J_CONFIG['user'],
             password = config.NEO4J_CONFIG['password'],
             embedding = self.embeddings,
             index_name = 'category3_embedding_index',
             keyword_index_name = 'category3_full_text_index',
             search_type = SearchType.HYBRID
             ),
             'Category2': Neo4jVector.from_existing_index(
             url = config.NEO4J_CONFIG['uri'],
             username = config.NEO4J_CONFIG['user'],
             password = config.NEO4J_CONFIG['password'],
             embedding = self.embeddings,
             index_name = 'category2_embedding_index',
             keyword_index_name = 'category2_full_text_index',
             search_type = SearchType.HYBRID
             ),
             'Category1': Neo4jVector.from_existing_index(
             url = config.NEO4J_CONFIG['uri'],
             username = config.NEO4J_CONFIG['user'],
             password = config.NEO4J_CONFIG['password'],
             embedding = self.embeddings,
             index_name = 'category1_embedding_index',
             keyword_index_name = 'category1_full_text_index',
             search_type = SearchType.HYBRID
            )
        }
        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()
        def chat(self,question):
            pass


        #1.根据问题，生成cypher
        def _generate_cypher(self, question: str, schema_info: str):
            generate_cypher_prompt = PromptTemplate(
                input_variables = ["question", "schema_info"],
                template = """
                 你是一个专业的Neo4j Cypher查询生成器。你的任务是根据用户问题生成一条Cypher查询语句，用于从知识图谱中获取回答用户问题所需的信息。
    
                 用户问题：{question}
    
                 知识图谱结构信息：{schema_info}
    
                 要求：
                 1. 生成参数化Cypher查询语句，用param_0, param_1等代替具体值
                 2. 识别需要对齐的实体
                 3. 必须严格使用以下JSON格式输出结果
                 {{
                  "cypher_query": "生成的Cypher语句",
                  "entities_to_align": [
                   {{
                    "param_name": "param_0",
                    "entity": "原始实体名称",
                    "label": "节点类型"
                  }}
                  ]
                  }}"""
                 ).format(schema_info=schema_info, question=question)
            cypher = self.llm.invoke(generate_cypher_prompt)
            cypher = self.json_parser.invoke(cypher)
            return cypher

        def _entity_align(self, entities_to_align: List[Dict[str, str]]) -> List[Dict[str, str]]:

