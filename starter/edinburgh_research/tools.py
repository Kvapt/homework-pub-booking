"""Ex5 tools."""

from __future__ import annotations

import json
from pathlib import Path

from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolError, ToolRegistry, ToolResult, _RegisteredTool

_SAMPLE_DATA = Path(__file__).parent / "sample_data"


def venue_search(near: str, party_size: int, budget_max_gbp: int = 1000) -> ToolResult:
    from starter.edinburgh_research.integrity import record_tool_call

    venues_path = _SAMPLE_DATA / "venues.json"
    if not venues_path.exists():
        raise ToolError("SA_TOOL_DEPENDENCY_MISSING", "venues.json not found")

    venues = json.loads(venues_path.read_text(encoding="utf-8"))
    results = [
        v
        for v in venues
        if v.get("open_now")
        and near.lower() in v.get("area", "").lower()
        and v.get("seats_available_evening", 0) >= party_size
        and (v.get("hire_fee_gbp", 0) + v.get("min_spend_gbp", 0)) <= budget_max_gbp
    ]

    output = {"near": near, "party_size": party_size, "results": results, "count": len(results)}
    record_tool_call(
        "venue_search",
        {"near": near, "party_size": party_size, "budget_max_gbp": budget_max_gbp},
        output,
    )
    return ToolResult(
        success=True,
        output=output,
        summary=f"venue_search({near}, party={party_size}): {len(results)} result(s)",
    )


def get_weather(city: str, date: str) -> ToolResult:
    from starter.edinburgh_research.integrity import record_tool_call

    weather_path = _SAMPLE_DATA / "weather.json"
    if not weather_path.exists():
        raise ToolError("SA_TOOL_DEPENDENCY_MISSING", "weather.json not found")

    weather = json.loads(weather_path.read_text(encoding="utf-8"))
    city_data = weather.get(city.lower())
    if not city_data:
        record_tool_call("get_weather", {"city": city, "date": date}, {})
        return ToolResult(
            success=False, output={}, summary=f"get_weather({city}, {date}): city not found"
        )

    day_data = city_data.get(date)
    if not day_data:
        record_tool_call("get_weather", {"city": city, "date": date}, {})
        return ToolResult(
            success=False, output={}, summary=f"get_weather({city}, {date}): date not found"
        )

    output = {"city": city, "date": date, **day_data}
    record_tool_call("get_weather", {"city": city, "date": date}, output)
    return ToolResult(
        success=True,
        output=output,
        summary=f"get_weather({city}, {date}): {day_data['condition']}, {day_data['temperature_c']}C",
    )


def calculate_cost(
    venue_id: str,
    party_size: int,
    duration_hours: int,
    catering_tier: str = "bar_snacks",
) -> ToolResult:
    from starter.edinburgh_research.integrity import record_tool_call

    catering_path = _SAMPLE_DATA / "catering.json"
    venues_path = _SAMPLE_DATA / "venues.json"
    if not catering_path.exists():
        raise ToolError("SA_TOOL_DEPENDENCY_MISSING", "catering.json not found")

    catering = json.loads(catering_path.read_text(encoding="utf-8"))
    venues = json.loads(venues_path.read_text(encoding="utf-8"))
    venue = next((v for v in venues if v["id"] == venue_id), None)
    if not venue:
        raise ToolError("SA_TOOL_INVALID_INPUT", f"venue_id {venue_id!r} not found")

    base_per_head = catering["base_rates_gbp_per_head"][catering_tier]
    venue_mult = catering["venue_modifiers"].get(venue_id, 1.0)
    subtotal = int(base_per_head * venue_mult * party_size * max(1, duration_hours))
    service = int(subtotal * catering["service_charge_percent"] / 100)
    total = max(subtotal, venue["min_spend_gbp"]) + service + venue["hire_fee_gbp"]

    if total < 300:
        deposit = 0
    elif total <= 1000:
        deposit = int(total * 0.20)
    else:
        deposit = int(total * 0.30)

    output = {
        "venue_id": venue_id,
        "party_size": party_size,
        "duration_hours": duration_hours,
        "catering_tier": catering_tier,
        "subtotal_gbp": subtotal,
        "service_gbp": service,
        "total_gbp": total,
        "deposit_required_gbp": deposit,
    }
    record_tool_call(
        "calculate_cost",
        {
            "venue_id": venue_id,
            "party_size": party_size,
            "duration_hours": duration_hours,
            "catering_tier": catering_tier,
        },
        output,
    )
    return ToolResult(
        success=True,
        output=output,
        summary=f"calculate_cost({venue_id}, {party_size}): total £{total}, deposit £{deposit}",
    )


