"""
LLM Router Service
Routes requests to appropriate LLM backends (local Ollama or cloud Claude)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import httpx
import yaml
import os
import re
import logging
from anthropic import Anthropic
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('llm_router_requests_total', 'Total requests', ['model_type', 'model_key'])
REQUEST_DURATION = Histogram('llm_router_request_duration_seconds', 'Request duration', ['model_type', 'model_key'])
ERROR_COUNT = Counter('llm_router_errors_total', 'Total errors', ['model_type', 'error_type'])

app = FastAPI(title="LLM Router", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Next.js UI
        "http://localhost:3000",  # Grafana
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
with open("router_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize clients
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", config["ollama"]["base_url"])
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

if CLAUDE_API_KEY:
    anthropic_client = Anthropic(api_key=CLAUDE_API_KEY)
else:
    anthropic_client = None
    logger.warning("CLAUDE_API_KEY not set - cloud reasoning will be unavailable")


class LLMRequest(BaseModel):
    """Request model for LLM inference"""
    task_type: str = Field(..., description="Type of task (e.g., 'smart_contract_analysis', 'triage')")
    prompt: str = Field(..., description="Input prompt")
    system_prompt: Optional[str] = Field(None, description="System prompt (optional)")
    max_tokens: Optional[int] = Field(None, description="Override max tokens")
    temperature: Optional[float] = Field(None, description="Override temperature")
    stream: bool = Field(False, description="Stream response")


class LLMResponse(BaseModel):
    """Response model for LLM inference"""
    response: str
    model_used: str
    model_type: str
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingRequest(BaseModel):
    """Request model for embeddings"""
    texts: List[str] = Field(..., description="Texts to embed")


class EmbeddingResponse(BaseModel):
    """Response model for embeddings"""
    embeddings: List[List[float]]
    model_used: str
    dimensions: int


def match_task_to_model(task_type: str) -> tuple[str, str, dict]:
    """
    Match task type to appropriate model configuration
    Returns: (model_type, model_key, model_config)
    """
    for rule in config["routing"]:
        pattern = rule["task_pattern"]
        if re.search(pattern, task_type, re.IGNORECASE):
            model_type = rule["model_type"]
            model_key = rule["model_key"]
            model_config = config["models"][model_type][model_key]
            return model_type, model_key, model_config
    
    # Default to fast triage for unknown tasks
    logger.warning(f"No routing rule matched for task '{task_type}', using fast_triage")
    return "local", "fast_triage", config["models"]["local"]["fast_triage"]


async def call_ollama(model: str, prompt: str, system_prompt: Optional[str] = None, 
                     max_tokens: int = 2048, temperature: float = 0.3) -> Dict[str, Any]:
    """Call local Ollama model"""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        }
    }
    
    if system_prompt:
        payload["system"] = system_prompt
    
    async with httpx.AsyncClient(timeout=config["ollama"]["timeout"]) as client:
        for attempt in range(config["ollama"]["retry_attempts"]):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                return {
                    "response": result.get("response", ""),
                    "tokens": result.get("eval_count", 0),
                    "metadata": {
                        "total_duration": result.get("total_duration"),
                        "load_duration": result.get("load_duration"),
                        "prompt_eval_count": result.get("prompt_eval_count"),
                    }
                }
            except Exception as e:
                logger.error(f"Ollama request failed (attempt {attempt + 1}): {e}")
                if attempt < config["ollama"]["retry_attempts"] - 1:
                    await asyncio.sleep(config["ollama"]["retry_delay"])
                else:
                    raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {str(e)}")


async def call_claude(model: str, prompt: str, system_prompt: Optional[str] = None,
                     max_tokens: int = 4096, temperature: float = 0.1) -> Dict[str, Any]:
    """Call Claude API"""
    if not anthropic_client:
        raise HTTPException(status_code=503, detail="Claude API key not configured")
    
    try:
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = anthropic_client.messages.create(**kwargs)
        
        return {
            "response": response.content[0].text,
            "tokens": response.usage.output_tokens,
            "metadata": {
                "input_tokens": response.usage.input_tokens,
                "model": response.model,
            }
        }
    except Exception as e:
        logger.error(f"Claude request failed: {e}")
        raise HTTPException(status_code=503, detail=f"Claude API error: {str(e)}")


async def get_embeddings_ollama(model: str, texts: List[str]) -> List[List[float]]:
    """Get embeddings from Ollama"""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    
    embeddings = []
    async with httpx.AsyncClient(timeout=config["ollama"]["timeout"]) as client:
        for text in texts:
            payload = {
                "model": model,
                "prompt": text
            }
            
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                embeddings.append(result.get("embedding", []))
            except Exception as e:
                logger.error(f"Embedding request failed: {e}")
                raise HTTPException(status_code=503, detail=f"Embedding service unavailable: {str(e)}")
    
    return embeddings


@app.post("/generate", response_model=LLMResponse)
async def generate(request: LLMRequest):
    """Generate text using appropriate LLM"""
    start_time = time.time()
    
    try:
        # Match task to model
        model_type, model_key, model_config = match_task_to_model(request.task_type)
        
        # Track metrics
        REQUEST_COUNT.labels(model_type=model_type, model_key=model_key).inc()
        
        # Get model parameters
        model_name = model_config["model"]
        max_tokens = request.max_tokens or model_config.get("max_tokens", 2048)
        temperature = request.temperature or model_config.get("temperature", 0.3)
        
        logger.info(f"Routing task '{request.task_type}' to {model_type}/{model_key} ({model_name})")
        
        # Call appropriate backend
        if model_config["endpoint"] == "ollama":
            result = await call_ollama(
                model=model_name,
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        elif model_config["endpoint"] == "anthropic":
            result = await call_claude(
                model=model_name,
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        else:
            raise HTTPException(status_code=500, detail=f"Unknown endpoint: {model_config['endpoint']}")
        
        # Track duration
        duration = time.time() - start_time
        REQUEST_DURATION.labels(model_type=model_type, model_key=model_key).observe(duration)
        
        return LLMResponse(
            response=result["response"],
            model_used=model_name,
            model_type=f"{model_type}/{model_key}",
            tokens_used=result.get("tokens"),
            metadata=result.get("metadata")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        ERROR_COUNT.labels(model_type="unknown", error_type=type(e).__name__).inc()
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed", response_model=EmbeddingResponse)
async def embed(request: EmbeddingRequest):
    """Generate embeddings"""
    try:
        model_config = config["models"]["local"]["embeddings"]
        model_name = model_config["model"]
        
        logger.info(f"Generating embeddings for {len(request.texts)} texts using {model_name}")
        
        embeddings = await get_embeddings_ollama(model_name, request.texts)
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model_used=model_name,
            dimensions=model_config.get("dimensions", 768)
        )
    
    except Exception as e:
        ERROR_COUNT.labels(model_type="local", error_type=type(e).__name__).inc()
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Check Ollama connectivity
    ollama_healthy = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_healthy = response.status_code == 200
    except:
        pass
    
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "ollama": "connected" if ollama_healthy else "disconnected",
        "claude": "configured" if anthropic_client else "not_configured"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/models")
async def list_models():
    """List available models and routing configuration"""
    return {
        "local_models": config["models"]["local"],
        "cloud_models": config["models"]["cloud"],
        "routing_rules": config["routing"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
