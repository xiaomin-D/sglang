"""
[prefill worker]

0. /generate
1. /prefill_finish to decode router => get decode_id
2. transfer kv cache to worker_(decode_id) (fake this for now, do recomputation)
3. /start_decode to decode router with decode_id to start decoding
4. return all tokens to the client

[decode router]

API Call

`/prefill_finish`
- inputs
    - text
- return
    - decode_worker_id

`/start_decode`
- inputs
    - decode_worker_id
- return
    - output_ids

[decode worker]

1. receive transfered kv cache
2. start decoding

Decode Router FastAPI server that manages routing between prefill and decode workers.
"""
from typing import List, Dict
from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel
import heapq

class PrefillFinishRequest(BaseModel):
    text: str

class GenerateDecodeRequest(BaseModel):
    decode_worker_url: str
    text: str
    sampling_params: Dict[str, int]

class DecodeWorkerState:
    def __init__(self, url: str):
        self.url = url
        self.queue_size = 0  # Number of tokens in waiting queue
    
    def __str__(self) -> str:
        return f"DecodeWorkerState(url='{self.url}', queue_size={self.queue_size})"
    
    def __repr__(self) -> str:
        return self.__str__()

app = FastAPI()

# Store decode worker states
# worker_url -> DecodeWorkerState
decode_workers: Dict[str, DecodeWorkerState] = {}

def init_decode_workers(worker_addresses: List[str]):
    """Initialize decode workers with their addresses."""
    for addr in worker_addresses:
        decode_workers[addr] = DecodeWorkerState(addr)

@app.post("/prefill_finish")
async def prefill_finish(request: PrefillFinishRequest):
    """
    Handle prefill finish request and select least loaded decode worker.
    """
    if not decode_workers:
        raise HTTPException(status_code=500, detail="No decode workers available")
    
    # Find worker with minimum queue size
    selected_worker = min(decode_workers.values(), key=lambda w: w.queue_size)

    print(decode_workers)

    # Update queue size - use length of text string instead of input_ids
    selected_worker.queue_size += len(request.text)

    
    print(f"Prefill finish request received! Selected worker: {selected_worker.url}")

    return {"decode_worker_url": selected_worker.url}

@app.post("/generate_decode")
async def generate_decode(request: GenerateDecodeRequest):
    """
    Route the decoding request to the specified decode worker.
    """
    if request.decode_worker_url not in decode_workers:
        raise HTTPException(status_code=404, detail="Decode worker not found")
    
    print(f"Generate decode request received! Decode worker: {request.decode_worker_url}")
    worker = decode_workers[request.decode_worker_url]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{worker.url}/generate",
                json={"text": request.text, "sampling_params": request.sampling_params}
            )
            response.raise_for_status()
            
            # Update queue size after processing
            worker.queue_size -= len(request.text)
            
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with decode worker: {str(e)}")

# Initialize workers when starting the server
# Example usage:
# init_decode_workers(["http://worker1:8001", "http://worker2:8002"])

def main():
    """CLI entrypoint for running the decode router server."""
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser(description="Run the decode router server")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                      help="Host address to bind to")
    parser.add_argument("--port", type=int, default=8000,
                      help="Port to listen on")
    parser.add_argument("--worker-urls", type=str, required=True,
                      help="Comma-separated list of worker URLs (e.g., http://worker1:8001,http://worker2:8002)")
    
    args = parser.parse_args()
    
    # Initialize workers
    worker_urls = [url.strip() for url in args.worker_urls.split(",")]
    init_decode_workers(worker_urls)
    
    # Start server
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()

