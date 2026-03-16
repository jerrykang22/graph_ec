import torch
class Predictor:
  def __init__(self, model, tokenizer, device):
      self.model = model.to(device)
      self.model.eval()
      self.tokenizer = tokenizer
      self.device = device

  def predict(self, inputs: str | list, batch_size=8):
      is_str = isinstance(inputs, str)
      if is_str:
          inputs = [inputs]
      #1.预分词，得到字符李彪
      tokens_list=[list(input) for input in inputs]
      #2.用tokenizer对列表进行分词，
      input_tensor=self.tokenizer(
          tokens_list,
          is_split_into_words=True,
          padding=True,
          truncation=True,
          return_tensors='pt'
      )#input_tensors就是input_ids,attention_mask,token_type_ids构成的字典
      #3.加载到设备
      input_tensor={k:v.to(self.device)for k,v in input_tensor.items()}
      #4.前向传播
      with torch.no_grad():
          #outputs就是模型返回结果，有loss，logits，hidden_states等
          outputs=self.model(**input_tensor)
          logits=outputs.logits
          predictions=torch.argmax(logits,dim=-1).tolist()#例如是[1,2,0,1,2]这是标签对应的ID
          final_predictions=[]
          for tokens,prediction in zip(tokens_list,predictions):
               #要真实有效的id，不要cls，sep

               prediction=prediction[1:len(tokens)+1]
               #转换成标签
               final_prediction=[self.model.config.id2label[id] for id in prediction]
      if is_str:
          return final_predictions[0]
      return final_predictions

#现在final_predictions的样子，比如一句话['B', 'I', 'O', 'B', 'I']
#现在已经识别到实体了，接下来需要把实体抽出来
  def extract(self,inputs:str|list[str]):#list[str]就是['我', '是', '张', '大', '三']
      is_str = isinstance(inputs, str)
      if is_str:
          inputs = [inputs]
      predictions=self.predict(inputs)#['B', 'I', 'O', 'B', 'I']
      #从当前列表中抽取实体列表
      entities_list=[]
      for input,labels in zip(inputs,predictions):
          #调用内部函数，抽取一个数据样本的所有实体标签
          entities=self._extract_tntities(list(input),labels)
          entities_list.append(entities)
      if is_str:
        return entities_list[0]
      return entities_list

  def _extract_tntities(self, tokens, labels):#tokens就是['我', '是', '张', '大', '三'] labels是三个标签BIO
      entities=[]
      current_entity=" "
      for token,label in zip(tokens,labels):
          #如果标签是B，开始保存新实体
          if label=='B':
              if current_entity!="":
                  entities.append((current_entity))
              current_entity=token
          #如果标签是I继续追加
          elif label=='I':
              if current_entity:
                  current_entity+=token
          #如果标签是O，就将实体抽取出来添加到列表
          else:
              if current_entity:
                  entities.append(current_entity)
              current_entity="  "
      if current_entity:
          entities.append(current_entity)
      return entities



































