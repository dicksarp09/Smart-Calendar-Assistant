"""
MCP Server Module
Model Context Protocol (MCP) for calendar tools
Ensures agent uses tools via standardized MCP interface, never directly
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json


class MCPTool:
    """MCP Tool definition"""
    
    def __init__(self, name: str, description: str, input_schema: Dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class MCPConnection:
    """MCP connection handler"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.registered_tools: List[MCPTool] = []
        self._register_tools()
    
    def _register_tools(self):
        """Register all available calendar tools"""
        
        # Tool 1: get_events
        self.register_tool(MCPTool(
            name="get_events",
            description="Get calendar events for a date range. Returns list of events.",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "time_min": {"type": "string", "description": "Start time (ISO format)"},
                    "time_max": {"type": "string", "description": "End time (ISO format)"}
                },
                "required": ["user_id"]
            }
        ))
        
        # Tool 2: create_event
        self.register_tool(MCPTool(
            name="create_event",
            description="Create a new calendar event with validation and conflict detection.",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "summary": {"type": "string", "description": "Event title"},
                    "description": {"type": "string", "description": "Event description"},
                    "start_time": {"type": "string", "description": "Start time (ISO format)"},
                    "end_time": {"type": "string", "description": "End time (ISO format)"},
                    "time_zone": {"type": "string", "description": "Time zone"},
                    "recurrence": {"type": "array", "description": "RRULE recurrence"}
                },
                "required": ["user_id", "summary", "start_time", "end_time"]
            }
        ))
        
        # Tool 3: update_event
        self.register_tool(MCPTool(
            name="update_event",
            description="Update an existing calendar event.",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "event_id": {"type": "string", "description": "Event ID to update"},
                    "summary": {"type": "string", "description": "New event title"},
                    "description": {"type": "string", "description": "New description"},
                    "start_time": {"type": "string", "description": "New start time"},
                    "end_time": {"type": "string", "description": "New end time"}
                },
                "required": ["user_id", "event_id"]
            }
        ))
        
        # Tool 4: delete_event
        self.register_tool(MCPTool(
            name="delete_event",
            description="Delete a calendar event.",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "event_id": {"type": "string", "description": "Event ID to delete"}
                },
                "required": ["user_id", "event_id"]
            }
        ))
        
        # Tool 5: find_available_slots
        self.register_tool(MCPTool(
            name="find_available_slots",
            description="Find available time slots for scheduling.",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                    "duration_minutes": {"type": "integer", "description": "Meeting duration"}
                },
                "required": ["user_id", "date"]
            }
        ))
        
        # Tool 6: check_conflicts
        self.register_tool(MCPTool(
            name="check_conflicts",
            description="Check for scheduling conflicts.",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "start_time": {"type": "string", "description": "Start time (ISO)"},
                    "end_time": {"type": "string", "description": "End time (ISO)"}
                },
                "required": ["user_id", "start_time", "end_time"]
            }
        ))
    
    def register_tool(self, tool: MCPTool):
        """Register a tool"""
        self.registered_tools.append(tool)
    
    def register_handler(self, name: str, handler: Callable):
        """Register tool handler function"""
        self.tools[name] = handler
    
    def list_tools(self) -> List[Dict]:
        """List all available tools (MCP protocol)"""
        return [tool.to_dict() for tool in self.registered_tools]
    
    async def call_tool(self, name: str, arguments: Dict) -> Dict:
        """
        Call a tool via MCP protocol.
        Agent MUST use this method, never call calendar service directly.
        """
        if name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {name}"
            }
        
        try:
            handler = self.tools[name]
            result = await handler(**arguments)
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_schema(self, name: str) -> Optional[Dict]:
        """Get tool schema"""
        for tool in self.registered_tools:
            if tool.name == name:
                return tool.to_dict()
        return None


