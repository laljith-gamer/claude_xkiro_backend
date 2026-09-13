"""
xKiro OpenAI-to-Anthropic API Proxy Converter
=============================================
Converts Anthropic API format (POST /v1/messages) to OpenAI format
and forwards to xKiro (api.xkiro.com).

This lets you use xKiro's 40+ free models with any tool that
expects the Anthropic API (Claude Desktop, Claude Code, etc.)

Usage:
    python proxy.py
    
Then set ANTHROPIC_BASE_URL=http://127.0.0.1:3000 in your tool.
"""

import os
import json
import sys
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    os.system(f"{sys.executable} -m pip install python-dotenv -q")
    from dotenv import load_dotenv

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system(f"{sys.executable} -m pip install httpx -q")
    import httpx

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import StreamingResponse, JSONResponse
    import uvicorn
except ImportError:
    print("Installing fastapi and uvicorn...")
    os.system(f"{sys.executable} -m pip install fastapi uvicorn -q")
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import StreamingResponse, JSONResponse
    import uvicorn

# Load .env from same directory as this script
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "https://api.xkiro.com/v1")
UPSTREAM_API_KEY = os.getenv("UPSTREAM_API_KEY", "")
UPSTREAM_MODEL = os.getenv("UPSTREAM_MODEL", "")  # Leave empty to use MODEL_MAP
LISTEN_HOST = os.getenv("LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.getenv("LISTEN_PORT", "3000"))

# ─── Claude Model → xKiro Free Model Mapping ──────────────────
# When Claude Desktop sends a model name, the proxy maps it to a real free model.
# You can override any mapping in .env with MODEL_MAP_<CLAUDE_NAME>=<xkiro_model>
DEFAULT_MODEL_MAP = {
    # Claude Model (from selector)         →  xKiro Free Model (actual)
    "claude-opus-4.8":       "mistralai/mistral-large-2512",      # Best overall
    "claude-sonnet-5":       "mistralai/mistral-large-2512",      # Best vision+reasoning
    "claude-fable-5":        "mistralai/codestral-2508",          # Best for coding
    "claude-opus-5":         "mistralai/mistral-small-2603",      # Fast + powerful
    "claude-sonnet-4.6":     "mistralai/mistral-medium-3.5",      # Mistral vision
    "claude-haiku-4.5":      "mistralai/ministral-3b",            # Fast answers
    "claude-opus-4.6":       "mistralai/ministral-8b",            # Reasoning
    "claude-fable-5-1":      "mistralai/devstral-medium",         # Coding
    "claude-opus-4.7":       "sensenova/sensenova-6.7-flash-lite",# Alternative
}

# Load custom overrides from .env (e.g. MODEL_MAP_OPUS_4_8=deepseek/deepseek-v4-flash)
MODEL_MAP = dict(DEFAULT_MODEL_MAP)
for key, val in os.environ.items():
    if key.startswith("MODEL_MAP_"):
        claude_name = key[10:].lower().replace("_", "-")
        # Convert e.g. MODEL_MAP_OPUS_4_8 → claude-opus-4.8 (try with dots)
        # Simple approach: just store as-is and also try with dots
        claude_name_dot = claude_name
        # Replace last dash before a digit with a dot (e.g. opus-4-8 → opus-4.8)
        import re
        claude_name_dot = re.sub(r'-(\d+)$', r'.\1', claude_name)
        MODEL_MAP[f"claude-{claude_name}"] = val
        MODEL_MAP[f"claude-{claude_name_dot}"] = val

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("xkiro-proxy")

app = FastAPI(title="xKiro Anthropic Proxy", version="1.0.0")


# ─── Message Conversion ───────────────────────────────────────

def anthropic_to_openai_messages(anthropic_messages: list) -> list:
    """Convert Anthropic message format to OpenAI message format."""
    openai_messages = []
    
    for msg in anthropic_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        # Handle string content directly
        if isinstance(content, str):
            openai_messages.append({"role": role, "content": content})
            continue
        
        # Handle content blocks (Anthropic format)
        if isinstance(content, list):
            parts = []
            tool_calls = []
            tool_results = []
            
            for block in content:
                block_type = block.get("type", "")
                
                if block_type == "text":
                    parts.append({"type": "text", "text": block.get("text", "")})
                
                elif block_type == "image":
                    source = block.get("source", {})
                    if source.get("type") == "base64":
                        parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{source.get('media_type', 'image/png')};base64,{source.get('data', '')}"
                            }
                        })
                    elif source.get("type") == "url":
                        parts.append({
                            "type": "image_url",
                            "image_url": {"url": source.get("url", "")}
                        })
                
                elif block_type == "tool_use":
                    tool_calls.append({
                        "id": block.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(block.get("input", {}))
                        }
                    })
                
                elif block_type == "tool_result":
                    result_content = block.get("content", "")
                    if isinstance(result_content, list):
                        text_parts = []
                        for rc in result_content:
                            if rc.get("type") == "text":
                                text_parts.append(rc.get("text", ""))
                        result_content = "\n".join(text_parts)
                    
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": str(result_content)
                    })
            
            if tool_calls:
                msg_obj = {"role": role}
                if parts:
                    if len(parts) == 1 and parts[0].get("type") == "text":
                        msg_obj["content"] = parts[0]["text"]
                    else:
                        msg_obj["content"] = parts
                else:
                    msg_obj["content"] = ""
                msg_obj["tool_calls"] = tool_calls
                openai_messages.append(msg_obj)
            elif tool_results:
                for tr in tool_results:
                    openai_messages.append(tr)
            elif parts:
                if len(parts) == 1 and parts[0].get("type") == "text":
                    openai_messages.append({"role": role, "content": parts[0]["text"]})
                else:
                    openai_messages.append({"role": role, "content": parts})
            else:
                openai_messages.append({"role": role, "content": ""})
    
    return openai_messages


