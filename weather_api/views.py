# weather_api/views.py
from django.shortcuts import render, redirect
import requests
from datetime import datetime

def index(request):
    return render(request, "weather_api/home.html")

def result(request):
    if request.method != "POST":
        return redirect("home")

    city = request.POST.get("city", "").strip()
    if not city:
        return redirect("home")

    # Clean autocomplete strings (e.g., "Bangalore, IN" becomes "Bangalore")
    if "," in city:
        city = city.split(",")[0].strip()

    # Active API Key configuration
    api_key = "6669059a0f1b90a8c107dd7b591b0071"
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    
    context = {}

    try:
        response = requests.get(url, timeout=5)
        
        # Catch key activation (401) or location missing errors (404) safely
        if response.status_code == 401:
            context["error_state"] = True
            context["error_message"] = "Security Handshake Refused: New API Key is still activating on OpenWeather servers. Please wait a few minutes."
            return render(request, "weather_api/results.html", context)
        elif response.status_code == 404:
            context["error_state"] = True
            context["error_message"] = f"Sector '{city}' not recognized on global grids."
            return render(request, "weather_api/results.html", context)
            
        response.raise_for_status()
        data = response.json()

        # -------------------------
        # CURRENT WEATHER DATA
        # -------------------------
        now = data["list"][0]
        current = {
            "temp": round(now["main"]["temp"]),
            "humidity": now["main"]["humidity"],
            "wind": now["wind"]["speed"],
            "description": now["weather"][0]["description"].title(),
            "icon": now["weather"][0]["icon"],
            "date": datetime.now().strftime("%A, %d %B %Y"),
            "weather_main": now["weather"][0]["main"],
            "pressure": now["main"].get("pressure", "N/A"), 
            "visibility": round(now.get("visibility", 0) / 1000), 
        }

        # -------------------------
        # FORECAST DATA AGGREGATION
        # -------------------------
        daily = {}
        days_order = []

        for entry in data["list"]:
            day = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S").strftime("%A")
            temp_min = entry["main"]["temp_min"]
            temp_max = entry["main"]["temp_max"]
            icon = entry["weather"][0]["icon"]
            desc = entry["weather"][0]["description"].title()

            if day not in daily:
                days_order.append(day)
                daily[day] = {
                    "min": temp_min,
                    "max": temp_max,
                    "icon": icon,
                    "description": desc
                }
            else:
                daily[day]["min"] = min(daily[day]["min"], temp_min)
                daily[day]["max"] = max(daily[day]["max"], temp_max)
                if "d" in icon:
                    daily[day]["icon"] = icon
                    daily[day]["description"] = desc

        forecast_list = []
        for d in days_order:
            forecast_list.append({
                "day": d,
                "min": round(daily[d]["min"]),
                "max": round(daily[d]["max"]),
                "icon": daily[d]["icon"],
                "description": daily[d]["description"]
            })

        context = {
            "city_name": data["city"]["name"],
            "city_country": data["city"]["country"],
            "current": current,
            "forecast": forecast_list,
            "error_state": False
        }

    except Exception as e:
        context["error_state"] = True
        context["error_message"] = f"Internal Matrix Malfunction. System error: {e}"

    return render(request, "weather_api/results.html", context)