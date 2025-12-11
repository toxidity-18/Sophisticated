from typing import Optional
from typing import Iterable, Callable, Iterator, Any
import itertools
import time

# --- 1. Utility Functions (Higher-Order Functions) ---

def apply_pipeline(data_stream: Iterable[Any], *functions: Callable) -> Iterator[Any]:
    """
    A higher-order function that chains multiple transformation functions.
    It returns a generator, enabling lazy evaluation.
    """
    current_stream = data_stream
    for func in functions:
        # Apply the function to the current stream, creating a new generator
        current_stream = (func(item) for item in current_stream)
    return current_stream

# --- 2. Generator Functions (Lazy Data Source) ---

def infinite_source(start: int = 0) -> Iterator[int]:
    """A generator for an infinite, lazy stream of integers."""
    n = start
    while True:
        yield n
        n += 1
        
# --- 3. Transformation Functions (Pure Functions) ---

def filter_odd(x: int) -> Optional[int]:
    """Pure function: Filters out odd numbers."""
    return x if x % 2 == 0 else None

def map_square(x: int) -> int:
    """Pure function: Squares the input."""
    return x * x

def map_format(x: int) -> str:
    """Pure function: Formats the number as a string."""
    return f"<RESULT:{x:06d}>"

# --- 4. Main Execution and Lazy Pipelining ---

def run_lazy_pipeline(limit: int):
    
    # 1. Define the Source (Lazy, potentially infinite)
    source_stream = infinite_source()

    # 2. Define the Truncation (Forces the limit)
    # This is also lazy; it doesn't execute until the final 'for' loop requests an item.
    limited_stream = itertools.islice(source_stream, limit)

    # 3. Define the Processing Chain (Using the Higher-Order Function)
    # All these operations are chained without executing a single step yet.
    # The output is a generator.
    pipeline_generator = apply_pipeline(
        limited_stream,
        filter_odd,    # Removes odd numbers (returns None for them)
        lambda x: x if x is not None else -1, # Intermediate cleanup of filtered items
        map_square,    # Squares the remaining even numbers
        map_format     # Formats the final result
    )
    
    print(f"✨ Pipeline created. No data processed yet (limit={limit}).")

    # 4. Final Consumption (The loop forces the entire lazy pipeline to execute)
    processed_count = 0
    start_time = time.time()
    
    print("\n--- Starting Data Consumption (Execution) ---")
    
    for item in pipeline_generator:
        # The stream is generated and transformed item-by-item on demand
        print(f"Consumed Item: {item}")
        processed_count += 1
        # Stop early for display purposes
        if processed_count >= 10: 
            break 
            
    end_time = time.time()
    
    print("\n--- Pipeline Summary ---")
    print(f"Total items requested from source: {limit}")
    print(f"Total items consumed and displayed: {processed_count}")
    print(f"Execution time: {end_time - start_time:.4f} seconds")
    print("The pipeline only calculated the first 10 items, demonstrating lazy efficiency.")

if __name__ == "__main__":
    # Simulate processing a large stream of 10,000 items
    run_lazy_pipeline(limit=10000)