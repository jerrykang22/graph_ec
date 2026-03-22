import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

from configuration import config
from utils import Neo4jWriter, MysqlReader  # 保持和TableSynchronizer一致的导入路径
from src.ner.predict import Predictor


# 构建文本信息同步器（和TableSynchronizer的注释风格一致）
class TextSynchronizer:
    def __init__(self):
        self.writer = Neo4jWriter()  # 统一命名为writer（原TableSynchronizer用的是writer）
        self.reader = MysqlReader()  # 统一命名为reader（原TableSynchronizer用的是reader）
        self.extractor = self._init_extractor()

    def _init_extractor(self):
        model = AutoModelForTokenClassification.from_pretrained(str(config.CHECKPOINT_DIR / 'ner' / 'best_model'))
        tokenizer = AutoTokenizer.from_pretrained(str(config.CHECKPOINT_DIR / 'ner' / 'best_model'))
        device = torch.device('cpu')
        return Predictor(model, tokenizer, device)

    def sync_spu_desc(self):
        sql = """
            select id, description
            from spu_info
        """
        # 读取mysql，得到SPU描述数据
        spu_desc = self.reader.read(sql)  # 统一用read方法（原TableSynchronizer用的是read）
        spu_ids = [spu['id'] for spu in spu_desc]
        descs = [spu['description'] for spu in spu_desc]
        spu_entities = self.extractor.extract(descs)

        nodes = []
        relationships = []
        for id, entities in zip(spu_ids, spu_entities):
            for index, entity in enumerate(entities):
                node = {
                    "id": '-'.join([str(id), str(index)]),
                    "name": entity
                }
                nodes.append(node)

                relationship = {
                    "start_id": id,
                    "end_id": '-'.join([str(id), str(index)])
                }
                relationships.append(relationship)

        # 向neo4j写入Tag节点（和TableSynchronizer的参数风格一致）
        self.writer.write_nodes("Tag", nodes)
        # 向neo4j写入SPU和Tag的关系（统一用write_relations方法）
        self.writer.write_relations("Have", "SPU", "Tag", relationships)


if __name__ == '__main__':
    synchronizer = TextSynchronizer()
    synchronizer.sync_spu_desc()