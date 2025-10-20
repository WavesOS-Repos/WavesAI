#!/usr/bin/env python3
"""
WavesAI Location and Weather Module
Handles location detection and weather information
"""

import requests
import json
from typing import Dict, Optional
from datetime import datetime


class LocationWeatherService:
    """Handles location detection and weather information"""
    
    def __init__(self):
        self.user_agent = 'WavesAI/1.0 (https://github.com/wavesai/wavesai)'
        self.cached_location = None
        self.cache_timestamp = None
        self.cache_duration = 3600  # Default cache duration
        self.manual_location = None  # Allow manual location override
        self.auto_detection_enabled = True  # Enable automatic detection by default
    
    def set_manual_location(self, city: str, region: str = "", country: str = "Unknown"):
        """Set manual location override"""
        # Auto-detect timezone and country code based on common patterns
        timezone = self._get_timezone_for_country(country)
        country_code = self._get_country_code(country)
        
        self.manual_location = {
            'city': city,
            'region': region,
            'country': country,
            'country_code': country_code,
            'lat': 0.0,
            'lon': 0.0,
            'timezone': timezone,
            'isp': 'Manual Override',
            'manual': True
        }
        self.auto_detection_enabled = False  # Disable auto-detection when manual is set
    
    def set_auto_detection(self, cache_duration: int = 1800):
        """Enable automatic location detection with configurable cache duration"""
        self.manual_location = None  # Clear manual override
        self.auto_detection_enabled = True
        self.cache_duration = cache_duration
        
        # Clear existing cache to force fresh detection
        self.cached_location = None
        self.cache_timestamp = None
    
    def refresh_location(self):
        """Force refresh of location detection (useful for travelers)"""
        self.cached_location = None
        self.cache_timestamp = None
        return self.get_location()
    
    def _get_timezone_for_country(self, country: str) -> str:
        """Get appropriate timezone for a country"""
        country_lower = country.lower()
        
        # Major timezone mappings for global coverage
        timezone_map = {
            'united states': 'America/New_York',
            'usa': 'America/New_York',
            'canada': 'America/Toronto',
            'united kingdom': 'Europe/London',
            'uk': 'Europe/London',
            'germany': 'Europe/Berlin',
            'france': 'Europe/Paris',
            'italy': 'Europe/Rome',
            'spain': 'Europe/Madrid',
            'russia': 'Europe/Moscow',
            'china': 'Asia/Shanghai',
            'japan': 'Asia/Tokyo',
            'south korea': 'Asia/Seoul',
            'india': 'Asia/Kolkata',
            'australia': 'Australia/Sydney',
            'brazil': 'America/Sao_Paulo',
            'mexico': 'America/Mexico_City',
            'argentina': 'America/Argentina/Buenos_Aires',
            'south africa': 'Africa/Johannesburg',
            'egypt': 'Africa/Cairo',
            'nigeria': 'Africa/Lagos',
            'thailand': 'Asia/Bangkok',
            'singapore': 'Asia/Singapore',
            'malaysia': 'Asia/Kuala_Lumpur',
            'indonesia': 'Asia/Jakarta',
            'philippines': 'Asia/Manila',
            'vietnam': 'Asia/Ho_Chi_Minh',
            'turkey': 'Europe/Istanbul',
            'israel': 'Asia/Jerusalem',
            'uae': 'Asia/Dubai',
            'saudi arabia': 'Asia/Riyadh'
        }
        
        return timezone_map.get(country_lower, 'UTC')
    
    def _get_country_code(self, country: str) -> str:
        """Get ISO country code for a country"""
        country_lower = country.lower()
        
        # ISO country code mappings
        country_codes = {
            'united states': 'US',
            'usa': 'US',
            'canada': 'CA',
            'united kingdom': 'GB',
            'uk': 'GB',
            'germany': 'DE',
            'france': 'FR',
            'italy': 'IT',
            'spain': 'ES',
            'russia': 'RU',
            'china': 'CN',
            'japan': 'JP',
            'south korea': 'KR',
            'india': 'IN',
            'australia': 'AU',
            'brazil': 'BR',
            'mexico': 'MX',
            'argentina': 'AR',
            'south africa': 'ZA',
            'egypt': 'EG',
            'nigeria': 'NG',
            'thailand': 'TH',
            'singapore': 'SG',
            'malaysia': 'MY',
            'indonesia': 'ID',
            'philippines': 'PH',
            'vietnam': 'VN',
            'turkey': 'TR',
            'israel': 'IL',
            'uae': 'AE',
            'saudi arabia': 'SA'
        }
        
        return country_codes.get(country_lower, 'XX')
    
    def get_location(self) -> Dict:
        """Get user's current location using IP geolocation or manual override"""
        try:
            # Check manual location first
            if self.manual_location:
                return self.manual_location
            
            # Check cache first
            if (self.cached_location and self.cache_timestamp and 
                (datetime.now().timestamp() - self.cache_timestamp) < self.cache_duration):
                return self.cached_location
            
            # Try multiple IP geolocation services for reliability
            services = [
                'http://ip-api.com/json/',
                'https://ipapi.co/json/',
                'https://ipinfo.io/json'
            ]
            
            for service_url in services:
                try:
                    headers = {'User-Agent': self.user_agent}
                    response = requests.get(service_url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Normalize data from different services
                        location = self._normalize_location_data(data, service_url)
                        
                        if location and location.get('city') and location.get('country'):
                            # Cache the result
                            self.cached_location = location
                            self.cache_timestamp = datetime.now().timestamp()
                            return location
                            
                except Exception:
                    continue
            
            # Fallback location if all services fail
            return {
                'city': 'Unknown',
                'region': 'Unknown', 
                'country': 'Unknown',
                'country_code': 'XX',
                'lat': 0.0,
                'lon': 0.0,
                'timezone': 'UTC',
                'isp': 'Unknown'
            }
            
        except Exception as e:
            return {'error': f'Location detection failed: {str(e)}'}
    
    def _normalize_location_data(self, data: Dict, service_url: str) -> Dict:
        """Normalize location data from different services"""
        try:
            if 'ip-api.com' in service_url:
                return {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', data.get('region', 'Unknown')),
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('countryCode', 'XX'),
                    'lat': float(data.get('lat', 0)),
                    'lon': float(data.get('lon', 0)),
                    'timezone': data.get('timezone', 'UTC'),
                    'isp': data.get('isp', 'Unknown'),
                    'ip': data.get('query', 'Unknown')
                }
            elif 'ipapi.co' in service_url:
                return {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'country_code': data.get('country', 'XX'),
                    'lat': float(data.get('latitude', 0)),
                    'lon': float(data.get('longitude', 0)),
                    'timezone': data.get('timezone', 'UTC'),
                    'isp': data.get('org', 'Unknown'),
                    'ip': data.get('ip', 'Unknown')
                }
            elif 'ipinfo.io' in service_url:
                loc = data.get('loc', '0,0').split(',')
                return {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('country', 'XX'),
                    'lat': float(loc[0]) if len(loc) > 0 else 0.0,
                    'lon': float(loc[1]) if len(loc) > 1 else 0.0,
                    'timezone': data.get('timezone', 'UTC'),
                    'isp': data.get('org', 'Unknown'),
                    'ip': data.get('ip', 'Unknown')
                }
            
            return {}
        except Exception:
            return {}
    
    def get_weather(self, location: str = None) -> Dict:
        """Get weather information for a location"""
        try:
            # If no location specified, use current location
            if not location:
                loc_data = self.get_location()
                if loc_data.get('error'):
                    return {'error': 'Could not determine location for weather'}
                
                # Build location string with region if available
                city = loc_data.get('city', 'Unknown')
                region = loc_data.get('region', '')
                country = loc_data.get('country', 'Unknown')
                
                if region and region != city:
                    location = f"{city}, {region}, {country}"
                else:
                    location = f"{city}, {country}"
            
            # Use wttr.in service for weather (no API key required)
            weather_url = f"https://wttr.in/{location}?format=j1"
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(weather_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_weather_data(data, location)
            else:
                return self._get_weather_fallback(location)
                
        except Exception as e:
            return {'error': f'Weather fetch failed: {str(e)}'}
    
    def _parse_weather_data(self, data: Dict, location: str) -> Dict:
        """Parse weather data from wttr.in"""
        try:
            current = data.get('current_condition', [{}])[0]
            today = data.get('weather', [{}])[0]
            
            return {
                'location': location,
                'temperature': f"{current.get('temp_C', 'N/A')}°C ({current.get('temp_F', 'N/A')}°F)",
                'condition': current.get('weatherDesc', [{}])[0].get('value', 'Unknown'),
                'humidity': f"{current.get('humidity', 'N/A')}%",
                'wind': f"{current.get('windspeedKmph', 'N/A')} km/h {current.get('winddir16Point', '')}",
                'feels_like': f"{current.get('FeelsLikeC', 'N/A')}°C",
                'visibility': f"{current.get('visibility', 'N/A')} km",
                'pressure': f"{current.get('pressure', 'N/A')} mb",
                'uv_index': current.get('uvIndex', 'N/A'),
                'high_temp': f"{today.get('maxtempC', 'N/A')}°C",
                'low_temp': f"{today.get('mintempC', 'N/A')}°C",
                'sunrise': today.get('astronomy', [{}])[0].get('sunrise', 'N/A'),
                'sunset': today.get('astronomy', [{}])[0].get('sunset', 'N/A'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception:
            return self._get_weather_fallback(location)
    
    def _get_weather_fallback(self, location: str) -> Dict:
        """Fallback weather response when API fails"""
        return {
            'location': location,
            'error': 'Weather data unavailable',
            'message': f"""**Weather Information for {location}**

I apologize, but I cannot fetch real-time weather data at the moment.

**Suggested alternatives:**
• Check weather apps on your device
• Visit weather websites: weather.com, accuweather.com
• Use command: `open firefox https://weather.com`
• Try: `curl wttr.in/{location.replace(' ', '_')}`

**Quick weather commands:**
• `open gnome-weather` - Open system weather app
• `firefox https://weather.com` - Open weather website

Would you like me to open a weather website for you?"""
        }
    
    def get_location_summary(self) -> str:
        """Get a formatted summary of current location"""
        location = self.get_location()
        
        if location.get('error'):
            return "Location: Unable to determine current location"
        
        city = location.get('city', 'Unknown')
        region = location.get('region', '')
        country = location.get('country', 'Unknown')
        timezone = location.get('timezone', 'UTC')
        
        location_str = f"{city}"
        if region and region != city:
            location_str += f", {region}"
        location_str += f", {country}"
        
        return f"Location: {location_str} ({timezone})"
    
    def get_weather_summary(self, location: str = None) -> str:
        """Get a formatted weather summary"""
        weather = self.get_weather(location)
        
        if weather.get('error'):
            return weather.get('message', f"Weather: {weather['error']}")
        
        temp = weather.get('temperature', 'N/A')
        condition = weather.get('condition', 'Unknown')
        feels_like = weather.get('feels_like', 'N/A')
        humidity = weather.get('humidity', 'N/A')
        
        return f"""**Weather in {weather.get('location', 'Unknown')}:**
• Temperature: {temp} (feels like {feels_like})
• Condition: {condition}
• Humidity: {humidity}
• High/Low: {weather.get('high_temp', 'N/A')}/{weather.get('low_temp', 'N/A')}"""
