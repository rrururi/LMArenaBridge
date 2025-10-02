"""
Request Queue System for LMArena Bridge

Handles request queuing, timeout management, and worker assignment
for cloud deployment architecture.
"""

import asyncio
import logging
import time
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QueuedRequest:
    """Represents a queued API request waiting for worker assignment."""
    request_id: str
    payload: dict
    model_name: str
    created_at: float
    timeout_seconds: int
    response_queue: asyncio.Queue
    assigned_worker_id: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if request has exceeded its timeout."""
        elapsed = time.time() - self.created_at
        return elapsed > self.timeout_seconds
    
    @property
    def wait_time(self) -> float:
        """Get current wait time in seconds."""
        return time.time() - self.created_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/debugging."""
        return {
            "request_id": self.request_id,
            "model_name": self.model_name,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "wait_time": round(self.wait_time, 2),
            "timeout_seconds": self.timeout_seconds,
            "assigned_worker_id": self.assigned_worker_id,
            "is_expired": self.is_expired
        }


class RequestQueue:
    """
    Manages in-memory request queue for worker assignment.
    
    This implementation does NOT queue requests when no workers are available.
    Instead, it immediately rejects requests (503 error) if no idle worker exists.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self._requests: Dict[str, QueuedRequest] = {}
        self._lock = asyncio.Lock()
        
        # Configuration
        queue_settings = config.get("queue_settings", {})
        self._max_wait_seconds = queue_settings.get("max_wait_seconds", 60)
        self._reject_when_no_workers = queue_settings.get("reject_when_no_workers", True)
        
        # Statistics
        self._total_requests = 0
        self._total_timeouts = 0
        self._total_completed = 0
        
        logger.info(
            f"RequestQueue initialized. "
            f"Max wait: {self._max_wait_seconds}s, "
            f"Reject when no workers: {self._reject_when_no_workers}"
        )
    
    async def add_request(
        self,
        request_id: str,
        payload: dict,
        model_name: str,
        response_queue: asyncio.Queue,
        timeout_seconds: Optional[int] = None
    ) -> QueuedRequest:
        """
        Add a new request to tracking system.
        
        Note: This doesn't actually queue the request for later processing.
        It's used for tracking active requests assigned to workers.
        
        Args:
            request_id: Unique request identifier
            payload: Request payload to send to worker
            model_name: Model name for this request
            response_queue: Queue for receiving worker responses
            timeout_seconds: Custom timeout, defaults to config value
        
        Returns:
            QueuedRequest: The created request object
        """
        async with self._lock:
            if timeout_seconds is None:
                timeout_seconds = self._max_wait_seconds
            
            queued_request = QueuedRequest(
                request_id=request_id,
                payload=payload,
                model_name=model_name,
                created_at=time.time(),
                timeout_seconds=timeout_seconds,
                response_queue=response_queue
            )
            
            self._requests[request_id] = queued_request
            self._total_requests += 1
            
            logger.info(
                f"REQUEST TRACK: Request '{request_id[:8]}' added to tracking. "
                f"Total active: {len(self._requests)}"
            )
            
            return queued_request
    
    async def assign_to_worker(self, request_id: str, worker_id: str) -> bool:
        """
        Assign a request to a specific worker.
        
        Args:
            request_id: Request identifier
            worker_id: Worker identifier
        
        Returns:
            bool: True if successful, False if request not found
        """
        async with self._lock:
            if request_id not in self._requests:
                logger.error(f"REQUEST ASSIGN: Request '{request_id[:8]}' not found")
                return False
            
            self._requests[request_id].assigned_worker_id = worker_id
            logger.info(
                f"REQUEST ASSIGN: Request '{request_id[:8]}' assigned to worker '{worker_id}'"
            )
            return True
    
    async def get_request(self, request_id: str) -> Optional[QueuedRequest]:
        """Get a specific request by ID."""
        async with self._lock:
            return self._requests.get(request_id)
    
    async def remove_request(self, request_id: str, completed: bool = True, timeout: bool = False) -> bool:
        """
        Remove a request from tracking.
        
        Args:
            request_id: Request identifier
            completed: Whether request completed successfully
            timeout: Whether request timed out
        
        Returns:
            bool: True if removed, False if not found
        """
        async with self._lock:
            if request_id not in self._requests:
                logger.warning(f"REQUEST REMOVE: Request '{request_id[:8]}' not found")
                return False
            
            request = self._requests[request_id]
            del self._requests[request_id]
            
            # Update statistics
            if timeout:
                self._total_timeouts += 1
                logger.warning(
                    f"REQUEST TIMEOUT: Request '{request_id[:8]}' timed out after "
                    f"{request.wait_time:.2f}s"
                )
            elif completed:
                self._total_completed += 1
                logger.info(
                    f"REQUEST COMPLETE: Request '{request_id[:8]}' completed in "
                    f"{request.wait_time:.2f}s by worker '{request.assigned_worker_id}'"
                )
            else:
                logger.info(f"REQUEST REMOVE: Request '{request_id[:8]}' removed")
            
            return True
    
    async def cleanup_expired_requests(self) -> int:
        """
        Remove requests that have exceeded their timeout.
        
        Returns:
            int: Number of requests cleaned up
        """
        async with self._lock:
            expired_ids = [
                req_id for req_id, req in self._requests.items()
                if req.is_expired
            ]
            
            for req_id in expired_ids:
                request = self._requests[req_id]
                
                # Send timeout error to response queue
                try:
                    await request.response_queue.put({
                        "error": f"Request timed out after {request.timeout_seconds} seconds"
                    })
                    await request.response_queue.put("[DONE]")
                except Exception as e:
                    logger.error(f"Error sending timeout to response queue: {e}")
                
                # Remove from tracking
                await self.remove_request(req_id, completed=False, timeout=True)
            
            if expired_ids:
                logger.info(f"CLEANUP: Removed {len(expired_ids)} expired request(s)")
            
            return len(expired_ids)
    
    async def get_active_requests(self) -> list[dict]:
        """Get list of all active requests."""
        async with self._lock:
            return [req.to_dict() for req in self._requests.values()]
    
    async def get_stats(self) -> dict:
        """Get queue statistics."""
        async with self._lock:
            active_requests = len(self._requests)
            
            # Calculate average wait time for active requests
            avg_wait = 0.0
            if active_requests > 0:
                total_wait = sum(req.wait_time for req in self._requests.values())
                avg_wait = total_wait / active_requests
            
            return {
                "active_requests": active_requests,
                "total_requests": self._total_requests,
                "total_completed": self._total_completed,
                "total_timeouts": self._total_timeouts,
                "avg_wait_time": round(avg_wait, 2),
                "max_wait_seconds": self._max_wait_seconds,
                "reject_when_no_workers": self._reject_when_no_workers
            }
    
    async def clear_all(self):
        """Clear all requests (used for shutdown)."""
        async with self._lock:
            # Send error to all pending requests
            for request in self._requests.values():
                try:
                    await request.response_queue.put({
                        "error": "Server is shutting down"
                    })
                    await request.response_queue.put("[DONE]")
                except Exception as e:
                    logger.error(f"Error sending shutdown error: {e}")
            
            count = len(self._requests)
            self._requests.clear()
            
            if count > 0:
                logger.info(f"CLEAR: Cleared {count} pending request(s)")
