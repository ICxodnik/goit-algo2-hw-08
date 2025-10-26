"""
Task 1. Data access optimization using LRU cache

Run:
    python task1_lru_cache.py --n 100000 --q 50000 --seed 42 --capacity 1000
"""
from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from typing import List, Tuple
import random
import time
import argparse
import copy

# ---------------------------
# Data preparation and cache
# ---------------------------

def make_queries(n: int, q: int, hot_pool: int = 30, p_hot: float = 0.95, p_update: float = 0.03):
    hot = [(random.randint(0, n//2), random.randint(n//2, n-1))
           for _ in range(hot_pool)]
    queries = []
    for _ in range(q):
        if random.random() < p_update:        # ~3% requests — Update
            idx = random.randint(0, n-1)
            val = random.randint(1, 100)
            queries.append(("Update", idx, val))
        else:                                 # ~97% — Range
            if random.random() < p_hot:       # 95% — "hot" ranges
                left, right = random.choice(hot)
            else:                             # 5% — random ranges
                left = random.randint(0, n-1)
                right = random.randint(left, n-1)
            queries.append(("Range", left, right))
    return queries

class LRUCache:
    """Simple LRU cache based on OrderedDict with get/put interface."""
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self._data: "OrderedDict[Tuple[int,int], int]" = OrderedDict()

    def get(self, key: Tuple[int,int]) -> int:
        if key not in self._data:
            return -1
        val = self._data.pop(key)
        self._data[key] = val  # move to end (most recent)
        return val

    def put(self, key: Tuple[int,int], value: int) -> None:
        if key in self._data:
            self._data.pop(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)  # remove oldest

    def keys(self):
        return list(self._data.keys())

    def __len__(self):
        return len(self._data)

# ---------------------------
# Functions without cache
# ---------------------------

def range_sum_no_cache(array: List[int], left: int, right: int) -> int:
    """Returns sum without caching (naive approach)."""
    return sum(array[left:right+1])

def update_no_cache(array: List[int], index: int, value: int) -> None:
    """Updates element without caching."""
    array[index] = value

# ---------------------------
# Functions with cache
# ---------------------------

def range_sum_with_cache(array: List[int], left: int, right: int, cache: LRUCache) -> int:
    """If cache has sum for (left,right), return it.
    Otherwise — compute, put in cache and return.
    """
    key = (left, right)
    cached = cache.get(key)
    if cached != -1:
        return cached
    res = sum(array[left:right+1])
    cache.put(key, res)
    return res

def update_with_cache(array: List[int], index: int, value: int, cache: LRUCache) -> None:
    """Update array and invalidate all keys that intersect with index.
    Invalidation — linear pass through keys (no need to modify LRUCache).
    """
    array[index] = value
    # collect keys that need to be deleted
    to_delete = []
    for (l, r) in cache.keys():
        if l <= index <= r:
            to_delete.append((l, r))
    # deletion
    for k in to_delete:
        # Without direct deletion API — re-insert elements except k
        # Simpler: pop-insert all except marked ones
        pass
    # Implement careful deletion: rebuild OrderedDict without these keys
    if to_delete:
        new_data = OrderedDict((k, v) for k, v in cache._data.items() if k not in set(to_delete))
        cache._data = new_data

# ---------------------------
# Query execution and measurements
# ---------------------------

def run_sequence_no_cache(array: List[int], queries):
    for q in queries:
        if q[0] == "Range":
            _, l, r = q
            _ = range_sum_no_cache(array, l, r)
        else:
            _, idx, val = q
            update_no_cache(array, idx, val)

def run_sequence_with_cache(array: List[int], queries, capacity: int = 1000):
    cache = LRUCache(capacity=capacity)
    for q in queries:
        if q[0] == "Range":
            _, l, r = q
            _ = range_sum_with_cache(array, l, r, cache)
        else:
            _, idx, val = q
            update_with_cache(array, idx, val, cache)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100_000, help="array size")
    parser.add_argument("--q", type=int, default=50_000, help="number of queries")
    parser.add_argument("--seed", type=int, default=42, help="seed for reproducibility")
    parser.add_argument("--capacity", type=int, default=1000, help="LRU cache capacity")
    parser.add_argument("--maxval", type=int, default=100, help="max value of array elements")
    args = parser.parse_args()

    random.seed(args.seed)

    array = [random.randint(1, args.maxval) for _ in range(args.n)]
    queries = make_queries(args.n, args.q)

    arr1 = array[:]  # for "without cache"
    arr2 = array[:]  # for "with cache"

    t0 = time.perf_counter()
    run_sequence_no_cache(arr1, queries)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    run_sequence_with_cache(arr2, queries, capacity=args.capacity)
    t3 = time.perf_counter()

    no_cache_time = t1 - t0
    with_cache_time = t3 - t2
    speedup = no_cache_time / with_cache_time if with_cache_time > 0 else float("inf")

    print(f"Without cache: {no_cache_time:7.2f} s")
    print(f"LRU cache: {with_cache_time:7.2f} s  (speedup ×{speedup:.1f})")

if __name__ == "__main__":
    main()