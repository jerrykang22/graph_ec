from utils import MysqlReader, Neo4jWriter


# 构建一个表数据的同步器
class TableSynchronizer:
    def __init__(self):
        self.reader = MysqlReader()
        self.writer = Neo4jWriter()

    def sync_category1(self):
        sql = """
            select id ,name
            from base_category1
        """
        # 读取mysql，得到一组属性  id name
        properties = self.reader.read(sql)
        # 向neo4j写入节点
        self.writer.write_nodes("category1", properties)

    def sync_category2(self):
        sql = """
            select id ,name
            from base_category2
        """
        # 读取mysql，得到一组属性  id name
        properties = self.reader.read(sql)
        # 向neo4j写入节点
        self.writer.write_nodes("category2", properties)

    def sync_category3(self):
        sql = """
            select id ,name
            from base_category3
        """
        # 读取mysql，得到一组属性  id name
        properties = self.reader.read(sql)
        # 向neo4j写入节点
        self.writer.write_nodes("category3", properties)

    def sync_category2_to_category1(self):
        sql = """
            select id start_id,category1_id end_id
            from base_category2
        """
        # 读取mysql，得到一组关系  start_id end_id
        relations = self.reader.read(sql)
        # 向neo4j写入关系
        self.writer.write_relations("Belong", "category2", "category1", relations)

    def sync_category3_to_category2(self):
        sql = """
            select id start_id,category2_id end_id
            from base_category3
        """
        # 读取mysql，得到一组关系  start_id end_id
        relations = self.reader.read(sql)
        # 向neo4j写入关系
        self.writer.write_relations("Belong", "category3", "category2", relations)

    def sync_base_attr_name(self):
        sql = """
           select id,attr_name name 
           from base_attr_info
        """
        properties = self.reader.read(sql)
        self.writer.write_nodes("BaseAttrName", properties=properties)

    def sync_base_attr_value(self):
        sql = """
           select id,value_name name 
           from base_attr_value
        """
        properties = self.reader.read(sql)
        self.writer.write_nodes("BaseAttrValue", properties=properties)

    def sync_base_attr_name_to_value(self):
        sql = """
           select id end_id,attr_id start_id
           from base_attr_value
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "BaseAttrName", "BaseAttrValue", relations=relations)

    def sync_category1_to_base_attr_name(self):
        sql = """
          select category_id start_id, id end_id
          from base_attr_info
          where category_level =1
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "category1", "BaseAttrName", relations=relations)

    def sync_category2_to_base_attr_name(self):
        sql = """
          select category_id start_id, id end_id
          from base_attr_info
          where category_level =2
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "category2", "BaseAttrName", relations=relations)

    def sync_category3_to_base_attr_name(self):
        sql = """
          select category_id start_id, id end_id
          from base_attr_info
          where category_level =3
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "category3", "BaseAttrName", relations=relations)

    def sync_spu(self):
        sql = """
             select id,spu_name name
             from spu_info
        """
        properties = self.reader.read(sql)
        self.writer.write_nodes("SPU", properties=properties)

    def sync_sku(self):
        sql = """
             select id,sku_name name
             from sku_info
        """
        properties = self.reader.read(sql)
        self.writer.write_nodes("SKU", properties=properties)

    def sync_sku_to_spu(self):
        sql = """
              select id start_id,spu_id end_id
              from sku_info
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Belong", "SKU", "SPU", relations=relations)

    def sync_spu_to_category3(self):
        sql = """
            select id start_id,category3_id end_id
            from spu_info
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Belong", "SPU", 'category3', relations=relations)

    def sync_tradmark(self):
        sql = """
           select id,tm_name name
           from base_trademark
        """
        properties = self.reader.read(sql)
        self.writer.write_nodes("Tradmark", properties=properties)

    def sync_spu_to_tradmark(self):
        sql = """
          select id start_id,tm_id end_id
          from spu_info
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Belong", "SPU", "Tradmark", relations=relations)

    def sync_sale_attr_name(self):
        sql = """
           select id ,sale_attr_name name
           from spu_sale_attr
        """
        properties = self.reader.read(sql)
        self.writer.write_nodes("SaleAttrName", properties=properties)

    def sync_sale_attr_value(self):
        sql = """
           select id ,sale_attr_value_name name
           from spu_sale_attr_value
        """
        properties = self.reader.read(sql)
        self.writer.write_nodes("SaleAttrValue", properties=properties)

    def sync_sale_attr_value_attr(self):
        sql = """
           select a.id start_id, v.id end_id
           from spu_sale_attr_value v
           join spu_sale_attr a on v.spu_id = a.spu_id and v.base_sale_attr_id = a.base_sale_attr_id
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "SaleAttrName", "SaleAttrValue", relations=relations)

    def sync_sku_base_attr_value(self):
        sql = """
           select sku_id start_id, value_id end_id
           from sku_attr_value
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "SKU", "BaseAttrValue", relations=relations)

    def sync_sku_sale_attr_value(self):
        sql = """
           select sku_id start_id, sale_attr_value_id end_id
           from sku_sale_attr_value
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "SKU", "SaleAttrValue", relations=relations)

    def sync_sale_attr_to_spu(self):
        sql = """
           select id end_id, spu_id start_id
           from spu_sale_attr
        """
        relations = self.reader.read(sql)
        self.writer.write_relations("Have", "SPU", "SaleAttrName", relations=relations)


if __name__ == '__main__':
    synchronizer = TableSynchronizer()
    # 同步分类
    synchronizer.sync_category1()
    synchronizer.sync_category2()
    synchronizer.sync_category3()
    synchronizer.sync_category2_to_category1()
    synchronizer.sync_category3_to_category2()

    # 同步基础属性
    synchronizer.sync_base_attr_name()
    synchronizer.sync_base_attr_value()
    synchronizer.sync_base_attr_name_to_value()
    synchronizer.sync_category1_to_base_attr_name()
    synchronizer.sync_category2_to_base_attr_name()
    synchronizer.sync_category3_to_base_attr_name()

    # 同步SPU/SKU
    synchronizer.sync_spu()
    synchronizer.sync_sku()
    synchronizer.sync_sku_to_spu()
    synchronizer.sync_spu_to_category3()

    # 同步品牌
    synchronizer.sync_tradmark()
    synchronizer.sync_spu_to_tradmark()

    # 同步销售属性
    synchronizer.sync_sale_attr_name()
    synchronizer.sync_sale_attr_value()
    synchronizer.sync_sale_attr_value_attr()
    synchronizer.sync_sale_attr_to_spu()

    # 同步SKU与属性值关联
    synchronizer.sync_sku_base_attr_value()
    synchronizer.sync_sku_sale_attr_value()