def generate_flyer(session: Session, event_details: dict) -> ToolResult:
    from starter.edinburgh_research.integrity import record_tool_call

    venue_name = event_details.get("venue_name", "TBD")
    venue_address = event_details.get("venue_address", "")
    date = event_details.get("date", "")
    time = event_details.get("time", "")
    party_size = event_details.get("party_size", "")
    condition = event_details.get("condition", "")
    temperature_c = event_details.get("temperature_c", "")
    total_gbp = event_details.get("total_gbp", "")
    deposit_required_gbp = event_details.get("deposit_required_gbp", 0)

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Event at {venue_name}</title></head>
<body><h1>Event Booking — {venue_name}</h1>
<dl>
<dt>Venue</dt><dd data-testid="venue_name">{venue_name}</dd>
<dt>Address</dt><dd data-testid="venue_address">{venue_address}</dd>
<dt>Date</dt><dd data-testid="date">{date}</dd>
<dt>Time</dt><dd data-testid="time">{time}</dd>
<dt>Party size</dt><dd data-testid="party_size">{party_size}</dd>
<dt>Weather</dt><dd data-testid="condition">{condition}, <span data-testid="temperature_c">{temperature_c}</span>°C</dd>
<dt>Total cost</dt><dd data-testid="total">£{total_gbp}</dd>
<dt>Deposit</dt><dd data-testid="deposit">£{deposit_required_gbp}</dd>
</dl></body></html>"""

    flyer_path = session.workspace_dir / "flyer.html"
    flyer_path.parent.mkdir(parents=True, exist_ok=True)
    flyer_path.write_text(html, encoding="utf-8")

    output = {"path": "workspace/flyer.html", "bytes_written": len(html)}
    record_tool_call("generate_flyer", {"event_details": event_details}, output)
    return ToolResult(
        success=True,
        output=output,
        summary=f"generate_flyer: wrote workspace/flyer.html ({len(html)} chars)",
    )


def build_tool_registry(session: Session) -> ToolRegistry:
    """
    DO NOT change the tool names — the tests and grader call them by name.
    """
    from sovereign_agent.tools.builtin import make_builtin_registry

    reg = make_builtin_registry(session)

    reg.register(
        _RegisteredTool(
            name="venue_search",
            description="Search Edinburgh venues by area, party size, and max budget.",
            fn=venue_search,
            parameters_schema={
                "type": "object",
                "properties": {
                    "near": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "budget_max_gbp": {"type": "integer", "default": 1000},
                },
                "required": ["near", "party_size"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,
            examples=[
                {
                    "input": {"near": "Haymarket", "party_size": 6, "budget_max_gbp": 800},
                    "output": {"count": 1, "results": [{"id": "haymarket_tap"}]},
                }
            ],
        )
    )

    reg.register(
        _RegisteredTool(
            name="get_weather",
            description="Get scripted weather for a city on a YYYY-MM-DD date.",
            fn=get_weather,
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["city", "date"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,
            examples=[
                {
                    "input": {"city": "Edinburgh", "date": "2026-04-25"},
                    "output": {"condition": "cloudy", "temperature_c": 12},
                }
            ],
        )
    )

    reg.register(
        _RegisteredTool(
            name="calculate_cost",
            description="Compute total cost and deposit for a booking.",
            fn=calculate_cost,
            parameters_schema={
                "type": "object",
                "properties": {
                    "venue_id": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "duration_hours": {"type": "integer"},
                    "catering_tier": {
                        "type": "string",
                        "enum": ["drinks_only", "bar_snacks", "sit_down_meal", "three_course_meal"],
                        "default": "bar_snacks",
                    },
                },
                "required": ["venue_id", "party_size", "duration_hours"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,
            examples=[
                {
                    "input": {"venue_id": "haymarket_tap", "party_size": 6, "duration_hours": 3},
                    "output": {"total_gbp": 540, "deposit_required_gbp": 0},
                }
            ],
        )
    )

    def _flyer_adapter(event_details: dict) -> ToolResult:
        return generate_flyer(session, event_details)

    reg.register(
        _RegisteredTool(
            name="generate_flyer",
            description="Write an HTML flyer for the event to workspace/flyer.html.",
            fn=_flyer_adapter,
            parameters_schema={
                "type": "object",
                "properties": {"event_details": {"type": "object"}},
                "required": ["event_details"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=False,
            examples=[
                {
                    "input": {
                        "event_details": {
                            "venue_name": "Haymarket Tap",
                            "date": "2026-04-25",
                            "party_size": 6,
                        }
                    },
                    "output": {"path": "workspace/flyer.html"},
                }
            ],
        )
    )

    return reg


__all__ = [
    "build_tool_registry",
    "venue_search",
    "get_weather",
    "calculate_cost",
    "generate_flyer",
]
