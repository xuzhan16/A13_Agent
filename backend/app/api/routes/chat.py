# backend/app/api/routes/chat.py
import os
import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量读取配置
API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://aihubmix.com/v1")
API_KEY = os.getenv("LLM_API_KEY", "sk-PHNhMDTobgukVxcsEa9219CdCc2e466e96568106D64d85F9")
MODEL = os.getenv("LLM_MODEL", "coding-glm-5-free")

# 创建路由器
router = APIRouter()

# 定义请求和响应模型
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None

@router.post("/completions")
async def chat_completions(request: ChatRequest):
    """
    转发聊天请求到目标 AI 服务（OpenAI 兼容格式）
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured")

    # 构建请求体
    payload = {
        "model": MODEL,
        "messages": [msg.dict() for msg in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "stream": request.stream,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    # 使用 httpx 异步客户端发送请求
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            logger.info(f"Sending request to {API_BASE_URL}/chat/completions")
            response = await client.post(
                f"{API_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    """健康检查端点"""
    return {
        "status": "ok",
        "model": MODEL,
        "api_key_configured": bool(API_KEY),
        "api_base_url": API_BASE_URL,
    }