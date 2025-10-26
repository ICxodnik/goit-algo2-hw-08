"""
Task 2. Rate Limiter (Sliding Window) for chat
Run:
    python task2_rate_limiter.py
"""
from __future__ import annotations
import random
from typing import Dict
import time
from collections import deque

class SlidingWindowRateLimiter:
    def __init__(self, window_size: int = 10, max_requests: int = 1):
        self.window_size = float(window_size)
        self.max_requests = int(max_requests)
        # History: user_id -> deque[timestamps]
        self.history: Dict[str, deque] = {}

    def _cleanup_window(self, user_id: str, current_time: float) -> None:
        """Clean everything that fell outside the window [current_time - window_size, current_time]."""
        dq = self.history.get(user_id)
        if dq is None:
            return
        # remove outdated timestamps
        window_start = current_time - self.window_size
        while dq and dq[0] <= window_start:
            dq.popleft()
        # if user has no events — remove record to save memory
        if not dq:
            self.history.pop(user_id, None)

    def can_send_message(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup_window(user_id, now)
        dq = self.history.get(user_id)
        if dq is None:
            return True  # first message is always allowed
        return len(dq) < self.max_requests

    def record_message(self, user_id: str) -> bool:
        """Record message if allowed. Return True/False."""
        now = time.time()
        self._cleanup_window(user_id, now)
        dq = self.history.get(user_id)
        if dq is None:
            dq = deque()
            self.history[user_id] = dq
        if len(dq) < self.max_requests:
            dq.append(now)
            return True
        # Limit exceeded
        return False

    def time_until_next_allowed(self, user_id: str) -> float:
        now = time.time()
        self._cleanup_window(user_id, now)
        dq = self.history.get(user_id)
        if dq is None or len(dq) < self.max_requests:
            return 0.0
        # when "space will be freed" — when oldest event leaves the window
        wait = (dq[0] + self.window_size) - now
        return max(0.0, wait)

# Demonstration of work
def test_rate_limiter():
    # Create rate limiter: window 10 seconds, 1 message
    limiter = SlidingWindowRateLimiter(window_size=10, max_requests=1)

    # Simulate message flow from users (sequential IDs from 1 to 20)
    print("\n=== Симуляція потоку повідомлень ===")
    for message_id in range(1, 11):
        # Simulate different users (IDs from 1 to 5)
        user_id = message_id % 5 + 1

        result = limiter.record_message(str(user_id))
        wait_time = limiter.time_until_next_allowed(str(user_id))

        print(f"Message {message_id:2d} | User {user_id} | "
              f"{'✓' if result else f'× (waiting {wait_time:.1f}s)'}")

        # Random delay between messages for realism
        # Random delay from 0.1 to 1 second
        time.sleep(random.uniform(0.1, 1.0))

    # Wait until window clears
    print("\nWaiting 4 seconds...")
    time.sleep(4)

    print("\n=== New series of messages after waiting ===")
    for message_id in range(11, 21):
        user_id = message_id % 5 + 1
        result = limiter.record_message(str(user_id))
        wait_time = limiter.time_until_next_allowed(str(user_id))
        print(f"Message {message_id:2d} | User {user_id} | "
              f"{'✓' if result else f'× (waiting {wait_time:.1f}s)'}")
        # Random delay from 0.1 to 1 second
        time.sleep(random.uniform(0.1, 1.0))

if __name__ == "__main__":
    test_rate_limiter()