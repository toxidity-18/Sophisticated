# distributed_lock_manager.py

import redis
import time
import uuid
import threading
import concurrent.futures

# --- Configuration ---
# Ensure a Redis server is running locally on the default port (6379)
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
LOCK_TIMEOUT_SECONDS = 5 # Maximum time a lock can be held
LOCK_KEY = "global_resource_lock"

# --- 1. The Distributed Lock Context Manager ---

class DistributedLock:
    """
    A context manager for acquiring and releasing a distributed lock 
    using Redis's SETNX command and unique value for safety.
    """
    def __init__(self, key: str, timeout: int = LOCK_TIMEOUT_SECONDS):
        self.key = key
        self.timeout = timeout
        self.lock_id = str(uuid.uuid4()) # Unique identifier for the lock owner
        self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.acquired = False

    def __enter__(self):
        """Acquire the lock (blocking wait)."""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout * 2: # Max wait time is double the lock timeout
            # Try to acquire the lock: 
            # NX: Only set if the key does NOT EXIST
            # EX: Set an expiration time (for safety against crashes)
            # This is an atomic operation (SET ... NX EX)
            if self.client.set(self.key, self.lock_id, ex=self.timeout, nx=True):
                self.acquired = True
                print(f"✅ Thread {threading.get_ident()} ACQUIRED lock: {self.lock_id}")
                return self
            
            # Lock is held by someone else, wait a bit
            time.sleep(0.1) 

        raise TimeoutError(f"❌ Failed to acquire lock {self.key} after blocking wait.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock (only if we own it)."""
        if self.acquired:
            # Use a Lua script for atomic check-and-delete:
            # This prevents a race condition where the lock could expire, 
            # be acquired by another thread, and then deleted by THIS thread.
            
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            # Execute the script atomically
            result = self.client.eval(lua_script, 1, self.key, self.lock_id)
            
            if result:
                print(f"🗑️ Thread {threading.get_ident()} RELEASED lock: {self.lock_id}")
            else:
                # This usually means the lock expired before we could release it
                print(f"⚠️ Thread {threading.get_ident()} failed to release lock; it may have expired.")
        
        self.acquired = False

# --- 2. Simulated Resource Access ---

# A shared, critical resource (e.g., a database counter)
SHARED_COUNTER = 0

def critical_section_worker(worker_id: int):
    """
    Function representing a concurrent task that needs access to 
    the globally shared resource.
    """
    global SHARED_COUNTER
    
    print(f"Attempting to run worker {worker_id}...")
    
    try:
        # Use the distributed lock context manager
        with DistributedLock(LOCK_KEY):
            # --- START CRITICAL SECTION ---
            # Operations here are guaranteed to be atomic across all processes
            print(f"⚙️ Worker {worker_id} INSIDE CRITICAL SECTION. Counter: {SHARED_COUNTER}")
            
            # Simulate work being done for 1 second
            time.sleep(1) 
            
            SHARED_COUNTER += 1
            print(f"📈 Worker {worker_id} updated counter to: {SHARED_COUNTER}")
            # --- END CRITICAL SECTION ---

    except TimeoutError as e:
        print(f"🚫 Worker {worker_id} skipped due to lock timeout.")
    except redis.exceptions.ConnectionError:
        print("FATAL: Redis connection failed. Please ensure Redis server is running.")
        return

# --- 3. Execution (Simulating Multi-threaded/Multi-process Access) ---

if __name__ == "__main__":
    
    # 1. Clean up old locks
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.delete(LOCK_KEY)
        print(f"🧹 Cleaned up old lock key: {LOCK_KEY}")
    except redis.exceptions.ConnectionError:
        print("FATAL: Cannot connect to Redis. Please start the Redis server.")
        sys.exit(1)

    NUM_WORKERS = 5
    
    print(f"\nLaunching {NUM_WORKERS} concurrent workers to access the critical section...")
    
    # Use a ThreadPoolExecutor to simulate concurrent access from different threads/processes
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Submit all workers to run concurrently
        futures = [executor.submit(critical_section_worker, i) for i in range(1, NUM_WORKERS + 1)]
        # Wait for all futures to complete
        concurrent.futures.wait(futures)

    print(f"\n--- Final SHARED_COUNTER value: {SHARED_COUNTER} (Should equal {NUM_WORKERS}) ---")
    print("If the final counter value is less than the number of workers, the lock failed.")