"""Read-only Model Context Protocol surface for the DClocking project.

The protocol layer deliberately depends on the pure-Python catalog service and
never imports the Qt canvas or a hardware controller.  This keeps local MCP
clients useful while ensuring discovery and validation calls have no device
side effects.
"""

from __future__ import annotations

import argparse
import hmac
import ipaddress
import logging
import os
from collections.abc import Sequence
from typing import Any, Protocol

from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import StrictBool, StrictInt, StrictStr


LOGGER = logging.getLogger(__name__)
DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 8765
TOKEN_ENVIRONMENT_VARIABLE = "DCLOCKING_MCP_TOKEN"
MINIMUM_HTTP_TOKEN_LENGTH = 32
MAXIMUM_HTTP_TOKEN_LENGTH = 256
HTTP_MAX_REQUEST_BODY_SIZE = 1024 * 1024
HTTP_MAX_SESSIONS = 16
HTTP_SESSION_IDLE_TIMEOUT = 300.0

_READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


class CatalogService(Protocol):
    """Operations required by the MCP protocol adapter."""

    def list_module_types(self, category: str | None = None) -> dict[str, Any]: ...

    def get_module_spec(self, module_type: str) -> dict[str, Any]: ...

    def validate_parameters(
        self, module_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]: ...

    def validate_connection(
        self,
        source_module: str,
        source_port: str | int,
        destination_module: str,
        destination_port: str | int,
        developer_mode: bool = False,
    ) -> dict[str, Any]: ...

    def validate_design(self, design: dict[str, Any]) -> dict[str, Any]: ...


class _StaticTokenVerifier:
    """Constant-time verifier for the opt-in, loopback-only HTTP transport."""

    def __init__(self, token: str) -> None:
        self._token = token.encode("ascii")

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            candidate = token.encode("ascii")
        except UnicodeEncodeError:
            return None
        if not hmac.compare_digest(candidate, self._token):
            return None
        return AccessToken(
            token=token,
            client_id="dclocking-local-client",
            scopes=["dclocking.read"],
        )


def _internal_error(operation: str, exc: Exception) -> dict[str, Any]:
    # Do not include exception messages: service errors may contain paths,
    # secrets, register values, or other information unsuitable for clients.
    LOGGER.error(
        "MCP catalog operation %s failed (%s)", operation, type(exc).__name__
    )
    return {
        "ok": False,
        "errors": [
            {
                "code": "internal_error",
                "field": operation,
                "message": "The local catalog operation could not be completed.",
            }
        ],
    }


def _safe_call(operation: str, function, /, *args, **kwargs) -> dict[str, Any]:
    try:
        return function(*args, **kwargs)
    except Exception as exc:  # defensive boundary around injected services
        return _internal_error(operation, exc)


def _http_token_error(token: str) -> str | None:
    if len(token) < MINIMUM_HTTP_TOKEN_LENGTH:
        return f"must contain at least {MINIMUM_HTTP_TOKEN_LENGTH} characters"
    if len(token) > MAXIMUM_HTTP_TOKEN_LENGTH:
        return f"must contain at most {MAXIMUM_HTTP_TOKEN_LENGTH} characters"
    if any(character.isspace() for character in token):
        return "must not contain whitespace"
    if any(not 0x21 <= ord(character) <= 0x7E for character in token):
        return "must contain only visible ASCII characters"
    return None


