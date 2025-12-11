import asyncio
from typing import ClassVar, Dict, Type, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time

# --- 1. Data Structure (Typed and Immutable-like) ---

@dataclass(frozen=False) # frozen=False allows mutation within the pipeline
class DataPacket:
    """A structured, typed data packet that travels through the pipeline."""
    
    # Required initial fields
    data_id: int
    raw_data: str
    
    # Internal state/history fields
    current_payload: str = field(default="")
    status: str = field(default="PENDING")
    history: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def log_step(self, processor_name: str, result: str):
        """Helper to log the action taken by a processor."""
        self.history.append(f"[{processor_name}] -> {result}")

    def fail(self, processor_name: str, error_msg: str):
        """Helper to mark the packet as failed."""
        self.status = "FAILED"
        self.errors.append(f"[{processor_name}] ERROR: {error_msg}")


# --- 2. Refined Metaclass for Ordered Self-Registration ---

class PipelineMeta(type):
    """
    Metaclass that automatically registers all concrete Processor subclasses
    and stores them with a defined execution order (using the 'order' attribute).
    """
    # Registered processors, keyed by their defined order number
    _processors: ClassVar[Dict[int, Type['AbstractProcessor']]] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Only register concrete subclasses of AbstractProcessor
        if any(base.__name__ == 'AbstractProcessor' for base in bases) and \
           not namespace.get('__abstractmethods__'):
            
            order = namespace.get('order')
            if not isinstance(order, int):
                raise TypeError(f"Processor {name} must define an integer 'order' class attribute.")
            
            if order in PipelineMeta._processors:
                 raise ValueError(f"Order '{order}' already registered by {PipelineMeta._processors[order].__name__}. Order must be unique.")
                 
            PipelineMeta._processors[order] = cls
            print(f"💡 Registered Processor: {name} (Order: {order})")
                
        return cls

    @staticmethod
    def get_ordered_processors() -> List[Type['AbstractProcessor']]:
        """Returns the list of concrete processor classes sorted by their 'order'."""
        # This dynamic sorting ensures the pipeline always runs in the correct sequence
        return [PipelineMeta._processors[k] for k in sorted(PipelineMeta._processors.keys())]

# --- 3. Abstract Processor with Strict Contract ---

class AbstractProcessor(ABC, metaclass=PipelineMeta):
    """
    Base class for all pipeline processors. Enforces the contract:
    - Must have an integer 'order' attribute.
    - Must implement the asynchronous 'process' method.
    """
    order: ClassVar[int] = 0 # Must be overridden by subclasses
    
    @abstractmethod
    async def process(self, packet: DataPacket) -> DataPacket:
        """
        The main asynchronous processing logic. 
        Takes a DataPacket and returns the (potentially modified) DataPacket.
        """
        raise NotImplementedError

# --- 4. Concrete Processor Implementations (Self-Registering and Ordered) ---

class ValidatorProcessor(AbstractProcessor):
    order = 10

    async def process(self, packet: DataPacket) -> DataPacket:
        await asyncio.sleep(0.1) # Simulate quick validation check
        
        if "ERROR" in packet.raw_data:
            packet.fail(self.__class__.__name__, "Contains forbidden 'ERROR' string.")
            packet.current_payload = "Validation failed, stopping further processing."
        else:
            packet.current_payload = packet.raw_data.replace("raw data", "validated data")
            packet.log_step(self.__class__.__name__, "Data validated and cleaned.")
            
        return packet

class TransformationProcessor(AbstractProcessor):
    order = 20

    async def process(self, packet: DataPacket) -> DataPacket:
        if packet.status == "FAILED":
            return packet # Skip if failed in previous step
            
        await asyncio.sleep(0.3) # Simulate a heavier transformation
        
        transformed = packet.current_payload.upper() + f" --TRANSFORMED--ID:{packet.data_id}"
        packet.current_payload = transformed
        packet.log_step(self.__class__.__name__, "Payload transformed to uppercase.")
        
        return packet

class PersistenceProcessor(AbstractProcessor):
    order = 30

    async def process(self, packet: DataPacket) -> DataPacket:
        if packet.status == "FAILED":
            return packet # Skip if failed
            
        await asyncio.sleep(0.5) # Simulate database I/O
        
        # In a real system, you'd write packet.current_payload to a database
        print(f"💾 Persistence: Wrote ID {packet.data_id} successfully.")
        
        packet.status = "COMPLETED"
        packet.log_step(self.__class__.__name__, "Result persisted to storage.")
        
        return packet


# --- 5. The Pipeline Runner Class ---

class Pipeline:
    """
    Encapsulates the execution logic for running a DataPacket through 
    the ordered, self-registered processor chain.
    """
    
    def __init__(self):
        self._processors = PipelineMeta.get_ordered_processors()
        print(f"\n✨ Pipeline Initialized with {len(self._processors)} steps.")

    async def run(self, packet: DataPacket) -> DataPacket:
        """
        Executes the processor chain sequentially, passing the DataPacket
        from one step's output to the next step's input.
        """
        current_packet = packet
        
        print(f"--- Starting DataPacket ID {current_packet.data_id} ---")

        for ProcessorClass in self._processors:
            # Check if the packet has failed and stop chaining
            if current_packet.status == "FAILED":
                print(f"🚨 Stopping chain for ID {current_packet.data_id} after {ProcessorClass.__name__}")
                break
            
            processor_instance = ProcessorClass() # Create instance per run (or use a pool/singleton)
            
            # The key improvement: input is the previous output
            current_packet = await processor_instance.process(current_packet)
            
        print(f"--- Finished DataPacket ID {current_packet.data_id} ({current_packet.status}) ---\n")
        return current_packet

# --- 6. Main Execution Loop ---

async def main():
    
    # 1. Prepare raw data
    raw_data = [
        ("payload A", 101),
        ("payload B", 102),
        ("payload ERROR C", 103), # The intentionally failing packet
        ("payload D", 104),
    ]
    
    # 2. Create DataPackets
    data_packets = [DataPacket(data_id=d_id, raw_data=d) for d, d_id in raw_data]
    
    # 3. Initialize Pipeline (which automatically gets the processor list)
    pipeline = Pipeline()
    
    start_time = time.time()
    
    # 4. Create tasks to run multiple packets concurrently
    tasks = [pipeline.run(p) for p in data_packets]
    
    # Run all pipelines concurrently (asyncio.gather is the true concurrency tool)
    finished_packets = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    # 5. Review Results
    print("\n\n=============== FINAL REPORT ===============")
    for packet in finished_packets:
        print(f"ID {packet.data_id} | Status: {packet.status}")
        if packet.errors:
            print(f"  Errors: {packet.errors}")
        if packet.status == "COMPLETED":
            print(f"  Final Payload (first 30 chars): {packet.current_payload[:30]}...")
        print(f"  History: {packet.history}")
        print("---------------------------------------------")

    print(f"\n--- Total execution time: {end_time - start_time:.2f} seconds ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted.")