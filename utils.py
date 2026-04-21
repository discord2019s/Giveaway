import re
from datetime import datetime, timedelta

def parse_duration(duration_str: str) -> int:
    duration_str = duration_str.strip().lower()
    duration_str = duration_str.replace(" ", "")
    
    if duration_str.isdigit():
        return int(duration_str)
    
    pattern = r'(\d+)([smhd])'
    matches = re.findall(pattern, duration_str)
    
    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit == 's':
            total_seconds += value
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 'h':
            total_seconds += value * 3600
        elif unit == 'd':
            total_seconds += value * 86400
    
    if total_seconds == 0:
        return 3600
    
    return total_seconds

def format_time(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0:
        parts.append(f"{secs}s")
    
    return " ".join(parts) if parts else "0s"

def get_end_time(duration_seconds: int) -> datetime:
    return datetime.now() + timedelta(seconds=duration_seconds)