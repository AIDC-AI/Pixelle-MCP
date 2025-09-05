# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

def format_duration(duration_seconds: float) -> str:
    """
    Convert seconds to a human-friendly time string
    
    Args:
        duration_seconds: Duration (seconds)
        
    Returns:
        Formatted time string, such as: 1h23m45s, 2m30s, 1.5s, 500ms
    """
    if duration_seconds < 0:
        return "0ms"
    
    # Convert to milliseconds
    total_ms = int(duration_seconds * 1000)
    
    # If less than 1 second, display milliseconds
    if total_ms < 1000:
        return f"{total_ms}ms"
    
    # Convert to each time unit
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = duration_seconds % 60
    
    # Build the time string
    time_parts = []
    
    if hours > 0:
        time_parts.append(f"{hours}h")
    
    if minutes > 0:
        time_parts.append(f"{minutes}m")
    
    # For seconds, if there is a decimal part and the total duration is less than 10 seconds, keep 1 decimal place
    if seconds > 0:
        if duration_seconds < 10 and seconds != int(seconds):
            time_parts.append(f"{seconds:.1f}s")
        else:
            time_parts.append(f"{int(seconds)}s")
    
    # If there are no time parts (theoretically should not happen), return 0ms
    if not time_parts:
        return "0ms"
    
    return "".join(time_parts) 