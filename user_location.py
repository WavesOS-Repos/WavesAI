#!/usr/bin/env python3
"""
WavesAI Global Location Configuration
Automatic location detection for users worldwide
"""

# Global Location Detection Settings
LOCATION_CONFIG = {
    # Automatic IP-based location detection (ENABLED by default for global users)
    'auto_detect': True,
    
    # Manual override (only enable if automatic detection is inaccurate in your region)
    'use_manual_override': False,
    
    # Manual location (example - only used if use_manual_override is True)
    'manual_location': {
        'city': 'Your_City',
        'region': 'Your_State_Province', 
        'country': 'Your_Country'
    },
    
    # Cache duration for location detection (in seconds)
    # 1800 = 30 minutes (recommended for most users)
    'cache_duration': 1800
}

def setup_user_location(location_weather_service):
    """Setup user's location detection behavior"""
    
    if LOCATION_CONFIG['use_manual_override']:
        # Use manual location override
        manual_loc = LOCATION_CONFIG['manual_location']
        location_weather_service.set_manual_location(
            city=manual_loc['city'],
            region=manual_loc['region'],
            country=manual_loc['country']
        )
        print(f"✅ Manual location set to: {manual_loc['city']}, {manual_loc['region']}, {manual_loc['country']}")
    else:
        # Use automatic IP-based detection
        location_weather_service.set_auto_detection(
            cache_duration=LOCATION_CONFIG['cache_duration']
        )
        print("[WavesAI] Automatic location detection enabled")
