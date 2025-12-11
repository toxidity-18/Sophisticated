# dependency_injector_app.py

import sys
import dependency_injector.containers as containers
import dependency_injector.providers as providers

# --- 1. Service Definitions (Business Logic) ---

class ExternalService:
    """A simulated external resource/API connection."""
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        print(f"🔗 ExternalService initialized with {self.endpoint} and key {api_key[:5]}...")

    def fetch_data(self, record_id: int) -> dict:
        """Simulates fetching data from the external source."""
        if self.api_key == "DEBUG_KEY":
            return {"id": record_id, "status": "mocked", "source": "DEBUG"}
        return {"id": record_id, "status": "success", "source": self.endpoint}

class DataProcessor:
    """Core business logic service that depends on the ExternalService."""
    def __init__(self, external_service: ExternalService):
        self._service = external_service

    def process_record(self, record_id: int) -> str:
        data = self._service.fetch_data(record_id)
        # Sophisticated processing logic (e.g., transformation, validation)
        if data["status"] == "mocked":
            return f"Processed ID {record_id}: MOCKED DATA. Source: {data['source']}"
        return f"Processed ID {record_id}: STATUS={data['status'].upper()}. Source: {data['source']}"

# --- 2. Dependency Container (Configuration and Wiring) ---

class Container(containers.DeclarativeContainer):
    """
    Central repository for all application components.
    Defines how services are created, configured, and managed.
    """

    # Configuration provider (e.g., reading environment variables or config files)
    config = providers.Configuration(
        # Default values for local testing
        default={"api_key": "DEFAULT_SECRET_KEY", "endpoint_url": "https://prod.api.com/v1"}
    )
    
    # Singleton provider for ExternalService: only one instance is ever created
    external_service = providers.Singleton(
        ExternalService,
        api_key=config.api_key,
        endpoint=config.endpoint_url
    )

    # Factory provider for DataProcessor: a new instance is created on every request
    data_processor = providers.Factory(
        DataProcessor,
        # The dependency injection: the container automatically provides the external_service instance
        external_service=external_service
    )

# --- 3. Application Entry Point ---

def run_application(container: Container, is_debug: bool):
    """The main application function that resolves the dependencies."""
    
    print("\n--- Application Start ---")
    
    if is_debug:
        # Override configuration for a specific run (e.g., local development)
        print("🛠️ Overriding configuration for DEBUG mode...")
        container.config.api_key.override("DEBUG_KEY")
        container.config.endpoint_url.override("https://dev.api.com/v1")
    
    # Resolve the DataProcessor instance from the container. 
    # The container handles creating ExternalService first and passing it.
    processor1 = container.data_processor()
    processor2 = container.data_processor() # A new instance (Factory)

    # Note: processor1 and processor2 will share the SAME ExternalService instance (Singleton)

    print(f"Processor 1 uses ExternalService instance: {id(processor1._service)}")
    print(f"Processor 2 uses ExternalService instance: {id(processor2._service)}")
    
    # Execute logic
    result1 = processor1.process_record(1)
    result2 = processor2.process_record(99)
    
    print(result1)
    print(result2)

if __name__ == "__main__":
    # Create the container instance
    app_container = Container()
    
    # Configure configuration based on command line argument (e.g., python app.py debug)
    debug_mode = len(sys.argv) > 1 and sys.argv[1].lower() == 'debug'
    
    run_application(app_container, debug_mode)