def create_mcp_server(
    service: CatalogService | None = None,
    *,
    http_token: str | None = None,
    resource_server_url: str | None = None,
) -> MCPServer:
    """Create the DClocking MCP server independently of its transport.

    ``http_token`` and ``resource_server_url`` must be supplied together.  The
    stdio server intentionally has no bearer-token configuration because the
    MCP client owns the child process and communicates through its pipes.
    """

    if service is None:
        from .mcp_catalog_service import McpCatalogService

        service = McpCatalogService()

    if (http_token is None) != (resource_server_url is None):
        raise ValueError("HTTP token and resource server URL must be supplied together")
    if http_token is not None:
        token_error = _http_token_error(http_token)
        if token_error is not None:
            raise ValueError(f"HTTP token {token_error}")

    server_kwargs: dict[str, Any] = {}
    if http_token is not None and resource_server_url is not None:
        server_kwargs.update(
            token_verifier=_StaticTokenVerifier(http_token),
            auth=AuthSettings(
                issuer_url=resource_server_url,
                # This optional local transport uses an explicitly configured,
                # pre-shared bearer token rather than advertising an OAuth
                # authorization server that does not exist.
                resource_server_url=None,
                validate_token_resource=False,
                required_scopes=["dclocking.read"],
            ),
        )

    server = MCPServer(
        name="dclocking-local",
        title="DClocking Local FPGA Catalog",
        description="Read-only FPGA module discovery and design validation.",
        version="1.0.0",
        log_level="WARNING",
        **server_kwargs,
    )

    @server.tool(
        name="list_module_types",
        description="List registered FPGA module types, optionally by category.",
        annotations=_READ_ONLY,
    )
    def list_module_types(category: StrictStr | None = None) -> dict[str, Any]:
        return _safe_call("list_module_types", service.list_module_types, category)

    @server.tool(
        name="get_module_spec",
        description="Get ports, parameters, limits, and metadata for one module type.",
        annotations=_READ_ONLY,
    )
    def get_module_spec(module_type: StrictStr) -> dict[str, Any]:
        return _safe_call("get_module_spec", service.get_module_spec, module_type)

    @server.tool(
        name="validate_parameters",
        description="Validate module parameters without changing the canvas or hardware.",
        annotations=_READ_ONLY,
    )
    def validate_parameters(
        module_type: StrictStr, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        return _safe_call(
            "validate_parameters",
            service.validate_parameters,
            module_type,
            parameters,
        )

    @server.tool(
        name="validate_connection",
        description="Check whether two registered module ports can be connected.",
        annotations=_READ_ONLY,
    )
    def validate_connection(
        source_module: StrictStr,
        source_port: StrictStr | StrictInt,
        destination_module: StrictStr,
        destination_port: StrictStr | StrictInt,
        developer_mode: StrictBool = False,
    ) -> dict[str, Any]:
        return _safe_call(
            "validate_connection",
            service.validate_connection,
            source_module,
            source_port,
            destination_module,
            destination_port,
            developer_mode,
        )

    @server.tool(
        name="validate_design",
        description=(
            "Validate a proposed MCP module graph without reading or writing files. "
            "This uses the documented nodes/connections schema, not the Qt saved-config format."
        ),
        annotations=_READ_ONLY,
    )
    def validate_design(design: dict[str, Any]) -> dict[str, Any]:
        return _safe_call("validate_design", service.validate_design, design)

    @server.resource(
        "dclocking://project/info",
        name="project-info",
        description="Static description of the local DClocking MCP surface.",
        mime_type="application/json",
    )
    def project_info() -> dict[str, Any]:
        return {
            "name": "DClocking",
            "server": "dclocking-local",
            "version": "1.0.0",
            "access": "read-only",
            "capabilities": [
                "module-catalog",
                "parameter-validation",
                "design-validation",
            ],
        }

    @server.resource(
        "dclocking://modules/catalog",
        name="module-catalog",
        description="Complete registered FPGA module catalog summary.",
        mime_type="application/json",
    )
    def module_catalog() -> dict[str, Any]:
        return _safe_call("list_module_types", service.list_module_types)

    @server.resource(
        "dclocking://modules/{module_type}",
        name="module-specification",
        description="Specification for one percent-encoded FPGA module type.",
        mime_type="application/json",
    )
    def module_specification(module_type: str) -> dict[str, Any]:
        return _safe_call("get_module_spec", service.get_module_spec, module_type)

    return server


def _port_number(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _canonical_loopback_host(host: str) -> str | None:
    candidate = host.strip()
    if candidate != host:
        return None
    # Scoped IPv6 literals are not valid in the Pydantic URL used by the SDK's
    # local auth settings and would otherwise fail later with a traceback.
    if "%" in candidate:
        return None
    if candidate.lower().rstrip(".") == "localhost":
        return "localhost"
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return str(address) if address.is_loopback else None


def _render_http_host(host: str) -> str:
    rendered_host = f"[{host}]" if ":" in host else host
    return rendered_host


def _resource_server_url(host: str, port: int) -> str:
    rendered_host = _render_http_host(host)
    return f"http://{rendered_host}:{port}/mcp"


def _transport_security_settings(
    host: str, port: int
) -> TransportSecuritySettings:
    rendered_host = _render_http_host(host)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[f"{rendered_host}:{port}"],
        allowed_origins=[f"http://{rendered_host}:{port}"],
    )


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dclocking-mcp",
        description="Start the read-only local DClocking MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    parser.add_argument("--host", default=DEFAULT_HTTP_HOST)
    parser.add_argument("--port", type=_port_number, default=DEFAULT_HTTP_PORT)
    return parser


def _run_server(server: MCPServer, /, **transport_options: Any) -> int:
    try:
        server.run(**transport_options)
    except KeyboardInterrupt:
        return 130
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Start the requested transport and return a process exit status."""

    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    if args.transport == "stdio":
        return _run_server(create_mcp_server(), transport="stdio")

    host = _canonical_loopback_host(args.host)
    if host is None:
        parser.error("streamable HTTP may only bind to a loopback host")

    token = os.environ.get(TOKEN_ENVIRONMENT_VARIABLE, "")
    token_error = _http_token_error(token)
    if token_error is not None:
        parser.error(f"{TOKEN_ENVIRONMENT_VARIABLE} {token_error}")

    url = _resource_server_url(host, args.port)
    server = create_mcp_server(http_token=token, resource_server_url=url)
    return _run_server(
        server,
        transport="streamable-http",
        host=host,
        port=args.port,
        max_request_body_size=HTTP_MAX_REQUEST_BODY_SIZE,
        max_sessions=HTTP_MAX_SESSIONS,
        session_idle_timeout=HTTP_SESSION_IDLE_TIMEOUT,
        transport_security=_transport_security_settings(host, args.port),
    )


if __name__ == "__main__":  # pragma: no cover - exercised through main(argv)
    raise SystemExit(main())