class MCPServer:
    """MCP Server for calendar tools"""
    
    def __init__(self):
        self.connection = MCPConnection()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup tool handlers - all go through MCP, never direct API calls"""
        
        async def get_events_handler(user_id: str, time_min: str = None, 
                                     time_max: str = None) -> List[Dict]:
            """Handle get_events tool call"""
            from backend.services.calendar_service import calendar_service
            
            t_min = datetime.fromisoformat(time_min) if time_min else None
            t_max = datetime.fromisoformat(time_max) if time_max else None
            
            events = await calendar_service.get_events(user_id, t_min, t_max)
            return [e.dict() if hasattr(e, 'dict') else e for e in events]
        
        async def create_event_handler(user_id: str, summary: str, 
                                       start_time: str, end_time: str,
                                       description: str = None, 
                                       time_zone: str = "UTC",
                                       recurrence: List[str] = None) -> Dict:
            """Handle create_event tool call"""
            from backend.services.calendar_service import calendar_service
            
            event_data = {
                "summary": summary,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "time_zone": time_zone,
                "recurrence": recurrence
            }
            
            result = await calendar_service.create_event(user_id, event_data)
            return result
        
        async def update_event_handler(user_id: str, event_id: str,
                                       summary: str = None, 
                                       description: str = None,
                                       start_time: str = None,
                                       end_time: str = None) -> Dict:
            """Handle update_event tool call"""
            from backend.services.calendar_service import calendar_service
            
            event_data = {}
            if summary:
                event_data["summary"] = summary
            if description:
                event_data["description"] = description
            if start_time:
                event_data["start_time"] = start_time
            if end_time:
                event_data["end_time"] = end_time
            
            result = await calendar_service.update_event(user_id, event_id, event_data)
            return result.dict() if hasattr(result, 'dict') else result
        
        async def delete_event_handler(user_id: str, event_id: str) -> bool:
            """Handle delete_event tool call"""
            from backend.services.calendar_service import calendar_service
            
            result = await calendar_service.delete_event(user_id, event_id)
            return result
        
        async def find_available_slots_handler(user_id: str, date: str,
                                             duration_minutes: int = 30) -> List[Dict]:
            """Handle find_available_slots tool call"""
            from backend.services.calendar_service import calendar_service
            
            slots = calendar_service.suggest_time_slots(
                user_id, "meeting", date, duration_minutes
            )
            return slots
        
        async def check_conflicts_handler(user_id: str, start_time: str,
                                         end_time: str) -> List[Dict]:
            """Handle check_conflicts tool call"""
            from backend.services.calendar_service import calendar_service
            
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            
            conflicts = await calendar_service.check_conflicts(user_id, start, end)
            return [c.dict() if hasattr(c, 'dict') else c for c in conflicts]
        
        # Register handlers
        self.connection.register_handler("get_events", get_events_handler)
        self.connection.register_handler("create_event", create_event_handler)
        self.connection.register_handler("update_event", update_event_handler)
        self.connection.register_handler("delete_event", delete_event_handler)
        self.connection.register_handler("find_available_slots", find_available_slots_handler)
        self.connection.register_handler("check_conflicts", check_conflicts_handler)
    
    def get_resources(self) -> Dict:
        """Get MCP resources"""
        return {
            "tools": self.connection.list_tools(),
            "version": "1.0.0"
        }
    
    async def process_request(self, request: Dict) -> Dict:
        """Process MCP request"""
        method = request.get("method")
        
        if method == "tools/list":
            return {"tools": self.connection.list_tools()}
        
        elif method == "tools/call":
            tool_name = request.get("tool")
            arguments = request.get("arguments", {})
            return await self.connection.call_tool(tool_name, arguments)
        
        elif method == "resources":
            return self.get_resources()
        
        else:
            return {"error": f"Unknown method: {method}"}


# Singleton MCP server instance
mcp_server = MCPServer()


def get_mcp_server() -> MCPServer:
    """Get MCP server instance"""
    return mcp_server