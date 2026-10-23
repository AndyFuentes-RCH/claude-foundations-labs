"""Fábrica de proveedores y diagnóstico de su estado (LIVE / MOCK / PENDIENTE).

Regla de seguridad: un proveedor real solo se construye si hay credenciales configuradas **y**
`CFL_ALLOW_LIVE_CALLS=true`. Así ninguna ejecución genera consumo facturable por accidente.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from cfl.config import Settings
from cfl.providers.base import Mode, ModelProvider, ProviderUnavailable
from cfl.providers.messages_api import MessagesAPIProvider
from cfl.providers.mock import MockProvider

PROVIDERS = ("mock", "anthropic", "vertex", "bedrock")
PROVIDER_LABELS = {
    "mock": "Mock local (sin modelo)",
    "anthropic": "Claude API (Anthropic)",
    "vertex": "Claude en Google Cloud Vertex AI",
    "bedrock": "Claude en Amazon Bedrock",
}


@dataclass
class ProviderStatus:
    provider: str
    label: str
    model: str
    mode: Mode
    credentials_configured: bool
    live_calls_allowed: bool
    missing: list[str] = field(default_factory=list)
    details: dict[str, str | None] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    return value if value else None


def _anthropic_credentials() -> list[str]:
    if _env("ANTHROPIC_API_KEY") or _env("ANTHROPIC_AUTH_TOKEN"):
        return []
    if (Path.home() / ".config" / "anthropic").exists():  # perfil de `ant auth login`
        return []
    return ["ANTHROPIC_API_KEY (o un perfil de `ant auth login`)"]


def _vertex_credentials(settings: Settings) -> list[str]:
    missing = []
    if not settings.vertex_project_id:
        missing.append("ANTHROPIC_VERTEX_PROJECT_ID")
    adc_file = _env("GOOGLE_APPLICATION_CREDENTIALS")
    default_adc = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    if not ((adc_file and Path(adc_file).exists()) or default_adc.exists()):
        missing.append("Application Default Credentials (gcloud auth application-default login)")
    return missing


def _bedrock_credentials(settings: Settings) -> list[str]:
    missing = []
    if not settings.aws_region:
        missing.append("AWS_REGION")
    has_creds = any(
        [
            _env("AWS_ACCESS_KEY_ID") and _env("AWS_SECRET_ACCESS_KEY"),
            _env("AWS_BEARER_TOKEN_BEDROCK"),
            _env("ANTHROPIC_AWS_API_KEY"),
            settings.aws_profile and ((Path.home() / ".aws" / "config").exists() or (Path.home() / ".aws" / "credentials").exists()),
            _env("AWS_WEB_IDENTITY_TOKEN_FILE"),
            _env("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"),
        ]
    )
    if not has_creds:
        missing.append("credenciales AWS (AWS_PROFILE, claves temporales o AWS_BEARER_TOKEN_BEDROCK)")
    return missing


def provider_status(name: str, settings: Settings) -> ProviderStatus:
    name = name.lower()
    if name not in PROVIDERS:
        raise ValueError(f"Proveedor desconocido: {name}")
    if name == "mock":
        return ProviderStatus("mock", PROVIDER_LABELS["mock"], MockProvider.model, "MOCK", True, False)
    if name == "anthropic":
        missing, model, details = _anthropic_credentials(), settings.anthropic_model, {
            "server_fallbacks": str(settings.enable_server_fallbacks).lower()
        }
    elif name == "vertex":
        missing, model, details = _vertex_credentials(settings), settings.vertex_model, {
            "project_id": settings.vertex_project_id,
            "region": settings.vertex_region,
        }
    else:
        missing, model, details = _bedrock_credentials(settings), settings.bedrock_model, {
            "region": settings.aws_region,
            "profile": settings.aws_profile,
        }
    configured = not missing
    if not settings.allow_live_calls:
        missing = missing + ["autorización de consumo (CFL_ALLOW_LIVE_CALLS=true)"]
    mode: Mode = "LIVE" if not missing else "PENDIENTE"
    return ProviderStatus(name, PROVIDER_LABELS[name], model, mode, configured, settings.allow_live_calls, missing, details)


def all_statuses(settings: Settings) -> list[ProviderStatus]:
    return [provider_status(name, settings) for name in PROVIDERS]


def build_provider(name: str, settings: Settings) -> ModelProvider:
    status = provider_status(name, settings)
    if status.mode == "PENDIENTE":
        raise ProviderUnavailable(status.provider, status.missing)
    if status.provider == "mock":
        return MockProvider()
    return build_live_provider(status.provider, settings)


def build_live_provider(name: str, settings: Settings) -> MessagesAPIProvider:
    """Construye el cliente real (no hace llamadas de red al construir)."""
    import anthropic

    common = {"max_tokens": settings.max_tokens, "effort": settings.effort}
    if name == "anthropic":
        return MessagesAPIProvider(
            name="anthropic",
            client=anthropic.Anthropic(),
            model=settings.anthropic_model,
            server_fallbacks=settings.enable_server_fallbacks,
            **common,
        )
    if name == "vertex":
        client = anthropic.AnthropicVertex(project_id=settings.vertex_project_id, region=settings.vertex_region)
        return MessagesAPIProvider(name="vertex", client=client, model=settings.vertex_model, **common)
    if name == "bedrock":
        client = anthropic.AnthropicBedrockMantle(aws_region=settings.aws_region, aws_profile=settings.aws_profile)
        return MessagesAPIProvider(name="bedrock", client=client, model=settings.bedrock_model, **common)
    raise ValueError(f"Proveedor sin cliente real: {name}")
