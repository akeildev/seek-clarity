#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Router for tool execution
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("mcp-router")


class ToolSpec:
    """Specification for an MCP tool"""
    def __init__(self, name: str, description: str, server: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.server = server
        self.parameters = parameters or {}


class McpToolRouter:
    """Routes tool calls to appropriate MCP servers"""

    def __init__(self, config_path: Optional[Path] = None):
        self.tools: Dict[str, ToolSpec] = {}
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.config_path = config_path

        if config_path and config_path.exists():
            self.load_config(config_path)

    def load_config(self, config_path: Path):
        """Load MCP configuration from JSON file"""
        try:
            with open(config_path) as f:
                config = json.load(f)

            # Load server configurations
            self.servers = config.get("servers", {})

            # Load tool specifications
            for tool_config in config.get("tools", []):
                tool = ToolSpec(
                    name=tool_config["name"],
                    description=tool_config["description"],
                    server=tool_config["server"],
                    parameters=tool_config.get("parameters", {})
                )
                self.tools[tool.name] = tool

            logger.info(f"Loaded {len(self.tools)} tools from config")
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], timeout: int = 30) -> Any:
        """Execute an MCP tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        server = self.servers.get(tool.server)

        if not server:
            raise ValueError(f"Server '{tool.server}' not configured")

        # Build MCP command
        command = self._build_command(server, tool, arguments)

        try:
            # Execute tool with timeout
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )

            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Tool execution failed: {error_msg}")

            # Parse and return result
            result = json.loads(stdout.decode()) if stdout else {}
            return result

        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool '{tool_name}' timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            raise

    def _build_command(self, server: Dict[str, Any], tool: ToolSpec, arguments: Dict[str, Any]) -> List[str]:
        """Build command to execute MCP tool"""
        command = [server.get("command", "mcp")]

        # Add server-specific arguments
        if server.get("args"):
            command.extend(server["args"])

        # Add tool name and arguments
        command.append(tool.name)
        if arguments:
            command.append(json.dumps(arguments))

        return command

    def get_tool_by_name(self, name: str) -> Optional[ToolSpec]:
        """Get tool specification by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[ToolSpec]:
        """List all available tools"""
        return list(self.tools.values())

    def find_tools(self, query: str, max_results: int = 5) -> List[ToolSpec]:
        """Find tools matching a query"""
        query_lower = query.lower()
        matches = []

        for tool in self.tools.values():
            if query_lower in tool.name.lower() or query_lower in tool.description.lower():
                matches.append(tool)

        # Sort by relevance (name match first, then description)
        matches.sort(key=lambda t: (
            query_lower not in t.name.lower(),
            -len(set(query_lower.split()) & set(t.description.lower().split()))
        ))

        return matches[:max_results]