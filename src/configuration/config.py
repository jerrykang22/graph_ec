from pathlib import Path
#1.目录路劲
ROOT_DIR=Path(__file__).parent.parent.parent
NER_DIR='ner'
DATA_DIR=ROOT_DIR/'data'
RAW_DATA_DIR=DATA_DIR/NER_DIR/'raw'
PROCESS_DATA_DIR=DATA_DIR/NER_DIR/'processed'
LOG_DIR=ROOT_DIR/'logs'
CHECKPOINT_DIR=ROOT_DIR/'checkpoints'

#2，数据文件名和模型名称
RAW_DATA_FILE=str(RAW_DATA_DIR/('data.json'))
MODEL_NAME='D:\\sgg\\bert-base-chinese'

#3.超参数
BATCH_SIZE=8
EPOCHS=5
LEARNING_RATE=1e-5

SAVE_STEPS=20


#4.NER任务分类标签
LABELS=['B','I','O']


#数据库连接
MYSQL_CONFIG={
    'host':'localhost',
    'port':3306,
    'user':'root',
    'password':'root',
    'database':'gmall',
}

NEO4J_CONFIG={
    'uri':'neo4j://localhost:7687',
    'auth':("neo4j","kangjierui0918")
}


API_KEY="sk-d939b49f02924f0c8478535d51944584"

WEB_STATIC_DIR=ROOT_DIR/'src'/'web'/'static'























