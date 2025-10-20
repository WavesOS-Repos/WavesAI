# 🌍 WavesAI - Global AI Assistant

**A sophisticated AI assistant designed for users worldwide with automatic location awareness**

[![Global Support](https://img.shields.io/badge/Global-Support-blue)](https://github.com/wavesai/wavesai)
[![Auto Location](https://img.shields.io/badge/Auto-Location-green)](https://github.com/wavesai/wavesai)
[![Multi Region](https://img.shields.io/badge/Multi-Region-orange)](https://github.com/wavesai/wavesai)

## 🚀 **Quick Start for Global Users**

### **1. Clone & Setup**
```bash
git clone https://github.com/wavesai/wavesai.git
cd wavesai
pip install -r requirements.txt
```

### **2. Run Anywhere in the World**
```bash
python wavesai.py
```

**That's it!** WavesAI automatically detects your location and provides relevant local information.

---

## 🌍 **Global Features**

### **✅ Automatic Location Detection**
- **Works worldwide** - No manual configuration needed
- **IP-based geolocation** with multiple fallback services
- **30+ country timezone support**
- **Real-time location updates** for travelers

### **✅ Localized Information**
- **Weather**: Automatic weather for your current location
- **Time**: Local timezone-aware responses
- **News**: Global and regional news detection
- **Language**: Supports major global regions

### **✅ Global Weather Coverage**
```bash
# Automatic location weather
wavesctl weather

# Any city worldwide
wavesctl weather "New York"
wavesctl weather "London"
wavesctl weather "Tokyo"
wavesctl weather "Sydney"
```

### **✅ Global News Support**
```bash
# World news (default)
wavesctl news

# Country-specific news
wavesctl news -r usa
wavesctl news -r uk
wavesctl news -r india
wavesctl news -r australia
```

---

## 🗺️ **Supported Regions**

### **Fully Supported Countries:**
🇺🇸 **USA** | 🇬🇧 **UK** | 🇨🇦 **Canada** | 🇦🇺 **Australia** | 🇩🇪 **Germany** | 🇫🇷 **France** | 🇮🇹 **Italy** | 🇪🇸 **Spain** | 🇷🇺 **Russia** | 🇨🇳 **China** | 🇯🇵 **Japan** | 🇰🇷 **South Korea** | 🇮🇳 **India** | 🇧🇷 **Brazil** | 🇲🇽 **Mexico** | 🇦🇷 **Argentina** | 🇿🇦 **South Africa** | 🇪🇬 **Egypt** | 🇳🇬 **Nigeria** | 🇹🇭 **Thailand** | 🇸🇬 **Singapore** | 🇲🇾 **Malaysia** | 🇮🇩 **Indonesia** | 🇵🇭 **Philippines** | 🇻🇳 **Vietnam** | 🇹🇷 **Turkey** | 🇮🇱 **Israel** | 🇦🇪 **UAE** | 🇸🇦 **Saudi Arabia**

### **Automatic Features by Region:**
- **Timezone Detection**: Automatic local time
- **Weather Services**: Local weather conditions
- **News Sources**: Regional news preferences
- **Language Support**: English with regional awareness

---

## 🛠️ **Configuration (Optional)**

### **Default: Automatic Detection (Recommended)**
```python
# user_location.py
LOCATION_CONFIG = {
    'auto_detect': True,        # ✅ Enabled by default
    'use_manual_override': False,
    'cache_duration': 1800      # 30 minutes
}
```

### **Manual Override (If Needed)**
```python
# Only if automatic detection is inaccurate
LOCATION_CONFIG = {
    'auto_detect': False,
    'use_manual_override': True,
    'manual_location': {
        'city': 'Your_City',
        'region': 'Your_State_Province',
        'country': 'Your_Country'
    }
}
```

---

## 📱 **Global Usage Examples**

### **🇺🇸 User in New York:**
```
[You] ➜ what's my location?
[WavesAI] ➜ You are currently in New York, New York, United States.

[You] ➜ what's the weather like?
[WavesAI] ➜ The weather in New York is currently 18°C and partly cloudy.

[You] ➜ latest news
[WavesAI] ➜ Here are the latest US news headlines...
```

### **🇬🇧 User in London:**
```
[You] ➜ where am i?
[WavesAI] ➜ You are in London, England, United Kingdom.

[You] ➜ temperature here
[WavesAI] ➜ The current temperature in London is 12°C with light rain.

[You] ➜ uk news
[WavesAI] ➜ Here are the latest UK news updates...
```

### **🇯🇵 User in Tokyo:**
```
[You] ➜ current location
[WavesAI] ➜ You are in Tokyo, Japan.

[You] ➜ weather condition
[WavesAI] ➜ Tokyo weather: 22°C, sunny with light breeze.

[You] ➜ japanese news
[WavesAI] ➜ Latest news from Japan...
```

---

## 🔧 **CLI Commands (Global)**

### **Location Commands:**
```bash
wavesctl location              # Show current location
wavesctl location --refresh    # Force refresh (for travelers)
```

### **Weather Commands:**
```bash
wavesctl weather              # Current location weather
wavesctl weather "Paris"      # Specific city weather
wavesctl weather "Mumbai"     # Any global city
```

### **News Commands:**
```bash
wavesctl news                 # World news
wavesctl news -r usa          # US news
wavesctl news -r uk           # UK news
wavesctl news -r india        # India news
```

### **System Commands:**
```bash
wavesctl status              # System info with location
wavesctl top                 # Process list
wavesctl find firefox        # Find processes
```

---

## 🌐 **Global Architecture**

### **Location Detection Services:**
1. **ip-api.com** (Primary)
2. **ipapi.co** (Fallback)
3. **ipinfo.io** (Secondary)

### **Weather Coverage:**
- **Global API**: wttr.in (no API key required)
- **Supports**: Any city worldwide
- **Data**: Temperature, conditions, humidity, forecasts

### **News Sources:**
- **Global**: BBC, Reuters, CNN, Associated Press
- **Regional**: Country-specific sources
- **Auto-detection**: Based on user location and query

### **Timezone Support:**
- **30+ Major Timezones** automatically detected
- **Automatic DST** handling
- **Local time responses** in user's timezone

---

## 🚀 **For Developers**

### **Adding New Regions:**
```python
# In modules/location_weather.py
timezone_map = {
    'your_country': 'Your/Timezone',
    # Add new countries here
}

country_codes = {
    'your_country': 'YC',
    # Add ISO codes here
}
```

### **Adding News Regions:**
```python
# In wavesai.py _detect_news_region()
country_keywords = {
    'your_country': ['keyword1', 'keyword2'],
    # Add country detection keywords
}
```

---

## 🔒 **Privacy & Security**

### **Location Privacy:**
- **IP-based only** - No GPS or personal data
- **Configurable caching** (30 minutes default)
- **No data storage** - Location detected fresh each time
- **Multiple fallback services** for reliability

### **Data Handling:**
- **No personal information stored**
- **No location tracking**
- **No user data transmission**
- **Local processing only**

---

## 🌟 **Global Benefits**

### **✅ For Travelers:**
- Automatic location updates as you travel
- Local weather wherever you are
- Regional news for your current location
- No manual reconfiguration needed

### **✅ For Remote Workers:**
- Works from any country
- Local timezone awareness
- Regional news and weather
- Consistent experience worldwide

### **✅ For Global Teams:**
- Same AI assistant everywhere
- Localized information per team member
- No region-specific setup required
- Universal deployment

---

## 📋 **Requirements**

### **System Requirements:**
- **OS**: Linux, macOS, Windows
- **Python**: 3.8+
- **Internet**: Required for location/weather/news
- **Dependencies**: Listed in requirements.txt

### **Global Compatibility:**
- **Works in any country** with internet access
- **No VPN restrictions**
- **No region-specific APIs** required
- **Universal timezone support**

---

## 🤝 **Contributing**

### **Adding Global Support:**
1. Fork the repository
2. Add your region to timezone/country mappings
3. Test with your local setup
4. Submit pull request

### **Reporting Issues:**
- Include your country/region
- Specify location detection accuracy
- Mention timezone issues if any

---

## 📞 **Global Support**

### **Common Issues:**
- **Inaccurate location**: Enable manual override
- **Wrong timezone**: Check country name format
- **News not relevant**: Use region-specific commands

### **Global Community:**
- **GitHub Issues**: For technical problems
- **Discussions**: For feature requests
- **Wiki**: For regional setup guides

---

## 🎯 **Roadmap**

### **Upcoming Global Features:**
- [ ] Multi-language support
- [ ] Currency conversion
- [ ] Local business information
- [ ] Cultural event awareness
- [ ] Regional holiday detection
- [ ] Local emergency services info

---

**WavesAI: Your intelligent assistant, anywhere in the world** 🌍

*Clone once, run everywhere - with automatic location awareness and global intelligence.*