def anthropic_to_openai_tools(anthropic_tools: list) -> list:
    """Convert Anthropic tool definitions to OpenAI function format."""
    openai_tools = []
    for tool in anthropic_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {})
            }
        })
    return openai_tools


def build_openai_request(anthropic_body: dict) -> dict:
    """Convert full Anthropic /v1/messages request to OpenAI /v1/chat/completions request."""
    
    messages = []
    
    # System message
    system = anthropic_body.get("system", "")
    if system:
        if isinstance(system, str):
            messages.append({"role": "system", "content": system})
        elif isinstance(system, list):
            # Anthropic system can be a list of content blocks
            text_parts = []
            for block in system:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            messages.append({"role": "system", "content": "\n".join(text_parts)})
    
    # Convert messages
    anthropic_messages = anthropic_body.get("messages", [])
    messages.extend(anthropic_to_openai_messages(anthropic_messages))
    
    # Resolve model: MODEL_MAP (claude -> xkiro) > UPSTREAM_MODEL override > fallback
    requested_model = anthropic_body.get("model", "")
    if UPSTREAM_MODEL:
        # Global override set in .env
        model = UPSTREAM_MODEL
    elif requested_model in MODEL_MAP:
        # Map Claude model name to xKiro free model
        model = MODEL_MAP[requested_model]
        log.info(f"  MODEL MAP: {requested_model} -> {model}")
    else:
        # Fallback
        model = "deepseek/deepseek-v4-pro"
        log.info(f"  MODEL (unmapped): {requested_model} -> {model}")
    
    openai_req = {
        "model": model,
        "messages": messages,
        "stream": anthropic_body.get("stream", False),
    }
    
    # Max tokens (output tokens)
    # Claude Desktop usually caps requests at 4096 or 8192 output tokens.
    # DeepSeek v4 Pro supports 65536 output tokens. Override if using DeepSeek.
    if "deepseek-v4" in model:
        openai_req["max_tokens"] = 65536
    else:
        openai_req["max_tokens"] = anthropic_body.get("max_tokens", 4096)
    
    # Temperature
    if "temperature" in anthropic_body:
        openai_req["temperature"] = anthropic_body["temperature"]
    
    # Top-p
    if "top_p" in anthropic_body:
        openai_req["top_p"] = anthropic_body["top_p"]
    
    # Stop sequences
    if "stop_sequences" in anthropic_body:
        openai_req["stop"] = anthropic_body["stop_sequences"]
    
    # Tools
    if "tools" in anthropic_body:
        openai_req["tools"] = anthropic_to_openai_tools(anthropic_body["tools"])
    
    return openai_req


# ─── Response Conversion ──────────────────────────────────────

def openai_to_anthropic_response(openai_resp: dict, model: str) -> dict:
    """Convert OpenAI chat completion response to Anthropic messages response."""
    
    choice = openai_resp.get("choices", [{}])[0]
    message = choice.get("message", {})
    
    content_blocks = []
    
    # Text content
    text = message.get("content", "")
    if text:
        content_blocks.append({"type": "text", "text": text})
    
    # Tool calls
    tool_calls = message.get("tool_calls", [])
    for tc in tool_calls:
        func = tc.get("function", {})
        try:
            arguments = json.loads(func.get("arguments", "{}"))
        except json.JSONDecodeError:
            arguments = {}
        
        content_blocks.append({
            "type": "tool_use",
            "id": tc.get("id", f"toolu_{int(time.time())}"),
            "name": func.get("name", ""),
            "input": arguments
        })
    
    if not content_blocks:
        content_blocks.append({"type": "text", "text": ""})
    
    # Map finish reason
    finish_reason = choice.get("finish_reason", "stop")
    stop_reason_map = {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "function_call": "tool_use",
        "content_filter": "end_turn",
    }
    stop_reason = stop_reason_map.get(finish_reason, "end_turn")
    
    # Usage
    usage = openai_resp.get("usage", {})
    
    return {
        "id": openai_resp.get("id", f"msg_{int(time.time())}"),
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content_blocks,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    }


