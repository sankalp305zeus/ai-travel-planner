import os
import base64
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry import baggage

class BaggageSpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context=None):
        for key, value in baggage.get_all(context=parent_context).items():
            span.set_attribute(key, value)

def setup_telemetry():
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
    
    if not public_key or not secret_key:
        print("Warning: Langfuse keys missing, telemetry not configured fully.")
        
    auth_str = f"{public_key}:{secret_key}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    resource = Resource.create({"service.name": "ai-travel-planner"})
    provider = TracerProvider(resource=resource)
    
    endpoint = base_url.rstrip("/") + "/api/public/otel/v1/traces" # or "/api/public/otel", langfuse standard is /v1/traces usually appended by OTEL. We explicitly pass it to the exporter if not.
    if "/api/public/otel" not in endpoint:
        pass
    # The prompt explicitly asked for OTLP exporter endpoint: LANGFUSE_BASE_URL + "/api/public/otel"
    # Wait, the prompt says: LANGFUSE_BASE_URL + "/api/public/otel"
    # OTLPSpanExporter automatically appends `/v1/traces` if we don't.
    endpoint = base_url.rstrip("/") + "/api/public/otel/v1/traces"

    exporter = OTLPSpanExporter(
        endpoint=endpoint,
        headers={"Authorization": f"Basic {b64_auth}"}
    )
    
    provider.add_span_processor(BatchSpanProcessor(exporter))
    provider.add_span_processor(BaggageSpanProcessor())
    
    trace.set_tracer_provider(provider)
    
    # We don't need to instrument fastapi or langgraph explicitly here if we just do custom spans and PydanticAI
    # If PydanticAI is used, pydantic_ai natively uses the global tracer provider.
    import pydantic_ai
    
    # Setup PydanticAI OTEL
    # PydanticAI automatically instruments if OTEL is present in environment, or we can just let it be.
