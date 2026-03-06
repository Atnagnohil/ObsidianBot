from typing import Optional, List, Dict, Any

from src.engine.content.base import BaseContentManager, ContentLayer, ContentItem
from src.engine.provider.llm import registry
from src.engine.provider.llm.scheams import LLMChatRequest
from src.utils import logger
from src.utils.config import config


class LocalContentProvider(BaseContentManager):
  """
  本地上下文实现（单例模式）。
  """

  _instance: Optional["LocalContentProvider"] = None
  _initialized: bool = False

  def __new__(cls):
    """
    单例模式实现。

    Returns:
        LocalContentProvider 单例实例
    """
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def __init__(self):
    """
    初始化本地上下文提供者。

    只在第一次创建时初始化，后续调用会跳过。
    配置参数从 config.yaml 的 content 节点读取。
    """
    # 如果已经初始化过，直接返回
    if self._initialized:
      return

    # 从配置文件读取参数
    content_config = config.get("content", {})

    self.content: List[ContentItem] = []
    self.user_info: Dict[str, Any] = {}
    self.group_info: Dict[str, Any] = {}
    self.max_content_num = content_config.get("max_content_num", 100)
    self.extract_threshold = content_config.get("extract_threshold", 20)
    self.extract_batch_size = content_config.get("extract_batch_size", 20)
    self._last_extract_count = 0  # 上次总结时的内容数量
    self._initialized = True

    logger.debug(
      f"LocalContentProvider 初始化完成: "
      f"max_content_num={self.max_content_num}, "
      f"extract_threshold={self.extract_threshold}, "
      f"extract_batch_size={self.extract_batch_size}"
    )

  # TODO: 未区分会话key，因此可能导致记忆混乱
  async def add_content(self, content_item: ContentItem, layer: ContentLayer):
    """添加上下文内容到列表中"""
    self.content.append(content_item)

    # 如果超过最大数量，移除最旧的
    if len(self.content) > self.max_content_num:
      self.content.pop(0)

    # 检查是否需要触发总结（异步执行，不阻塞）
    if self._should_extract():
      import asyncio
      # 创建后台任务，不等待完成
      asyncio.create_task(
        self._extract_content_background(
          content_item.user_id, content_item.group_id, layer
        )
      )
      self._last_extract_count = len(self.content)

  def _should_extract(self) -> bool:
    """
    判断是否应该触发总结。

    规则：
    1. 内容数量达到阈值
    2. 距离上次总结增加了足够的内容

    Returns:
        是否应该触发总结
    """
    current_count = len(self.content)

    # 规则1：达到阈值
    if current_count >= self.extract_threshold:
      return True

    # 规则2：距离上次总结增加了批次大小的内容
    if current_count - self._last_extract_count >= self.extract_batch_size:
      return True

    return False

  async def get_content(
    self,
    user_id: str,
    group_id: Optional[str],
    layer: ContentLayer,
    limit: int = 10,
  ) -> List[ContentItem]:
    """
    获取指定用户/群组的上下文内容。

    Args:
        user_id: 用户 ID
        group_id: 群组 ID
        layer: 上下文层级
        limit: 最大返回数量

    Returns:
        上下文内容项列表
    """
    # 根据层级过滤内容
    if layer == ContentLayer.GROUP and group_id:
      filtered = [
        item for item in self.content if item.group_id == group_id
      ]
    elif layer == ContentLayer.USER:
      filtered = [
        item
        for item in self.content
        if item.user_id == user_id and item.group_id is None
      ]
    else:
      filtered = self.content

    # 返回最近的 limit 条
    return filtered[-limit:] if limit > 0 else filtered

  async def clear_content(
    self, user_id: str, group_id: Optional[str], layer: ContentLayer
  ):
    """
    清除指定用户/群组的上下文内容。

    Args:
        user_id: 用户 ID
        group_id: 群组 ID
        layer: 记忆层级
    """
    if layer == ContentLayer.GROUP and group_id:
      self.content = [
        item for item in self.content if item.group_id != group_id
      ]
    elif layer == ContentLayer.USER:
      self.content = [
        item
        for item in self.content
        if not (item.user_id == user_id and item.group_id is None)
      ]
    else:
      self.content.clear()

    # 重置总结计数
    self._last_extract_count = len(self.content)

  async def _extract_content_background(
    self, user_id: str, group_id: Optional[str], layer: ContentLayer
  ):
    """
    后台异步执行总结任务（不阻塞主流程）。

    Args:
        user_id: 用户 ID
        group_id: 群组 ID
        layer: 记忆层级
    """
    try:
      await self.extract_content(user_id, group_id, layer)
    except Exception as e:
      logger.error(f"后台总结任务失败: {e}", exc_info=True)

  async def extract_content(
    self, user_id: str, group_id: Optional[str], layer: ContentLayer
  ):
    """
    提取并总结上下文内容。

    使用 LLM 对历史对话进行总结，提取关键信息。

    Args:
        user_id: 用户 ID
        group_id: 群组 ID
        layer: 记忆层级
    """
    # 获取需要总结的内容
    contents_to_extract = await self.get_content(
      user_id, group_id, layer, limit=self.extract_batch_size
    )

    if not contents_to_extract:
      return

    # 构建对话历史文本
    conversation_text = self._build_conversation_text(contents_to_extract)

    # 根据层级选择不同的提示词
    if layer == ContentLayer.GROUP and group_id:
      extract_prompt = self._build_group_extract_prompt(conversation_text)
    else:
      extract_prompt = self._build_user_extract_prompt(conversation_text)

    try:
      # 调用 LLM 进行总结
      from src.engine.provider.llm.scheams import LLMMessage, MessageRole
      import json
      import re

      logger.debug(f"开始异步总结任务: user_id={user_id}, group_id={group_id}, layer={layer.value}")

      llm = registry.create("siliconflow")

      request = LLMChatRequest(
        model="Qwen/Qwen3.5-122B-A10B",
        message=[LLMMessage(role=MessageRole.USER, content=extract_prompt)],
        stream=False,
        temperature=0.3,  # 降低温度以获得更稳定的 JSON 输出
        max_tokens=512,
      )

      # 获取 LLM 响应
      summary_text = ""
      async for chunk in llm.chat(request):
        summary_text = chunk.choice.message

      logger.debug(f"LLM 总结原始响应: {summary_text}")

      # 尝试提取 JSON（可能包含在 markdown 代码块中）
      json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', summary_text, re.DOTALL)
      if json_match:
        json_str = json_match.group(1)
      else:
        # 尝试直接查找 JSON 对象
        json_match = re.search(r'\{.*\}', summary_text, re.DOTALL)
        if json_match:
          json_str = json_match.group(0)
        else:
          json_str = summary_text

      # 解析 JSON
      try:
        summary_data = json.loads(json_str)
        logger.debug(f"异步总结完成: {summary_data}")

        # 存储总结
        if layer == ContentLayer.GROUP and group_id:
          self.group_info[group_id] = summary_data
        elif layer == ContentLayer.USER:
          self.user_info[user_id] = summary_data

      except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}, 原始文本: {json_str[:200]}")
        # 存储原始文本作为备用
        fallback_data = {
          "main_topics": [],
          "key_information": [summary_text[:100]],
          "user_preferences": [] if layer == ContentLayer.USER else None,
          "group_atmosphere": [] if layer == ContentLayer.GROUP else None,
          "pending_items": [],
          "_raw_text": summary_text,
        }
        if layer == ContentLayer.GROUP and group_id:
          self.group_info[group_id] = fallback_data
        elif layer == ContentLayer.USER:
          self.user_info[user_id] = fallback_data

    except Exception as e:
      logger.error(f"总结提取失败: {e}", exc_info=True)

  def _build_user_extract_prompt(self, conversation_text: str) -> str:
    """
    构建用户对话总结提示词。

    Args:
        conversation_text: 对话文本

    Returns:
        提示词
    """
    return f"""你是一个对话总结助手，需要分析用户的私聊对话并提取关键信息。

请严格按照 JSON 格式返回总结结果。

示例1：
对话历史：
用户: 我想学习 Python
助手: 好的，Python 是一门很适合初学者的编程语言
用户: 有什么推荐的书吗
助手: 推荐《Python 编程：从入门到实践》

返回：
{{
  "main_topics": ["Python 学习", "编程入门"],
  "key_information": ["用户想学习 Python", "推荐了《Python 编程：从入门到实践》"],
  "user_preferences": ["对编程感兴趣", "初学者", "喜欢通过书籍学习"],
  "pending_items": ["等待用户确认是否需要更多学习资源"]
}}

示例2：
对话历史：
用户: 明天天气怎么样
助手: 明天多云，气温 15-22 度
用户: 好的谢谢

返回：
{{
  "main_topics": ["天气查询"],
  "key_information": ["明天多云，15-22度"],
  "user_preferences": ["关注天气信息"],
  "pending_items": []
}}

现在请总结以下私聊对话：
对话历史：
{conversation_text}

要求：
1. 必须返回有效的 JSON 格式
2. 包含四个字段：main_topics, key_information, user_preferences, pending_items
3. 每个字段都是字符串数组
4. user_preferences 重点关注：用户的兴趣、习惯、性格特征、交流风格等
5. 如果某个字段没有内容，返回空数组 []
6. 不要添加任何 JSON 之外的文字

返回："""

  def _build_group_extract_prompt(self, conversation_text: str) -> str:
    """
    构建群组对话总结提示词。

    Args:
        conversation_text: 对话文本

    Returns:
        提示词
    """
    return f"""你是一个对话总结助手，需要分析群组对话并提取关键信息。

请严格按照 JSON 格式返回总结结果。

示例1：
对话历史：
用户A: 大家周末去哪玩
用户B: 我想去爬山
用户C: 爬山+1
助手: 可以考虑去香山，现在红叶正好

返回：
{{
  "main_topics": ["周末活动", "爬山计划"],
  "key_information": ["多人想去爬山", "推荐了香山", "现在是红叶季节"],
  "group_atmosphere": ["活跃", "成员积极参与讨论", "户外活动爱好者"],
  "pending_items": ["确定具体时间和集合地点"]
}}

示例2：
对话历史：
用户A: 今天的作业是什么
用户B: 第三章习题
用户A: 谢谢

返回：
{{
  "main_topics": ["作业查询"],
  "key_information": ["作业是第三章习题"],
  "group_atmosphere": ["学习群", "成员互助"],
  "pending_items": []
}}

现在请总结以下群组对话：
对话历史：
{conversation_text}

要求：
1. 必须返回有效的 JSON 格式
2. 包含四个字段：main_topics, key_information, group_atmosphere, pending_items
3. 每个字段都是字符串数组
4. group_atmosphere 重点关注：群组氛围、成员活跃度、群组主题、互动特点等
5. 如果某个字段没有内容，返回空数组 []
6. 不要添加任何 JSON 之外的文字

返回："""

  def _build_conversation_text(self, contents: List[ContentItem]) -> str:
    """
    构建对话历史文本。

    Args:
        contents: 内容项列表

    Returns:
        格式化的对话文本
    """
    lines = []
    for item in contents:
      role_name = "用户" if item.role.value == "user" else "助手"
      lines.append(f"{role_name}: {item.content}")

    return "\n".join(lines)
