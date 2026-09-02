"""
Weather Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ....application.ports.external_services import WeatherServicePort
from ....domain.entities.weather import WeatherAlert, WeatherForecast
from ....domain.value_objects.coordinates import Coordinates


@dataclass
class CurrentWeatherData:
    """Current weather data"""
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    wind_speed: float
    wind_direction: int
    weather_code: int
    weather_description: str
    visibility: float
    uv_index: float | None
    timestamp: datetime


@dataclass
class ForecastData:
    """Forecast data"""
    latitude: float
    longitude: float
    timezone: str
    current: CurrentWeatherData
    hourly: list[dict[str, Any]]
    daily: list[dict[str, Any]]


class BaseWeatherAdapter(WeatherServicePort, ABC):
    """Base weather adapter"""

    @abstractmethod
    async def _get_current_weather_request(self, coordinates: Coordinates) -> CurrentWeatherData | None:
        """Get current weather request"""
        pass

    @abstractmethod
    async def _get_forecast_request(
        self,
        coordinates: Coordinates,
        days: int,
        hourly: bool,
    ) -> ForecastData | None:
        """Get forecast request"""
        pass

    @abstractmethod
    async def _get_alerts_request(self, coordinates: Coordinates) -> list[WeatherAlert]:
        """Get alerts request"""
        pass

    @abstractmethod
    async def _get_historical_request(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get historical weather request"""
        pass

    async def get_current_weather(self, coordinates: Coordinates) -> dict[str, Any] | None:
        """Get current weather"""
        data = await self._get_current_weather_request(coordinates)
        if data:
            return {
                "temperature": data.temperature,
                "feels_like": data.feels_like,
                "humidity": data.humidity,
                "pressure": data.pressure,
                "wind_speed": data.wind_speed,
                "wind_direction": data.wind_direction,
                "weather_code": data.weather_code,
                "weather_description": data.weather_description,
                "visibility": data.visibility,
                "uv_index": data.uv_index,
                "timestamp": data.timestamp.isoformat(),
            }
        return None

    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        hourly: bool = True,
    ) -> WeatherForecast | None:
        """Get weather forecast"""
        data = await self._get_forecast_request(coordinates, days, hourly)
        if data:
            # Convert to WeatherForecast entity
            return WeatherForecast(
                latitude=data.latitude,
                longitude=data.longitude,
                timezone=data.timezone,
                current=data.current,
                hourly=data.hourly,
                daily=data.daily,
            )
        return None

    async def get_alerts(self, coordinates: Coordinates) -> list[WeatherAlert]:
        """Get weather alerts"""
        return await self._get_alerts_request(coordinates)

    async def get_historical(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get historical weather"""
        return await self._get_historical_request(coordinates, start_date, end_date)


class OpenMeteoAdapter(BaseWeatherAdapter):
    """Open-Meteo weather API adapter (free, no API key required)"""

    def __init__(self, base_url: str = "https://api.open-meteo.com/v1"):
        self.base_url = base_url
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_current_weather_request(self, coordinates: Coordinates) -> CurrentWeatherData | None:
        session = await self._get_session()

        url = f"{self.base_url}/forecast"
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "current_weather": "true",
            "timezone": "auto",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                current = data.get("current_weather", {})
                return CurrentWeatherData(
                    temperature=current.get("temperature", 0),
                    feels_like=current.get("temperature", 0),  # Open-Meteo doesn't provide feels_like
                    humidity=0,  # Not in current_weather
                    pressure=0,  # Not in current_weather
                    wind_speed=current.get("windspeed", 0),
                    wind_direction=current.get("winddirection", 0),
                    weather_code=current.get("weathercode", 0),
                    weather_description=self._weather_code_to_description(current.get("weathercode", 0)),
                    visibility=0,
                    uv_index=None,
                    timestamp=datetime.fromisoformat(current.get("time", datetime.utcnow().isoformat())),
                )
        return None

    async def _get_forecast_request(
        self,
        coordinates: Coordinates,
        days: int,
        hourly: bool,
    ) -> ForecastData | None:
        session = await self._get_session()

        url = f"{self.base_url}/forecast"
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,windspeed_10m_max,uv_index_max,sunrise,sunset",
            "timezone": "auto",
            "forecast_days": min(days, 16),
        }

        if hourly:
            params["hourly"] = "temperature_2m,relativehumidity_2m,precipitation_probability,precipitation,weathercode,windspeed_10m,winddirection_10m,uv_index"

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                # Build current weather from first hourly entry
                current = None
                if hourly and "hourly" in data:
                    hourly_data = data["hourly"]
                    if hourly_data.get("time"):
                        idx = 0
                        current = CurrentWeatherData(
                            temperature=hourly_data["temperature_2m"][idx],
                            feels_like=hourly_data["temperature_2m"][idx],
                            humidity=hourly_data["relativehumidity_2m"][idx],
                            pressure=0,
                            wind_speed=hourly_data["windspeed_10m"][idx],
                            wind_direction=hourly_data["winddirection_10m"][idx],
                            weather_code=hourly_data["weathercode"][idx],
                            weather_description=self._weather_code_to_description(hourly_data["weathercode"][idx]),
                            visibility=0,
                            uv_index=hourly_data.get("uv_index", [None])[idx],
                            timestamp=datetime.fromisoformat(hourly_data["time"][idx]),
                        )

                # Build hourly forecast
                hourly_forecast = []
                if hourly and "hourly" in data:
                    hourly_data = data["hourly"]
                    times = hourly_data.get("time", [])
                    for i, time_str in enumerate(times[:48]):  # 48 hours
                        hourly_forecast.append({
                            "time": time_str,
                            "temperature": hourly_data["temperature_2m"][i],
                            "feels_like": hourly_data["temperature_2m"][i],
                            "humidity": hourly_data["relativehumidity_2m"][i],
                            "precipitation_probability": hourly_data["precipitation_probability"][i],
                            "precipitation": hourly_data["precipitation"][i],
                            "weather_code": hourly_data["weathercode"][i],
                            "weather_description": self._weather_code_to_description(hourly_data["weathercode"][i]),
                            "wind_speed": hourly_data["windspeed_10m"][i],
                            "wind_direction": hourly_data["winddirection_10m"][i],
                            "uv_index": hourly_data.get("uv_index", [None])[i],
                        })

                # Build daily forecast
                daily_forecast = []
                if "daily" in data:
                    daily_data = data["daily"]
                    times = daily_data.get("time", [])
                    for i, date_str in enumerate(times):
                        daily_forecast.append({
                            "date": date_str,
                            "temperature_max": daily_data["temperature_2m_max"][i],
                            "temperature_min": daily_data["temperature_2m_min"][i],
                            "feels_like_max": daily_data["temperature_2m_max"][i],
                            "feels_like_min": daily_data["temperature_2m_min"][i],
                            "humidity_max": 0,
                            "humidity_min": 0,
                            "precipitation_probability": daily_data["precipitation_probability_max"][i],
                            "precipitation": daily_data["precipitation_sum"][i],
                            "weather_code": daily_data["weathercode"][i],
                            "weather_description": self._weather_code_to_description(daily_data["weathercode"][i]),
                            "wind_speed_max": daily_data["windspeed_10m_max"][i],
                            "uv_index_max": daily_data.get("uv_index_max", [None])[i],
                            "sunrise": daily_data["sunrise"][i],
                            "sunset": daily_data["sunset"][i],
                        })

                return ForecastData(
                    latitude=coordinates.latitude,
                    longitude=coordinates.longitude,
                    timezone=data.get("timezone", "UTC"),
                    current=current or CurrentWeatherData(
                        temperature=0, feels_like=0, humidity=0, pressure=0,
                        wind_speed=0, wind_direction=0, weather_code=0,
                        weather_description="", visibility=0, uv_index=None,
                        timestamp=datetime.utcnow()
                    ),
                    hourly=hourly_forecast,
                    daily=daily_forecast,
                )
        return None

    async def _get_alerts_request(self, coordinates: Coordinates) -> list[WeatherAlert]:
        # Open-Meteo doesn't provide alerts
        return []

    async def _get_historical_request(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        session = await self._get_session()

        url = f"{self.base_url}/forecast"
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                historical = []
                if "daily" in data:
                    daily_data = data["daily"]
                    times = daily_data.get("time", [])
                    for i, date_str in enumerate(times):
                        historical.append({
                            "date": date_str,
                            "temperature_max": daily_data["temperature_2m_max"][i],
                            "temperature_min": daily_data["temperature_2m_min"][i],
                            "temperature_avg": (daily_data["temperature_2m_max"][i] + daily_data["temperature_2m_min"][i]) / 2,
                            "precipitation": daily_data["precipitation_sum"][i],
                            "weather_code": daily_data["weathercode"][i],
                            "weather_description": self._weather_code_to_description(daily_data["weathercode"][i]),
                        })
                return historical
        return []

    def _weather_code_to_description(self, code: int) -> str:
        """Convert WMO weather code to description"""
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return codes.get(code, "Unknown")

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class OpenWeatherMapAdapter(BaseWeatherAdapter):
    """OpenWeatherMap API adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_current_weather_request(self, coordinates: Coordinates) -> CurrentWeatherData | None:
        session = await self._get_session()

        url = f"{self.base_url}/weather"
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "appid": self.api_key,
            "units": "metric",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                main = data.get("main", {})
                wind = data.get("wind", {})
                weather = data.get("weather", [{}])[0]

                return CurrentWeatherData(
                    temperature=main.get("temp", 0),
                    feels_like=main.get("feels_like", 0),
                    humidity=main.get("humidity", 0),
                    pressure=main.get("pressure", 0),
                    wind_speed=wind.get("speed", 0),
                    wind_direction=wind.get("deg", 0),
                    weather_code=weather.get("id", 0),
                    weather_description=weather.get("description", ""),
                    visibility=data.get("visibility", 0) / 1000,  # Convert to km
                    uv_index=None,
                    timestamp=datetime.fromtimestamp(data.get("dt", 0)),
                )
        return None

    async def _get_forecast_request(
        self,
        coordinates: Coordinates,
        days: int,
        hourly: bool,
    ) -> ForecastData | None:
        session = await self._get_session()

        url = f"{self.base_url}/forecast"
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "appid": self.api_key,
            "units": "metric",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                # Process 3-hourly forecast into daily
                daily_forecast = []
                hourly_forecast = []

                # Group by day
                from collections import defaultdict
                daily_groups = defaultdict(list)

                for item in data.get("list", []):
                    dt = datetime.fromtimestamp(item["dt"])
                    date_key = dt.date().isoformat()
                    daily_groups[date_key].append(item)

                    if hourly:
                        main = item.get("main", {})
                        wind = item.get("wind", {})
                        weather = item.get("weather", [{}])[0]
                        hourly_forecast.append({
                            "time": dt.isoformat(),
                            "temperature": main.get("temp", 0),
                            "feels_like": main.get("feels_like", 0),
                            "humidity": main.get("humidity", 0),
                            "precipitation_probability": int(item.get("pop", 0) * 100),
                            "precipitation": item.get("rain", {}).get("3h", 0) + item.get("snow", {}).get("3h", 0),
                            "weather_code": weather.get("id", 0),
                            "weather_description": weather.get("description", ""),
                            "wind_speed": wind.get("speed", 0),
                            "wind_direction": wind.get("deg", 0),
                            "uv_index": None,
                        })

                # Build daily forecast
                for date_str, items in list(daily_groups.items())[:days]:
                    temps = [i["main"]["temp"] for i in items]
                    humidity = [i["main"]["humidity"] for i in items]
                    pop = max([i.get("pop", 0) for i in items])
                    rain = sum([i.get("rain", {}).get("3h", 0) for i in items])
                    snow = sum([i.get("snow", {}).get("3h", 0) for i in items])
                    weather = items[0].get("weather", [{}])[0]

                    daily_forecast.append({
                        "date": date_str,
                        "temperature_max": max(temps),
                        "temperature_min": min(temps),
                        "feels_like_max": max([i["main"]["feels_like"] for i in items]),
                        "feels_like_min": min([i["main"]["feels_like"] for i in items]),
                        "humidity_max": max(humidity),
                        "humidity_min": min(humidity),
                        "precipitation_probability": int(pop * 100),
                        "precipitation": rain + snow,
                        "weather_code": weather.get("id", 0),
                        "weather_description": weather.get("description", ""),
                        "wind_speed_max": max([i["wind"]["speed"] for i in items]),
                        "uv_index_max": None,
                        "sunrise": "",
                        "sunset": "",
                    })

                # Current from first hourly
                current = None
                if hourly_forecast:
                    h = hourly_forecast[0]
                    current = CurrentWeatherData(
                        temperature=h["temperature"],
                        feels_like=h["feels_like"],
                        humidity=h["humidity"],
                        pressure=0,
                        wind_speed=h["wind_speed"],
                        wind_direction=h["wind_direction"],
                        weather_code=h["weather_code"],
                        weather_description=h["weather_description"],
                        visibility=0,
                        uv_index=None,
                        timestamp=datetime.fromisoformat(h["time"]),
                    )

                return ForecastData(
                    latitude=coordinates.latitude,
                    longitude=coordinates.longitude,
                    timezone=data.get("city", {}).get("timezone", "UTC"),
                    current=current or CurrentWeatherData(
                        temperature=0, feels_like=0, humidity=0, pressure=0,
                        wind_speed=0, wind_direction=0, weather_code=0,
                        weather_description="", visibility=0, uv_index=None,
                        timestamp=datetime.utcnow()
                    ),
                    hourly=hourly_forecast,
                    daily=daily_forecast,
                )
        return None

    async def _get_alerts_request(self, coordinates: Coordinates) -> list[WeatherAlert]:
        session = await self._get_session()

        url = f"{self.base_url}/onecall"
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "appid": self.api_key,
            "exclude": "current,minutely,hourly,daily",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                alerts = []
                for alert in data.get("alerts", []):
                    alerts.append(WeatherAlert(
                        id=alert.get("event", ""),
                        event=alert.get("event", ""),
                        severity=alert.get("severity", ""),
                        urgency=alert.get("urgency", ""),
                        certainty=alert.get("certainty", ""),
                        effective=datetime.fromtimestamp(alert.get("start", 0)),
                        expires=datetime.fromtimestamp(alert.get("end", 0)),
                        description=alert.get("description", ""),
                        instruction=alert.get("instruction"),
                        areas=[],  # Not provided
                    ))
                return alerts
        return []

    async def _get_historical_request(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        # OpenWeatherMap historical requires paid plan
        return []

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class WeatherAPIAdapter(BaseWeatherAdapter):
    """WeatherAPI.com adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.weatherapi.com/v1"
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_current_weather_request(self, coordinates: Coordinates) -> CurrentWeatherData | None:
        session = await self._get_session()

        url = f"{self.base_url}/current.json"
        params = {
            "key": self.api_key,
            "q": f"{coordinates.latitude},{coordinates.longitude}",
            "aqi": "no",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                current = data.get("current", {})
                condition = current.get("condition", {})

                return CurrentWeatherData(
                    temperature=current.get("temp_c", 0),
                    feels_like=current.get("feelslike_c", 0),
                    humidity=current.get("humidity", 0),
                    pressure=current.get("pressure_mb", 0),
                    wind_speed=current.get("wind_kph", 0) / 3.6,  # Convert to m/s
                    wind_direction=current.get("wind_degree", 0),
                    weather_code=condition.get("code", 0),
                    weather_description=condition.get("text", ""),
                    visibility=current.get("vis_km", 0),
                    uv_index=current.get("uv"),
                    timestamp=datetime.fromisoformat(current.get("last_updated", "").replace(" ", "T")),
                )
        return None

    async def _get_forecast_request(
        self,
        coordinates: Coordinates,
        days: int,
        hourly: bool,
    ) -> ForecastData | None:
        session = await self._get_session()

        url = f"{self.base_url}/forecast.json"
        params = {
            "key": self.api_key,
            "q": f"{coordinates.latitude},{coordinates.longitude}",
            "days": min(days, 10),
            "aqi": "no",
            "alerts": "no",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                current_data = data.get("current", {})
                condition = current_data.get("condition", {})
                current = CurrentWeatherData(
                    temperature=current_data.get("temp_c", 0),
                    feels_like=current_data.get("feelslike_c", 0),
                    humidity=current_data.get("humidity", 0),
                    pressure=current_data.get("pressure_mb", 0),
                    wind_speed=current_data.get("wind_kph", 0) / 3.6,
                    wind_direction=current_data.get("wind_degree", 0),
                    weather_code=condition.get("code", 0),
                    weather_description=condition.get("text", ""),
                    visibility=current_data.get("vis_km", 0),
                    uv_index=current_data.get("uv"),
                    timestamp=datetime.fromisoformat(current_data.get("last_updated", "").replace(" ", "T")),
                )

                hourly_forecast = []
                daily_forecast = []

                for day in data.get("forecast", {}).get("forecastday", []):
                    date_str = day.get("date", "")
                    day_data = day.get("day", {})
                    day_condition = day_data.get("condition", {})

                    daily_forecast.append({
                        "date": date_str,
                        "temperature_max": day_data.get("maxtemp_c", 0),
                        "temperature_min": day_data.get("mintemp_c", 0),
                        "feels_like_max": day_data.get("maxtemp_c", 0),
                        "feels_like_min": day_data.get("mintemp_c", 0),
                        "humidity_max": 0,
                        "humidity_min": 0,
                        "precipitation_probability": day_data.get("daily_chance_of_rain", 0),
                        "precipitation": day_data.get("totalprecip_mm", 0),
                        "weather_code": day_condition.get("code", 0),
                        "weather_description": day_condition.get("text", ""),
                        "wind_speed_max": day_data.get("maxwind_kph", 0) / 3.6,
                        "uv_index_max": day_data.get("uv", 0),
                        "sunrise": day.get("astro", {}).get("sunrise", ""),
                        "sunset": day.get("astro", {}).get("sunset", ""),
                    })

                    if hourly:
                        for hour in day.get("hour", []):
                            hour_condition = hour.get("condition", {})
                            hourly_forecast.append({
                                "time": hour.get("time", "").replace(" ", "T"),
                                "temperature": hour.get("temp_c", 0),
                                "feels_like": hour.get("feelslike_c", 0),
                                "humidity": hour.get("humidity", 0),
                                "precipitation_probability": hour.get("chance_of_rain", 0),
                                "precipitation": hour.get("precip_mm", 0),
                                "weather_code": hour_condition.get("code", 0),
                                "weather_description": hour_condition.get("text", ""),
                                "wind_speed": hour.get("wind_kph", 0) / 3.6,
                                "wind_direction": hour.get("wind_degree", 0),
                                "uv_index": hour.get("uv"),
                            })

                return ForecastData(
                    latitude=coordinates.latitude,
                    longitude=coordinates.longitude,
                    timezone=data.get("location", {}).get("tz_id", "UTC"),
                    current=current,
                    hourly=hourly_forecast,
                    daily=daily_forecast,
                )
        return None

    async def _get_alerts_request(self, coordinates: Coordinates) -> list[WeatherAlert]:
        session = await self._get_session()

        url = f"{self.base_url}/forecast.json"
        params = {
            "key": self.api_key,
            "q": f"{coordinates.latitude},{coordinates.longitude}",
            "days": 1,
            "aqi": "no",
            "alerts": "yes",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                alerts = []
                for alert in data.get("alerts", {}).get("alert", []):
                    alerts.append(WeatherAlert(
                        id=alert.get("event", ""),
                        event=alert.get("event", ""),
                        severity=alert.get("severity", ""),
                        urgency=alert.get("urgency", ""),
                        certainty=alert.get("certainty", ""),
                        effective=datetime.fromisoformat(alert.get("effective", "").replace(" ", "T")),
                        expires=datetime.fromisoformat(alert.get("expires", "").replace(" ", "T")),
                        description=alert.get("desc", ""),
                        instruction=alert.get("instruction"),
                        areas=alert.get("areas", []),
                    ))
                return alerts
        return []

    async def _get_historical_request(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        session = await self._get_session()

        historical = []
        current_date = start_date
        while current_date <= end_date:
            url = f"{self.base_url}/history.json"
            params = {
                "key": self.api_key,
                "q": f"{coordinates.latitude},{coordinates.longitude}",
                "dt": current_date.date().isoformat(),
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    day = data.get("forecast", {}).get("forecastday", [{}])[0]
                    day_data = day.get("day", {})
                    condition = day_data.get("condition", {})

                    historical.append({
                        "date": current_date.date().isoformat(),
                        "temperature_max": day_data.get("maxtemp_c", 0),
                        "temperature_min": day_data.get("mintemp_c", 0),
                        "temperature_avg": day_data.get("avgtemp_c", 0),
                        "precipitation": day_data.get("totalprecip_mm", 0),
                        "weather_code": condition.get("code", 0),
                        "weather_description": condition.get("text", ""),
                    })

            current_date += timedelta(days=1)

        return historical

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
