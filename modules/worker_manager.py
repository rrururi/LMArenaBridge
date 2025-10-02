"""
Worker Management System for LMArena Bridge Cloud Deployment

This module handles worker registration, authentication, status tracking,
and load balancing for distributed worker architecture.
"""

import logging
import time
import threading
import os
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Worker:
    """Represents a connected worker instance."""
    worker_id: str
    auth_token: str
    websocket: object  # WebSocket connection
    status: str = "idle"  # idle, busy, offline
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    current_request_id: Optional[str] = None
    requests_processed: int = 0
    total_processing_time: float = 0.0
    last_error: Optional[str] = None
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time for this worker."""
        if self.requests_processed == 0:
            return 0.0
        return self.total_processing_time / self.requests_processed
    
    @property
    def is_healthy(self) -> bool:
        """Check if worker is responding to heartbeats."""
        time_since_heartbeat = time.time() - self.last_heartbeat
        return time_since_heartbeat < 120  # 2 minutes timeout
    
    def to_dict(self) -> dict:
        """Convert worker to dictionary for JSON serialization."""
        return {
            "worker_id": self.worker_id,
            "status": self.status,
            "connected_at": datetime.fromtimestamp(self.connected_at).isoformat(),
            "last_heartbeat": datetime.fromtimestamp(self.last_heartbeat).isoformat(),
            "current_request_id": self.current_request_id,
            "requests_processed": self.requests_processed,
            "avg_response_time": round(self.avg_response_time, 2),
            "is_healthy": self.is_healthy,
            "last_error": self.last_error
        }


class WorkerManager:
    """
    Manages worker pool, handles registration, authentication,
    load balancing, and health monitoring.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.workers: Dict[str, Worker] = {}
        self._lock = threading.RLock()
        self._valid_tokens = self._load_valid_tokens()
        self._max_workers = config.get("worker_settings", {}).get("max_workers", 10)
        self._heartbeat_timeout = config.get("worker_settings", {}).get("worker_timeout_seconds", 120)
        
        logger.info(f"WorkerManager initialized. Max workers: {self._max_workers}")
    
    def _load_valid_tokens(self) -> set:
        """
        Load valid worker authentication tokens.
        Priority: Environment variable > Config file
        
        Environment variable format: WORKER_TOKENS="token1,token2,token3"
        """
        # Try to load from environment variable first
        env_tokens = os.getenv("WORKER_TOKENS", "").strip()
        if env_tokens:
            tokens = [t.strip() for t in env_tokens.split(",") if t.strip()]
            logger.info(f"Loaded {len(tokens)} worker token(s) from WORKER_TOKENS environment variable")
            return set(tokens)
        
        # Fallback to config file
        worker_settings = self.config.get("worker_settings", {})
        tokens = worker_settings.get("valid_tokens", [])
        
        if not tokens:
            logger.warning("No valid worker tokens configured. Set WORKER_TOKENS environment variable or add tokens to config.jsonc")
        else:
            logger.info(f"Loaded {len(tokens)} worker token(s) from config file")
        
        return set(tokens)
    
    def authenticate_worker(self, auth_token: str) -> bool:
        """Validate worker authentication token."""
        if not self.config.get("worker_settings", {}).get("require_authentication", True):
            logger.info("Worker authentication is disabled.")
            return True
        
        is_valid = auth_token in self._valid_tokens
        if not is_valid:
            logger.warning(f"Authentication failed for token: {auth_token[:10]}...")
        
        return is_valid
    
    def register_worker(self, worker_id: str, auth_token: str, websocket) -> tuple[bool, str]:
        """
        Register a new worker.
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        with self._lock:
            # Check if worker limit reached
            if len(self.workers) >= self._max_workers:
                msg = f"Maximum worker limit ({self._max_workers}) reached"
                logger.warning(f"WORKER REGISTER: {msg}")
                return False, msg
            
            # Check if worker ID already exists
            if worker_id in self.workers:
                msg = f"Worker ID '{worker_id}' is already registered"
                logger.warning(f"WORKER REGISTER: {msg}")
                return False, msg
            
            # Authenticate worker
            if not self.authenticate_worker(auth_token):
                msg = "Invalid authentication token"
                logger.warning(f"WORKER REGISTER: {msg} for worker '{worker_id}'")
                return False, msg
            
            # Create and register worker
            worker = Worker(
                worker_id=worker_id,
                auth_token=auth_token,
                websocket=websocket
            )
            self.workers[worker_id] = worker
            
            logger.info(f"✅ WORKER REGISTER: Worker '{worker_id}' registered successfully. Total workers: {len(self.workers)}")
            return True, "Worker registered successfully"
    
    def unregister_worker(self, worker_id: str) -> bool:
        """
        Unregister a worker.
        
        Returns:
            bool: True if worker was unregistered, False if not found
        """
        with self._lock:
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                # If worker was processing a request, log it
                if worker.current_request_id:
                    logger.warning(
                        f"WORKER UNREGISTER: Worker '{worker_id}' disconnected while processing request '{worker.current_request_id[:8]}'"
                    )
                
                del self.workers[worker_id]
                logger.info(f"❌ WORKER UNREGISTER: Worker '{worker_id}' removed. Remaining workers: {len(self.workers)}")
                return True
            
            logger.warning(f"WORKER UNREGISTER: Worker '{worker_id}' not found")
            return False
    
    def get_available_worker(self) -> Optional[Worker]:
        """
        Get an available (idle and healthy) worker for request assignment.
        Uses least-loaded strategy for load balancing.
        
        Returns:
            Optional[Worker]: Available worker or None if no workers available
        """
        with self._lock:
            available_workers = [
                w for w in self.workers.values()
                if w.status == "idle" and w.is_healthy
            ]
            
            if not available_workers:
                logger.warning("GET WORKER: No available workers found")
                return None
            
            # Select worker with least average response time (least loaded)
            selected_worker = min(available_workers, key=lambda w: w.avg_response_time)
            logger.info(
                f"GET WORKER: Selected worker '{selected_worker.worker_id}' "
                f"(processed: {selected_worker.requests_processed}, "
                f"avg time: {selected_worker.avg_response_time:.2f}s)"
            )
            return selected_worker
    
    def mark_worker_busy(self, worker_id: str, request_id: str) -> bool:
        """
        Mark a worker as busy with a specific request.
        
        Returns:
            bool: True if successful, False if worker not found
        """
        with self._lock:
            if worker_id not in self.workers:
                logger.error(f"MARK BUSY: Worker '{worker_id}' not found")
                return False
            
            worker = self.workers[worker_id]
            worker.status = "busy"
            worker.current_request_id = request_id
            logger.info(f"MARK BUSY: Worker '{worker_id}' now processing request '{request_id[:8]}'")
            return True
    
    def mark_worker_idle(self, worker_id: str, processing_time: float = 0.0, error: Optional[str] = None) -> bool:
        """
        Mark a worker as idle after completing a request.
        
        Args:
            worker_id: Worker identifier
            processing_time: Time taken to process the request in seconds
            error: Error message if request failed
        
        Returns:
            bool: True if successful, False if worker not found
        """
        with self._lock:
            if worker_id not in self.workers:
                logger.error(f"MARK IDLE: Worker '{worker_id}' not found")
                return False
            
            worker = self.workers[worker_id]
            worker.status = "idle"
            worker.requests_processed += 1
            worker.total_processing_time += processing_time
            worker.current_request_id = None
            worker.last_error = error
            
            status_msg = "completed" if not error else f"failed: {error}"
            logger.info(
                f"MARK IDLE: Worker '{worker_id}' {status_msg}. "
                f"Total processed: {worker.requests_processed}"
            )
            return True
    
    def update_heartbeat(self, worker_id: str) -> bool:
        """
        Update worker's last heartbeat timestamp.
        
        Returns:
            bool: True if successful, False if worker not found
        """
        with self._lock:
            if worker_id not in self.workers:
                return False
            
            self.workers[worker_id].last_heartbeat = time.time()
            return True
    
    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """Get a specific worker by ID."""
        with self._lock:
            return self.workers.get(worker_id)
    
    def get_all_workers(self) -> List[Worker]:
        """Get list of all registered workers."""
        with self._lock:
            return list(self.workers.values())
    
    def get_worker_count(self) -> Dict[str, int]:
        """Get count of workers by status."""
        with self._lock:
            total = len(self.workers)
            idle = sum(1 for w in self.workers.values() if w.status == "idle" and w.is_healthy)
            busy = sum(1 for w in self.workers.values() if w.status == "busy")
            unhealthy = sum(1 for w in self.workers.values() if not w.is_healthy)
            
            return {
                "total": total,
                "idle": idle,
                "busy": busy,
                "unhealthy": unhealthy
            }
    
    def cleanup_unhealthy_workers(self) -> int:
        """
        Remove workers that haven't sent heartbeat within timeout period.
        
        Returns:
            int: Number of workers removed
        """
        with self._lock:
            unhealthy_workers = [
                worker_id for worker_id, worker in self.workers.items()
                if not worker.is_healthy
            ]
            
            for worker_id in unhealthy_workers:
                logger.warning(f"CLEANUP: Removing unhealthy worker '{worker_id}'")
                self.unregister_worker(worker_id)
            
            if unhealthy_workers:
                logger.info(f"CLEANUP: Removed {len(unhealthy_workers)} unhealthy worker(s)")
            
            return len(unhealthy_workers)
    
    def get_stats(self) -> dict:
        """Get overall worker pool statistics."""
        with self._lock:
            workers_list = list(self.workers.values())
            
            if not workers_list:
                return {
                    "total_workers": 0,
                    "idle_workers": 0,
                    "busy_workers": 0,
                    "unhealthy_workers": 0,
                    "total_requests_processed": 0,
                    "avg_response_time": 0.0
                }
            
            total_requests = sum(w.requests_processed for w in workers_list)
            avg_response_time = (
                sum(w.avg_response_time * w.requests_processed for w in workers_list) / total_requests
                if total_requests > 0 else 0.0
            )
            
            return {
                "total_workers": len(workers_list),
                "idle_workers": sum(1 for w in workers_list if w.status == "idle" and w.is_healthy),
                "busy_workers": sum(1 for w in workers_list if w.status == "busy"),
                "unhealthy_workers": sum(1 for w in workers_list if not w.is_healthy),
                "total_requests_processed": total_requests,
                "avg_response_time": round(avg_response_time, 2),
                "max_workers": self._max_workers
            }
