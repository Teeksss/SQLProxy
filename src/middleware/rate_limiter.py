from flask import request
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests = 100
        self.time_window = 60
        
    def is_allowed(self, client_id: str) -> bool:
        current_time = time.time()
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < self.time_window
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
            
        self.requests[client_id].append(current_time)
        return True