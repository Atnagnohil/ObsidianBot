from src.engine.provider.llm.scheams import LLMChatRequest, LLMChatResponse, ChatChoice, TokenUsage


def build_llm_response(chunk, request: LLMChatRequest, index: int = 0) -> LLMChatResponse:
  """
  从 LangChain 响应块构建 LLMChatResponse。

  从块中提取元数据和使用信息，并构建标准化的响应对象。
  """
  usage_metadata = chunk.usage_metadata if hasattr(chunk, 'usage_metadata') else None

  return LLMChatResponse(
    id=chunk.id,
    timestamp=int(chunk.response_metadata.get("created", 0)),
    model=chunk.response_metadata.get("model_name", request.model),
    choice=ChatChoice(
      message=chunk.content,
      finish_reason=chunk.response_metadata.get("finish_reason"),
      index=index
    ),
    usage=TokenUsage(
      completion_tokens=usage_metadata.get("output_tokens", 0) if usage_metadata else 0,
      prompt_tokens=usage_metadata.get("input_tokens", 0) if usage_metadata else 0,
      total_tokens=usage_metadata.get("total_tokens", 0) if usage_metadata else 0
    )
  )
