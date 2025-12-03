from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Set
from datetime import datetime
from enum import Enum
import asyncio
import json
from collections import defaultdict

app = FastAPI(
    title="Streaming Indexer",
    description="Real-time blockchain event indexing and WebSocket streaming",
    version="1.0.0"
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory storage for indexed events
indexed_events: List[Dict] = []
event_index: Dict[str, List[Dict]] = defaultdict(list)  # contract_address -> events
subscription_topics: Dict[str, Set[WebSocket]] = defaultdict(set)  # topic -> websockets

# Active WebSocket connections
active_connections: Set[WebSocket] = set()

class Chain(str, Enum):
    """Supported blockchains"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"

class EventType(str, Enum):
    """Types of blockchain events"""
    TRANSFER = "Transfer"
    APPROVAL = "Approval"
    SWAP = "Swap"
    MINT = "Mint"
    BURN = "Burn"
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    OWNERSHIP_TRANSFERRED = "OwnershipTransferred"
    PAUSED = "Paused"
    UNPAUSED = "Unpaused"

class IndexRequest(BaseModel):
    """Request to index a contract"""
    contract_address: str
    chain: Chain
    start_block: Optional[int] = None
    event_types: Optional[List[EventType]] = None
    backfill: bool = Field(default=False, description="Backfill historical events")

class QueryRequest(BaseModel):
    """Request to query indexed events"""
    contract_address: Optional[str] = None
    chain: Optional[Chain] = None
    event_type: Optional[EventType] = None
    from_block: Optional[int] = None
    to_block: Optional[int] = None
    limit: int = Field(default=100, le=1000)

class BlockchainEvent(BaseModel):
    """Blockchain event structure"""
    event_id: str
    contract_address: str
    chain: Chain
    event_type: EventType
    block_number: int
    transaction_hash: str
    log_index: int
    args: Dict[str, Any]
    timestamp: datetime

class EventIndexer:
    """
    Real-time blockchain event indexer
    """
    
    def __init__(self):
        self.indexed_contracts: Dict[str, Dict] = {}
        self.current_blocks: Dict[Chain, int] = {
            Chain.ETHEREUM: 18500000,
            Chain.BSC: 33000000,
            Chain.POLYGON: 49000000,
            Chain.ARBITRUM: 150000000,
            Chain.OPTIMISM: 110000000,
        }
    
    async def start_indexing(self, request: IndexRequest) -> Dict[str, Any]:
        """
        Start indexing events for a contract
        
        In production, this would:
        - Connect to RPC node
        - Subscribe to contract events
        - Process events in real-time
        - Store in database
        """
        contract_key = f"{request.chain.value}:{request.contract_address}"
        
        if contract_key in self.indexed_contracts:
            return {
                "status": "already_indexing",
                "contract": request.contract_address,
                "chain": request.chain.value
            }
        
        # Register contract for indexing
        self.indexed_contracts[contract_key] = {
            "contract_address": request.contract_address,
            "chain": request.chain.value,
            "start_block": request.start_block or self.current_blocks[request.chain],
            "indexed_count": 0,
            "last_block": self.current_blocks[request.chain],
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Start background indexing
        asyncio.create_task(self._index_contract(request))
        
        return {
            "status": "indexing_started",
            "contract": request.contract_address,
            "chain": request.chain.value,
            "start_block": self.current_blocks[request.chain]
        }
    
    async def _index_contract(self, request: IndexRequest):
        """
        Background task to index contract events
        
        Simulates real-time event processing
        """
        contract_key = f"{request.chain.value}:{request.contract_address}"
        
        # Backfill historical events if requested
        if request.backfill and request.start_block:
            await self._backfill_events(request)
        
        # Continuous indexing loop (simulated)
        while contract_key in self.indexed_contracts:
            await asyncio.sleep(2)  # Simulate block time
            
            # Simulate new block
            current_block = self.current_blocks[request.chain]
            self.current_blocks[request.chain] += 1
            
            # Simulate events (in production, fetch from RPC)
            simulated_events = self._simulate_events(
                request.contract_address,
                request.chain,
                current_block,
                request.event_types or []
            )
            
            for event in simulated_events:
                # Store event
                indexed_events.append(event)
                event_index[request.contract_address].append(event)
                
                # Update contract stats
                self.indexed_contracts[contract_key]["indexed_count"] += 1
                self.indexed_contracts[contract_key]["last_block"] = current_block
                
                # Broadcast to WebSocket subscribers
                await self._broadcast_event(event)
    
    async def _backfill_events(self, request: IndexRequest):
        """
        Backfill historical events
        
        In production, would query historical blocks
        """
        if not request.start_block:
            return
        
        current = self.current_blocks[request.chain]
        blocks_to_backfill = min(current - request.start_block, 1000)  # Limit backfill
        
        for block_offset in range(blocks_to_backfill):
            block_num = request.start_block + block_offset
            
            events = self._simulate_events(
                request.contract_address,
                request.chain,
                block_num,
                request.event_types or []
            )
            
            for event in events:
                indexed_events.append(event)
                event_index[request.contract_address].append(event)
            
            await asyncio.sleep(0.01)  # Don't block too long
    
    def _simulate_events(
        self,
        contract_address: str,
        chain: Chain,
        block_number: int,
        event_types: List[EventType]
    ) -> List[Dict]:
        """
        Simulate blockchain events (for demo)
        
        In production, would parse actual blockchain events
        """
        import random
        
        # Randomly generate 0-2 events per block
        if random.random() > 0.3:
            return []
        
        num_events = random.randint(1, 2)
        events = []
        
        for i in range(num_events):
            # Pick random event type
            if event_types:
                event_type = random.choice(event_types)
            else:
                event_type = random.choice(list(EventType))
            
            # Generate event data
            event = {
                "event_id": f"{block_number}:{i}",
                "contract_address": contract_address,
                "chain": chain.value,
                "event_type": event_type.value,
                "block_number": block_number,
                "transaction_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                "log_index": i,
                "args": self._generate_event_args(event_type),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            events.append(event)
        
        return events
    
    def _generate_event_args(self, event_type: EventType) -> Dict[str, Any]:
        """Generate simulated event arguments"""
        import random
        
        base_address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
        
        args_map = {
            EventType.TRANSFER: {
                "from": base_address,
                "to": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                "value": str(random.randint(1000, 1000000) * 10**18)
            },
            EventType.APPROVAL: {
                "owner": base_address,
                "spender": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                "value": str(random.randint(1000, 1000000) * 10**18)
            },
            EventType.SWAP: {
                "sender": base_address,
                "amount0In": str(random.randint(1000, 100000) * 10**18),
                "amount1In": "0",
                "amount0Out": "0",
                "amount1Out": str(random.randint(1000, 100000) * 10**18),
                "to": f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
            },
            EventType.OWNERSHIP_TRANSFERRED: {
                "previousOwner": base_address,
                "newOwner": f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
            }
        }
        
        return args_map.get(event_type, {"data": "event_data"})
    
    async def _broadcast_event(self, event: Dict):
        """Broadcast event to WebSocket subscribers"""
        contract_topic = f"contract:{event['contract_address']}"
        chain_topic = f"chain:{event['chain']}"
        event_topic = f"event:{event['event_type']}"
        
        # Get all subscribers for relevant topics
        subscribers = set()
        subscribers.update(subscription_topics.get(contract_topic, set()))
        subscribers.update(subscription_topics.get(chain_topic, set()))
        subscribers.update(subscription_topics.get(event_topic, set()))
        subscribers.update(subscription_topics.get("all", set()))
        
        # Broadcast to subscribers
        for websocket in subscribers:
            try:
                await websocket.send_json(event)
            except:
                # Remove dead connections
                active_connections.discard(websocket)

# Initialize indexer
indexer = EventIndexer()

@app.post("/index/start")
async def start_indexing(request: IndexRequest):
    """
    Start indexing events for a contract
    
    Begins real-time event streaming and optional historical backfill
    """
    result = await indexer.start_indexing(request)
    return result

@app.post("/index/stop")
async def stop_indexing(contract_address: str, chain: Chain):
    """Stop indexing a contract"""
    contract_key = f"{chain.value}:{contract_address}"
    
    if contract_key not in indexer.indexed_contracts:
        raise HTTPException(404, "Contract not being indexed")
    
    del indexer.indexed_contracts[contract_key]
    
    return {
        "status": "stopped",
        "contract": contract_address,
        "chain": chain.value
    }

@app.get("/index/status")
async def get_indexing_status():
    """Get status of all indexed contracts"""
    return {
        "indexed_contracts": list(indexer.indexed_contracts.values()),
        "total": len(indexer.indexed_contracts),
        "total_events": len(indexed_events)
    }

@app.post("/query")
async def query_events(request: QueryRequest):
    """
    Query indexed events with filtering
    
    Supports filtering by contract, chain, event type, and block range
    """
    events = indexed_events
    
    # Filter by contract
    if request.contract_address:
        events = [e for e in events if e["contract_address"] == request.contract_address]
    
    # Filter by chain
    if request.chain:
        events = [e for e in events if e["chain"] == request.chain.value]
    
    # Filter by event type
    if request.event_type:
        events = [e for e in events if e["event_type"] == request.event_type.value]
    
    # Filter by block range
    if request.from_block:
        events = [e for e in events if e["block_number"] >= request.from_block]
    
    if request.to_block:
        events = [e for e in events if e["block_number"] <= request.to_block]
    
    # Apply limit
    events = events[-request.limit:]
    
    return {
        "events": events,
        "total": len(events),
        "has_more": len(indexed_events) > request.limit
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming
    
    Clients can subscribe to topics:
    - "all" - all events
    - "contract:<address>" - events from specific contract
    - "chain:<chain>" - events from specific chain
    - "event:<type>" - specific event types
    """
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        while True:
            # Receive subscription commands
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "subscribe":
                topic = data.get("topic", "all")
                subscription_topics[topic].add(websocket)
                await websocket.send_json({
                    "type": "subscribed",
                    "topic": topic
                })
            
            elif command == "unsubscribe":
                topic = data.get("topic")
                if topic in subscription_topics:
                    subscription_topics[topic].discard(websocket)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "topic": topic
                })
    
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        # Remove from all subscriptions
        for topic_subs in subscription_topics.values():
            topic_subs.discard(websocket)

@app.get("/stats")
async def get_stats():
    """Get indexer statistics"""
    events_by_chain = defaultdict(int)
    events_by_type = defaultdict(int)
    
    for event in indexed_events:
        events_by_chain[event["chain"]] += 1
        events_by_type[event["event_type"]] += 1
    
    return {
        "total_events": len(indexed_events),
        "indexed_contracts": len(indexer.indexed_contracts),
        "active_websockets": len(active_connections),
        "events_by_chain": dict(events_by_chain),
        "events_by_type": dict(events_by_type),
        "current_blocks": {
            chain.value: block
            for chain, block in indexer.current_blocks.items()
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "streaming-indexer",
        "version": "1.0.0",
        "indexed_events": len(indexed_events),
        "active_contracts": len(indexer.indexed_contracts),
        "websocket_connections": len(active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)
