import evaluate
import logging
import time
from datasets import load_from_disk
from transformers import (
    AutoModelForTokenClassification,
    Trainer,
    TrainingArguments,
    EvalPrediction,
    DataCollatorForTokenClassification,
    AutoTokenizer
)
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import threading
from configuration import config
from configuration.config import MODEL_NAME, LABELS, CHECKPOINT_DIR, NER_DIR, LOG_DIR, EPOCHS

# ========== [修改点 1]: 配置 Python 基础日志，同时输出到屏幕和文件 ==========
# 确保存放日志的目录存在
os.makedirs(config.LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # 将带有 ✅ 和 ❤️ 的日志保存到文件
        logging.FileHandler(config.LOG_DIR / "ner_training_console.log", encoding="utf-8"),
        # 同时在终端屏幕上打印
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 心跳线程：每5秒打印一次日志，证明程序还在运行
def heartbeat():
    count = 0
    while True:
        time.sleep(5)
        count += 5
        logger.info(f"❤️ 程序仍在运行，已等待{count}秒（CPU训练初始化需要时间，请勿终止）")


# 启动心跳线程（守护线程，主程序结束会自动退出）
heart_thread = threading.Thread(target=heartbeat, daemon=True)
heart_thread.start()

# ========== 2. 基础初始化 ==========
logger.info(f"✅ 开始初始化模型：{MODEL_NAME}")
id2label = {id: label for id, label in enumerate(config.LABELS)}
label2id = {label: id for id, label in enumerate(config.LABELS)}
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# 加载模型
model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABELS),
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True
)
logger.info("✅ 模型初始化完成！")

# ========== 3. 加载数据集 + 预验证（关键：确保数据集格式正确） ==========
logger.info("✅ 开始加载数据集...")
train_dataset = load_from_disk(config.DATA_DIR / 'ner' / 'processed' / 'train')
valid_dataset = load_from_disk(config.DATA_DIR / 'ner' / 'processed' / 'valid')
logger.info(f"✅ 数据集加载完成：训练集{len(train_dataset)}条，验证集{len(valid_dataset)}条")

# 预验证数据集格式（触发数据加载到内存，提前暴露格式错误）
logger.info("✅ 开始验证数据集格式（预加载第一条数据）...")
try:
    sample = train_dataset[0]
    logger.info(f"✅ 数据集格式验证通过：")
    logger.info(f"   - input_ids长度：{len(sample['input_ids'])}")
    logger.info(f"   - labels长度：{len(sample['labels'])}")
    logger.info(f"   - 第一条label值：{sample['labels'][0]}")
except Exception as e:
    logger.error(f"❌ 数据集格式错误：{e}", exc_info=True)
    exit(1)

# ========== 4. 训练参数 ==========
logger.info("✅ 初始化训练参数...")
args = TrainingArguments(
    output_dir=str(CHECKPOINT_DIR / NER_DIR),
    logging_dir=str(config.LOG_DIR / 'ner'),
    num_train_epochs=3,
    per_device_train_batch_size=1,
    use_cpu=True,
    fp16=False,
    save_steps=5,
    save_total_limit=1,
    save_strategy='steps',
    logging_strategy='steps',
    logging_steps=1,
    eval_strategy='steps',
    eval_steps=5,
    metric_for_best_model='eval_overall_f1',
    load_best_model_at_end=True,
    disable_tqdm=False,
    # ========== [修改点 2]: 开启 TensorBoard 日志记录 ==========
    report_to="tensorboard",  # 这里把原来的 "none" 改成了 "tensorboard"
    # ==========================================================
    #max_steps=5,  # 只跑5步，极致缩短首次验证时间
    gradient_accumulation_steps=1,  # 关闭梯度累积，加快计算
    remove_unused_columns=False,  # 减少数据处理耗时
)

# ========== 5. 数据整理器 + 评估函数 ==========
logger.info("✅ 初始化数据整理器...")
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer, padding=True, return_tensors='pt')

logger.info("✅ 加载评估指标...")
seqeval = evaluate.load('seqeval')


def compute_metrics(prediction: EvalPrediction) -> dict:
    logits = prediction.predictions
    preds = logits.argmax(axis=-1)
    labels = prediction.label_ids

    true_predictions = [
        [id2label[p] for (p, l) in zip(pred, label) if l != -100]
        for pred, label in zip(preds, labels)
    ]
    true_labels = [
        [id2label[l] for (p, l) in zip(pred, label) if l != -100]
        for pred, label in zip(preds, labels)
    ]

    results = seqeval.compute(predictions=true_predictions, references=true_labels)
    return {
        "eval_overall_f1": results.get("overall_f1", 0.0),
        "eval_precision": results.get("overall_precision", 0.0),
        "eval_recall": results.get("overall_recall", 0.0),
        "eval_accuracy": results.get("overall_accuracy", 0.0),
    }


# ========== 6. 启动训练 ==========
logger.info("✅ 所有初始化完成，开始训练！CPU首次迭代可能需要5-10分钟，心跳日志会持续打印...")
trainer = Trainer(
    model=model,
    train_dataset=train_dataset,
    eval_dataset=valid_dataset,
    args=args,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

try:
    start_time = time.time()
    trainer.train()
    logger.info(f"✅ 训练完成！总耗时：{time.time() - start_time:.2f}秒")
    trainer.save_model(str(CHECKPOINT_DIR / NER_DIR / 'best_model'))
    logger.info(f"✅ 模型已保存到：{CHECKPOINT_DIR / NER_DIR / 'best_model'}")
except Exception as e:
    logger.error(f"❌ 训练出错：{e}", exc_info=True)