# ─── Streaming Conversion ─────────────────────────────────────

async def convert_stream(openai_stream, model: str):
    """Convert OpenAI SSE stream to Anthropic SSE stream format."""
    
    msg_id = f"msg_{int(time.time())}"
    
    # Send message_start
    start_event = {
        "type": "message_start",
        "message": {
            "id": msg_id,
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }
    }
    yield f"event: message_start\ndata: {json.dumps(start_event)}\n\n"
    
    content_block_started = False
    tool_call_blocks = {}  # Track tool calls by index
    current_text_index = 0
    
    async for line in openai_stream:
        line = line.strip()
        if not line:
            continue
        
        line_str = line if isinstance(line, str) else line.decode("utf-8")
        
        if not line_str.startswith("data: "):
            continue
        
        data_str = line_str[6:]
        if data_str == "[DONE]":
            break
        
        try:
            chunk = json.loads(data_str)
        except json.JSONDecodeError:
            continue
        
        choices = chunk.get("choices", [])
        if not choices:
            continue
        
        delta = choices[0].get("delta", {})
        finish_reason = choices[0].get("finish_reason")
        
        # Handle text content
        text_content = delta.get("content", "")
        if text_content:
            if not content_block_started:
                # Start text block
                block_start = {
                    "type": "content_block_start",
                    "index": current_text_index,
                    "content_block": {"type": "text", "text": ""}
                }
                yield f"event: content_block_start\ndata: {json.dumps(block_start)}\n\n"
                content_block_started = True
            
            block_delta = {
                "type": "content_block_delta",
                "index": current_text_index,
                "delta": {"type": "text_delta", "text": text_content}
            }
            yield f"event: content_block_delta\ndata: {json.dumps(block_delta)}\n\n"
        
        # Handle tool calls
        tool_calls = delta.get("tool_calls", [])
        for tc in tool_calls:
            tc_index = tc.get("index", 0)
            
            if tc_index not in tool_call_blocks:
                # Close text block if open
                if content_block_started:
                    block_stop = {"type": "content_block_stop", "index": current_text_index}
                    yield f"event: content_block_stop\ndata: {json.dumps(block_stop)}\n\n"
                    content_block_started = False
                    current_text_index += 1
                
                # Start tool use block
                tool_call_blocks[tc_index] = {
                    "id": tc.get("id", f"toolu_{int(time.time())}_{tc_index}"),
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": ""
                }
                
                block_idx = current_text_index + tc_index
                block_start = {
                    "type": "content_block_start",
                    "index": block_idx,
                    "content_block": {
                        "type": "tool_use",
                        "id": tool_call_blocks[tc_index]["id"],
                        "name": tool_call_blocks[tc_index]["name"],
                        "input": {}
                    }
                }
                yield f"event: content_block_start\ndata: {json.dumps(block_start)}\n\n"
            
            # Accumulate arguments
            args_delta = tc.get("function", {}).get("arguments", "")
            if args_delta:
                tool_call_blocks[tc_index]["arguments"] += args_delta
                block_idx = current_text_index + tc_index
                block_delta = {
                    "type": "content_block_delta",
                    "index": block_idx,
                    "delta": {"type": "input_json_delta", "partial_json": args_delta}
                }
                yield f"event: content_block_delta\ndata: {json.dumps(block_delta)}\n\n"
        
        # Handle finish
        if finish_reason:
            # Close any open text block
            if content_block_started:
                block_stop = {"type": "content_block_stop", "index": current_text_index}
                yield f"event: content_block_stop\ndata: {json.dumps(block_stop)}\n\n"
            
            # Close any open tool blocks
            for tc_idx in tool_call_blocks:
                block_idx = current_text_index + tc_idx
                block_stop = {"type": "content_block_stop", "index": block_idx}
                yield f"event: content_block_stop\ndata: {json.dumps(block_stop)}\n\n"
            
            stop_reason_map = {
                "stop": "end_turn",
                "length": "max_tokens",
                "tool_calls": "tool_use",
                "function_call": "tool_use",
            }
            stop_reason = stop_reason_map.get(finish_reason, "end_turn")
            
            # Usage from the chunk if available
            usage = chunk.get("usage", {})
            
            msg_delta = {
                "type": "message_delta",
                "delta": {
                    "stop_reason": stop_reason,
                    "stop_sequence": None
                },
                "usage": {
                    "output_tokens": usage.get("completion_tokens", 0)
                }
            }
            yield f"event: message_delta\ndata: {json.dumps(msg_delta)}\n\n"
    
    # Send message_stop
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"


