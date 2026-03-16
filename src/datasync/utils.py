
from configuration.config import *
import pymysql
from neo4j import GraphDatabase
from pymysql.cursors import DictCursor



class MysqlReader:
    def __init__(self):
        self.connection = pymysql.connect(**MYSQL_CONFIG)
        self.cursor = self.connection.cursor(cursor=DictCursor)

    def read(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connection.close()


class Neo4jWriter:
    def __init__(self):
        self.driver=GraphDatabase.driver(**NEO4J_CONFIG)

    #写入节点
    def write_nodes(self,label,properties:list[dict]):

        cypher = f"""
                UNWIND $batch AS item
                MERGE(:{label} {{id:item.id,name:item.name}})

                """
        self.driver.execute_query(cypher, batch=properties)
    #写入关系
    def write_relations(self,type:str,start_label,end_label,relations:list[dict]):
        cypher = f"""
                        UNWIND $batch AS item    
                        MATCH(start:{start_label}{{id:item.start_id}}),(end:{end_label}{{id:item.end_id}})
                        MERGE(start)-[:{type}]->(end)

                        """
        self.driver.execute_query(cypher, batch=relations)



if __name__ == '__main__':
    reader=MysqlReader()
    writer = Neo4jWriter()
    driver=GraphDatabase.driver(**NEO4J_CONFIG)

    sql="""
        select *
        from
        base_category1
    
    """
    category1=reader.read(sql)#[{'id': 1, 'name': '图书、音像、电子书刊', 'create_time': datetime.datetime(2021, 12, 14, 0, 0), 'operate_time': None}, {'id': 2, 'name': '手机', 'create_time': datetime.datetime(2021, 12, 14, 0, 0), 'operate_time': None}]
    print(category1)

   #写入neo4j
    writer.write_nodes('category1',category1)


   #...................................
    sql = """
            select *
            from
            base_category2

        """
    category2 = reader.read(sql)
    print(category2)

    #写入neo4j
    writer.write_nodes('category2',category2)


    #.................category2->category1
    sql="""
       select id as start_id,category1_id as end_id
       from 
       base_category2
     
    """
    relations=reader.read(sql)
    print(relations)#[{'start_id': 1, 'end_id': 1}, {'start_id': 2, 'end_id': 1}, {'start_id': 3, 'end_id': 1}]
    #item就是relation里每一条，{'start_id': 1, 'end_id': 1}，{'start_id': 2, 'end_id': 1}
    #MATCH(start:category2{id:item.start_id}),(end:category1{id:item.end_id})这句话就是先取item里的start_id去category2里找到记录为start，同理在1里记录为end
    #然后二者belong
    #cypher = """
    #            UNWIND $relations AS item
    #           MATCH(start:category2{id:item.start_id}),(end:category1{id:item.end_id})
    #           MERGE(start)-[:Belong]->(end)
    #
    #            """
    #driver.execute_query(cypher, relations=relations)
    writer.write_relations('Belong',start_label='category2',end_label='category1',relations=relations)




























