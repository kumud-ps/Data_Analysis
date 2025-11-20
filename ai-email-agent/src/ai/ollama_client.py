import asyncio
import httpx
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ..config.settings import get_settings
from ..utils.logger import get_logger, audit_logger
from ..utils.exceptions import AIServiceError, AIModelNotFoundError, AIResponseError

logger = get_logger(__name__)
settings = get_settings()


class OllamaModel(BaseModel):
    """Model information for Ollama."""
    name: str
    size: int
    modified_at: str


class OllamaResponse(BaseModel):
    """Response from Ollama API."""
    response: str
    done: bool
    model: str
    created_at: str
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(
        self,
        base_url: str = None,
        model_name: str = None,
        timeout: int = None
    ):
        """Initialize Ollama client."""
        self.base_url = base_url or settings.ai.ollama_base_url
        self.model_name = model_name or settings.ai.model_name
        self.timeout = timeout or settings.ai.timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def check_connection(self) -> bool:
        """Check if Ollama service is accessible."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error("Failed to connect to Ollama service", error=str(e))
            return False

    async def list_models(self) -> List[OllamaModel]:
        """List available Ollama models."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("models", []):
                models.append(OllamaModel(
                    name=model.get("name", ""),
                    size=model.get("size", 0),
                    modified_at=model.get("modified_at", "")
                ))

            return models
        except httpx.HTTPError as e:
            logger.error("Failed to list Ollama models", error=str(e))
            raise AIServiceError(f"Failed to list models: {str(e)}")

    async def model_exists(self, model_name: str = None) -> bool:
        """Check if a model exists in Ollama."""
        model = model_name or self.model_name
        try:
            models = await self.list_models()
            return any(m.name == model for m in models)
        except AIServiceError:
            return False

    async def pull_model(self, model_name: str = None) -> bool:
        """Pull a model from Ollama registry."""
        model = model_name or self.model_name
        try:
            response = await self.client.post(
                "/api/pull",
                json={"name": model}
            )
            response.raise_for_status()

            # Stream the response to track progress
            async for line in response.aiter_lines():
                if line:
                    logger.info(f"Pulling model {model}: {line}")

            return True
        except httpx.HTTPError as e:
            logger.error("Failed to pull Ollama model", model=model, error=str(e))
            raise AIServiceError(f"Failed to pull model {model}: {str(e)}")

    async def generate_response(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = None
    ) -> OllamaResponse:
        """Generate a response from Ollama."""
        model_name = model or self.model_name
        temp = temperature if temperature is not None else settings.ai.temperature
        max_tok = max_tokens or settings.ai.max_tokens

        # Check if model exists
        if not await self.model_exists(model_name):
            logger.error("Model not found", model=model_name)
            raise AIModelNotFoundError(model_name)

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_tok
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            logger.info("Generating AI response", model=model_name, prompt_length=len(prompt))

            response = await self.client.post(
                "/api/generate",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            ollama_response = OllamaResponse(**data)

            # Log AI usage
            audit_logger.log_ai_response(
                sender="system",
                model=model_name,
                tokens_used=ollama_response.eval_count or 0
            )

            logger.info(
                "AI response generated successfully",
                model=model_name,
                response_length=len(ollama_response.response),
                eval_count=ollama_response.eval_count
            )

            return ollama_response

        except httpx.HTTPError as e:
            logger.error("HTTP error generating AI response", error=str(e))
            raise AIResponseError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error("Error generating AI response", error=str(e))
            raise AIResponseError(f"Generation error: {str(e)}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> OllamaResponse:
        """Generate a chat completion response."""
        model_name = model or self.model_name
        temp = temperature if temperature is not None else settings.ai.temperature
        max_tok = max_tokens or settings.ai.max_tokens

        # Check if model exists
        if not await self.model_exists(model_name):
            logger.error("Model not found", model=model_name)
            raise AIModelNotFoundError(model_name)

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_tok
            }
        }

        try:
            logger.info("Generating chat completion", model=model_name, message_count=len(messages))

            response = await self.client.post(
                "/api/chat",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            ollama_response = OllamaResponse(
                response=data.get("message", {}).get("content", ""),
                done=data.get("done", False),
                model=model_name,
                created_at=data.get("created_at", ""),
                eval_count=data.get("eval_count"),
                total_duration=data.get("total_duration"),
                prompt_eval_count=data.get("prompt_eval_count")
            )

            # Log AI usage
            audit_logger.log_ai_response(
                sender="system",
                model=model_name,
                tokens_used=ollama_response.eval_count or 0
            )

            logger.info(
                "Chat completion generated successfully",
                model=model_name,
                response_length=len(ollama_response.response),
                eval_count=ollama_response.eval_count
            )

            return ollama_response

        except httpx.HTTPError as e:
            logger.error("HTTP error generating chat completion", error=str(e))
            raise AIResponseError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error("Error generating chat completion", error=str(e))
            raise AIResponseError(f"Generation error: {str(e)}")

    async def analyze_email_content(
        self,
        email_body: str,
        sender: str = None,
        subject: str = None
    ) -> Dict[str, Any]:
        """Analyze email content and extract key information."""
        analysis_prompt = f"""
        Analyze this email and provide insights:

        From: {sender or 'Unknown'}
        Subject: {subject or 'No subject'}

        Email content:
        {email_body}

        Please provide:
        1. Email type (business inquiry, personal message, support request, meeting request, etc.)
        2. Urgency level (low, medium, high)
        3. Key topics mentioned
        4. Required action needed
        5. Tone (formal, informal, professional, casual)

        Respond in JSON format with these fields: type, urgency, topics, action_required, tone
        """

        try:
            response = await self.generate_response(
                prompt=analysis_prompt,
                temperature=0.3,  # Lower temperature for consistent analysis
                system_prompt="You are an email analysis assistant. Always respond in valid JSON format."
            )

            # Try to parse the response as JSON
            import json
            try:
                analysis = json.loads(response.response)
                return analysis
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "type": "unknown",
                    "urgency": "medium",
                    "topics": [],
                    "action_required": False,
                    "tone": "neutral",
                    "raw_analysis": response.response
                }

        except Exception as e:
            logger.error("Error analyzing email content", error=str(e))
            raise AIServiceError(f"Email analysis failed: {str(e)}")