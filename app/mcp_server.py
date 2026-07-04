import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nomad-navigator-mcp")

@mcp.tool()
def get_attractions(city: str) -> str:
    """Get top travel attractions for a given city.

    Args:
        city: The name of the city.
    """
    city_lower = city.lower()
    if "paris" in city_lower:
        return "1. Eiffel Tower (Iconic landmark, booking recommended)\n2. Louvre Museum (World's largest art museum)\n3. Palace of Versailles (Opulent royal residence)\n4. Seine River Cruise (Scenic boat tours)"
    elif "tokyo" in city_lower:
        return "1. Senso-ji Temple (Tokyo's oldest temple in Asakusa)\n2. Shibuya Crossing (World's busiest pedestrian crossing)\n3. Meiji Shrine (Tranquil shrine in Yoyogi Park)\n4. Akihabara (Hub for gaming, anime, and electronics)"
    elif "new york" in city_lower or "nyc" in city_lower:
        return "1. Central Park (Urban oasis in Manhattan)\n2. Statue of Liberty & Ellis Island (Historic national monuments)\n3. Broadway Theatre District (World-class stage performances)\n4. Empire State Building (Panoramic city views)"
    else:
        return f"1. Local Historic Center (Explore the historical roots of {city})\n2. City Museum of Art (Showcasing local and international artists)\n3. Central Public Park (A green escape with walking trails)\n4. Popular Food Market (Sample local culinary delights)"

@mcp.tool()
def get_weather_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast details for a city over the next N days.

    Args:
        city: The name of the city.
        days: Number of days (default 3).
    """
    city_lower = city.lower()
    if "paris" in city_lower:
        return "Day 1: 18°C, Partly Cloudy, Light Breeze\nDay 2: 20°C, Sunny, Low UV Index\nDay 3: 17°C, Light Showers, Wind 15km/h"
    elif "tokyo" in city_lower:
        return "Day 1: 24°C, Clear, High Humidity\nDay 2: 26°C, Sunny, Perfect for sightseeing\nDay 3: 22°C, Overcast, Mild temperatures"
    else:
        return f"Day 1: 22°C, Clear Sky, Sunny\nDay 2: 21°C, Mild Clouds, Warm\nDay 3: 23°C, Sunny and Dry"

@mcp.tool()
def calculate_transit_time(origin: str, destination: str, mode: str = "transit") -> str:
    """Calculate travel distance and duration between two points.

    Args:
        origin: Starting point address or landmark.
        destination: Destination address or landmark.
        mode: Mode of transport (transit, driving, walking, bicycling).
    """
    mode_lower = mode.lower()
    if mode_lower == "walking":
        return f"Route from {origin} to {destination}: Distance approx 2.5 km. Duration: 30 minutes. Easy walking terrain."
    elif mode_lower == "driving":
        return f"Route from {origin} to {destination}: Distance approx 5.2 km. Duration: 15 minutes (subject to traffic)."
    else:
        return f"Route from {origin} to {destination}: Distance approx 4.8 km. Duration: 20 minutes via local train/metro. Mode: {mode}."

@mcp.tool()
def get_local_tips(city: str) -> str:
    """Retrieve safety tips, cultural norms, and tipping etiquette for a given city.

    Args:
        city: The name of the city.
    """
    city_lower = city.lower()
    if "paris" in city_lower:
        return "Cultural: Always greet with 'Bonjour' or 'Bonsoir' when entering shops. Tipping: Service is included (service compris), but leaving 5-10% is polite. Safety: Keep bags secure around major tourist areas (pickpockets)."
    elif "tokyo" in city_lower:
        return "Cultural: Bowing is standard greeting. Avoid eating while walking. Tipping: Strictly no tipping; it is considered rude. Safety: Extremely safe, but keep left on escalators."
    else:
        return f"Cultural: Respect local customs and dress modestly in historic sites. Tipping: 10% is customary for good service. Safety: Stay aware of your surroundings and stick to well-lit areas at night."

if __name__ == "__main__":
    mcp.run()
