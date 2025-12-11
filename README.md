
# 📚 Advanced Python Architectural Patterns

This repository contains three distinct, self-contained Python examples demonstrating modern, sophisticated architectural patterns and best practices. These examples go beyond basic scripting to illustrate techniques for building scalable, maintainable, and concurrent applications.

## 1\. `dependency_injector_app.py`

### 💡 Core Concept: Dependency Injection (DI) and Inversion of Control (IoC)

This code uses the external `dependency-injector` library to manage the instantiation and lifecycle of application services.

#### What it Does

It defines an `ExternalService` and a `DataProcessor` that depends on it. The central `Container` then **wires** these classes together, defining `ExternalService` as a **Singleton** (one shared instance) and `DataProcessor` as a **Factory** (a new instance per request).

#### How it Helps

| Benefit | Description |
| :--- | :--- |
| **Decoupling** | The `DataProcessor` doesn't know *how* to create the `ExternalService`; it just asks for it. This makes components independent. |
| **Testability** | You can easily **override** the `ExternalService` with a mock or dummy version in your tests without changing the `DataProcessor`'s code. |
| **Lifecycle Management** | The container manages complexity: ensuring the `ExternalService` is initialized only once (Singleton) and automatically passing it to all dependents. |
| **Configuration Control**| Allows environment-specific configurations (like debug vs. production API keys) to be injected centrally. |

**To Run:**

```bash
python dependency_injector_app.py
# Run in debug mode to see config override:
python dependency_injector_app.py debug
```

-----

## 2\. `distributed_lock_manager.py`

### 💡 Core Concept: Distributed Concurrency Control and External State

This code demonstrates how to safely manage access to a critical shared resource across multiple processes or machines using a common external data store (Redis).

#### What it Does

It implements a `DistributedLock` using a Python **Context Manager** (`with` statement). The lock relies on atomic Redis operations (`SETNX` with expiration) and a unique lock ID to ensure:

1.  Only one thread/process holds the lock at a time.
2.  The lock automatically expires (`EX`) if the process holding it crashes, preventing a deadlock.
3.  A **Lua Script** is used to atomically check the lock owner ID and delete it upon release, preventing race conditions.

#### How it Helps

| Benefit | Description |
| :--- | :--- |
| **Preventing Race Conditions** | Guarantees the integrity of shared resources (like the `SHARED_COUNTER`) in highly concurrent, distributed environments (e.g., multiple microservices). |
| **Resilience** | The `EX` (expire) timeout ensures that if a service fails mid-operation, the lock will be released automatically, avoiding system-wide deadlocks. |
| **Readability** | Using the Python context manager (`with DistributedLock(...)`) simplifies the complex acquire/release logic, making the critical section clear and tidy. |

**To Run (Requires Redis server):**

```bash
python distributed_lock_manager.py
```

-----

## 3\. `functional_data_stream.py`

### 💡 Core Concept: Functional Programming, Generators, and Lazy Evaluation

This code utilizes Python's functional tools to process data streams efficiently without loading the entire dataset into memory.

#### What it Does

It defines a pipeline of **pure functions** (`filter_odd`, `map_square`, `map_format`). The data source (`infinite_source`) and the pipeline execution are built using **generators** and `itertools.islice`.

A higher-order function, `apply_pipeline`, chains these transformations together. Crucially, the pipeline is **lazy**, meaning processing only occurs **item-by-item** as the final consumer (the main loop) requests data, not when the pipeline is defined.

#### How it Helps

| Benefit | Description |
| :--- | :--- |
| **Memory Efficiency** | By using generators, the entire stream (simulated as 10,000 items) is never stored in memory simultaneously. Only one data item exists at any step of the pipeline. |
| **Scalability** | You can process streams that are truly infinite or too large for your machine's RAM. |
| **Modularity & Reusability** | The transformation functions are **pure** (no side effects), making them easy to test, swap, and reuse in different pipelines. |
| **Performance** | Only the necessary work is done. If the consumer stops early, the rest of the stream is never processed. |

**To Run:**

```bash
python functional_data_stream.py
```