# ─── API Endpoints ────────────────────────────────────────────

@app.get("/healthz")
@app.get("/health")
async def health():
    return {"status": "ok", "model": UPSTREAM_MODEL, "upstream": UPSTREAM_BASE_URL}


@app.post("/v1/messages")
async def messages(request: Request):
    """Handle Anthropic /v1/messages requests by converting to OpenAI format."""
    
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"type": "invalid_request_error", "message": str(e)}}
        )
    
    model = UPSTREAM_MODEL or body.get("model", "deepseek/deepseek-v4-pro")
    is_stream = body.get("stream", False)
    
    log.info(f"{'STREAM' if is_stream else 'REQUEST'} → model={model}")
    
    # Convert to OpenAI format
    openai_req = build_openai_request(body)
    
    headers = {
        "Authorization": f"Bearer {UPSTREAM_API_KEY}",
        "Content-Type": "application/json",
    }
    
    url = f"{UPSTREAM_BASE_URL.rstrip('/')}/chat/completions"
    
    if is_stream:
        # Streaming response
        async def stream_generator():
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", url, json=openai_req, headers=headers) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        log.error(f"Upstream error {resp.status_code}: {error_body.decode()}")
                        error_event = {
                            "type": "error",
                            "error": {
                                "type": "api_error",
                                "message": f"Upstream returned {resp.status_code}: {error_body.decode()[:500]}"
                            }
                        }
                        yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
                        return
                    
                    async for chunk in convert_stream(resp.aiter_lines(), model):
                        yield chunk
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    else:
        # Non-streaming response
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(url, json=openai_req, headers=headers)
        
        if resp.status_code != 200:
            log.error(f"Upstream error {resp.status_code}: {resp.text[:500]}")
            return JSONResponse(
                status_code=resp.status_code,
                content={
                    "error": {
                        "type": "api_error",
                        "message": f"Upstream returned {resp.status_code}: {resp.text[:500]}"
                    }
                }
            )
        
        openai_resp = resp.json()
        anthropic_resp = openai_to_anthropic_response(openai_resp, model)
        
        log.info(f"RESPONSE ← {anthropic_resp['usage']['input_tokens']}in/{anthropic_resp['usage']['output_tokens']}out tokens")
        
        return JSONResponse(content=anthropic_resp)


@app.get("/v1/models")
async def list_models():
    """Return Anthropic-format models list so Claude Desktop knows the limits."""
    anthropic_models = []
    
    # Tell Claude Desktop that all our mapped models support 1M context
    for claude_id, real_model in MODEL_MAP.items():
        anthropic_models.append({
            "type": "model",
            "id": claude_id,
            "display_name": f"{claude_id} ({real_model})",
            "max_input_tokens": 1048576,  # 1 Million context!
            "max_tokens": 65536,          # Max output tokens
            "created_at": "2025-01-01T00:00:00Z"
        })
        
    return JSONResponse(content={
        "data": anthropic_models,
        "has_more": False,
        "first_id": anthropic_models[0]["id"] if anthropic_models else None,
        "last_id": anthropic_models[-1]["id"] if anthropic_models else None
    })


# ─── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    if not UPSTREAM_API_KEY or UPSTREAM_API_KEY == "xk-paste-your-xkiro-api-key-here":
        print("=" * 50)
        print("  ERROR: API key not configured!")
        print("  Edit .env and set your xKiro API key.")
        print("  Get a FREE key at: https://xkiro.com")
        print("=" * 50)
        sys.exit(1)
    
    print("=" * 60)
    print("  xKiro -> Anthropic Proxy Converter")
    print("=" * 60)
    print(f"  Upstream:  {UPSTREAM_BASE_URL}")
    print(f"  Listen:    http://{LISTEN_HOST}:{LISTEN_PORT}")
    print(f"  Health:    http://{LISTEN_HOST}:{LISTEN_PORT}/healthz")
    print()
    if UPSTREAM_MODEL:
        print(f"  FORCED MODEL: {UPSTREAM_MODEL} (all requests)")
        print("  (Clear UPSTREAM_MODEL in .env to use per-model mapping)")
    else:
        print("  Claude Model (selector)   ->  Real xKiro Model")
        print("  " + "-" * 56)
        for claude_m, real_m in MODEL_MAP.items():
            pad = 26 - len(claude_m)
            print(f"  {claude_m}{' '*pad}->  {real_m}")
    print()
    print("=" * 60)
    print()
    
    uvicorn.run(app, host=LISTEN_HOST, port=LISTEN_PORT, log_level="info")
