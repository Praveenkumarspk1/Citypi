"""
SQLAlchemy Weather Models
"""
from datetime import date, datetime

from ai_smart_city_concierge.domain.entities.weather import (
    PrecipitationType,
    WeatherAlert,
    WeatherCondition,
    WeatherCurrent,
    WeatherDaily,
    WeatherForecast,
    WeatherHourly,
    WeatherSeverity,
)
from ai_smart_city_concierge.infrastructure.config.database import Base
from sqlalchemy import JSON, Column, Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy import Enum as SQLEnum


class WeatherCurrentModel(Base):
    """SQLAlchemy model for Current Weather"""
    __tablename__ = "weather_current"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Temperature
    temperature = Column(Float, default=0.0, nullable=False)
    feels_like = Column(Float, default=0.0, nullable=False)
    dew_point = Column(Float, default=0.0, nullable=False)

    # Humidity & Pressure
    humidity = Column(Integer, default=0, nullable=False)
    pressure = Column(Float, default=0.0, nullable=False)

    # Wind
    wind_speed = Column(Float, default=0.0, nullable=False)
    wind_direction = Column(Integer, default=0, nullable=False)
    wind_gust = Column(Float, nullable=True)

    # Conditions
    condition = Column(SQLEnum(WeatherCondition), default=WeatherCondition.UNKNOWN, nullable=False)
    condition_description = Column(String(255), default="", nullable=False)
    cloud_cover = Column(Integer, default=0, nullable=False)
    visibility = Column(Float, default=0.0, nullable=False)

    # Precipitation
    precipitation = Column(Float, default=0.0, nullable=False)
    precipitation_type = Column(SQLEnum(PrecipitationType), default=PrecipitationType.NONE, nullable=False)
    precipitation_probability = Column(Integer, default=0, nullable=False)

    # UV & Solar
    uv_index = Column(Float, default=0.0, nullable=False)
    solar_radiation = Column(Float, default=0.0, nullable=False)

    # Air Quality
    air_quality_index = Column(Integer, nullable=True)
    pm25 = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    o3 = Column(Float, nullable=True)
    no2 = Column(Float, nullable=True)
    so2 = Column(Float, nullable=True)
    co = Column(Float, nullable=True)

    # Source
    source = Column(String(50), default="open-meteo", nullable=False)
    raw_data = Column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index('ix_weather_current_location_time', 'latitude', 'longitude', 'timestamp'),
    )

    def to_entity(self):
        from ....domain.value_objects.coordinates import Coordinates
        return WeatherCurrent(
            coordinates=Coordinates(latitude=self.latitude, longitude=self.longitude),
            timestamp=self.timestamp,
            temperature=self.temperature,
            feels_like=self.feels_like,
            dew_point=self.dew_point,
            humidity=self.humidity,
            pressure=self.pressure,
            wind_speed=self.wind_speed,
            wind_direction=self.wind_direction,
            wind_gust=self.wind_gust,
            condition=self.condition,
            condition_description=self.condition_description,
            cloud_cover=self.cloud_cover,
            visibility=self.visibility,
            precipitation=self.precipitation,
            precipitation_type=self.precipitation_type,
            precipitation_probability=self.precipitation_probability,
            uv_index=self.uv_index,
            solar_radiation=self.solar_radiation,
            air_quality_index=self.air_quality_index,
            pm25=self.pm25,
            pm10=self.pm10,
            o3=self.o3,
            no2=self.no2,
            so2=self.so2,
            co=self.co,
            source=self.source,
            raw_data=self.raw_data,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            latitude=entity.coordinates.latitude,
            longitude=entity.coordinates.longitude,
            timestamp=entity.timestamp,
            temperature=entity.temperature,
            feels_like=entity.feels_like,
            dew_point=entity.dew_point,
            humidity=entity.humidity,
            pressure=entity.pressure,
            wind_speed=entity.wind_speed,
            wind_direction=entity.wind_direction,
            wind_gust=entity.wind_gust,
            condition=entity.condition,
            condition_description=entity.condition_description,
            cloud_cover=entity.cloud_cover,
            visibility=entity.visibility,
            precipitation=entity.precipitation,
            precipitation_type=entity.precipitation_type,
            precipitation_probability=entity.precipitation_probability,
            uv_index=entity.uv_index,
            solar_radiation=entity.solar_radiation,
            air_quality_index=entity.air_quality_index,
            pm25=entity.pm25,
            pm10=entity.pm10,
            o3=entity.o3,
            no2=entity.no2,
            so2=entity.so2,
            co=entity.co,
            source=entity.source,
            raw_data=entity.raw_data,
        )


class WeatherHourlyModel(Base):
    """SQLAlchemy model for Hourly Weather Forecast"""
    __tablename__ = "weather_hourly"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Temperature
    temperature = Column(Float, default=0.0, nullable=False)
    feels_like = Column(Float, default=0.0, nullable=False)
    dew_point = Column(Float, default=0.0, nullable=False)

    # Humidity & Pressure
    humidity = Column(Integer, default=0, nullable=False)
    pressure = Column(Float, default=0.0, nullable=False)

    # Wind
    wind_speed = Column(Float, default=0.0, nullable=False)
    wind_direction = Column(Integer, default=0, nullable=False)
    wind_gust = Column(Float, nullable=True)

    # Conditions
    condition = Column(SQLEnum(WeatherCondition), default=WeatherCondition.UNKNOWN, nullable=False)
    condition_description = Column(String(255), default="", nullable=False)
    cloud_cover = Column(Integer, default=0, nullable=False)
    visibility = Column(Float, default=0.0, nullable=False)

    # Precipitation
    precipitation = Column(Float, default=0.0, nullable=False)
    precipitation_type = Column(SQLEnum(PrecipitationType), default=PrecipitationType.NONE, nullable=False)
    precipitation_probability = Column(Integer, default=0, nullable=False)

    # UV
    uv_index = Column(Float, default=0.0, nullable=False)

    __table_args__ = (
        Index('ix_weather_hourly_location_time', 'latitude', 'longitude', 'timestamp'),
    )

    def to_entity(self):
        return WeatherHourly(
            timestamp=self.timestamp,
            temperature=self.temperature,
            feels_like=self.feels_like,
            dew_point=self.dew_point,
            humidity=self.humidity,
            pressure=self.pressure,
            wind_speed=self.wind_speed,
            wind_direction=self.wind_direction,
            wind_gust=self.wind_gust,
            condition=self.condition,
            condition_description=self.condition_description,
            cloud_cover=self.cloud_cover,
            visibility=self.visibility,
            precipitation=self.precipitation,
            precipitation_type=self.precipitation_type,
            precipitation_probability=self.precipitation_probability,
            uv_index=self.uv_index,
        )

    @classmethod
    def from_entity(cls, entity, latitude, longitude):
        return cls(
            latitude=latitude,
            longitude=longitude,
            timestamp=entity.timestamp,
            temperature=entity.temperature,
            feels_like=entity.feels_like,
            dew_point=entity.dew_point,
            humidity=entity.humidity,
            pressure=entity.pressure,
            wind_speed=entity.wind_speed,
            wind_direction=entity.wind_direction,
            wind_gust=entity.wind_gust,
            condition=entity.condition,
            condition_description=entity.condition_description,
            cloud_cover=entity.cloud_cover,
            visibility=entity.visibility,
            precipitation=entity.precipitation,
            precipitation_type=entity.precipitation_type,
            precipitation_probability=entity.precipitation_probability,
            uv_index=entity.uv_index,
        )


class WeatherDailyModel(Base):
    """SQLAlchemy model for Daily Weather Forecast"""
    __tablename__ = "weather_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    forecast_date = Column(Date, nullable=False, index=True)

    # Temperature
    temperature_min = Column(Float, default=0.0, nullable=False)
    temperature_max = Column(Float, default=0.0, nullable=False)
    temperature_morning = Column(Float, default=0.0, nullable=False)
    temperature_noon = Column(Float, default=0.0, nullable=False)
    temperature_evening = Column(Float, default=0.0, nullable=False)
    temperature_night = Column(Float, default=0.0, nullable=False)

    # Feels like
    feels_like_min = Column(Float, default=0.0, nullable=False)
    feels_like_max = Column(Float, default=0.0, nullable=False)

    # Sun
    sunrise = Column(DateTime, nullable=True)
    sunset = Column(DateTime, nullable=True)
    daylight_duration = Column(Float, default=0.0, nullable=False)
    sunshine_duration = Column(Float, default=0.0, nullable=False)

    # Conditions
    condition = Column(SQLEnum(WeatherCondition), default=WeatherCondition.UNKNOWN, nullable=False)
    condition_description = Column(String(255), default="", nullable=False)

    # Precipitation
    precipitation_sum = Column(Float, default=0.0, nullable=False)
    precipitation_probability_max = Column(Integer, default=0, nullable=False)
    precipitation_hours = Column(Float, default=0.0, nullable=False)
    precipitation_type = Column(SQLEnum(PrecipitationType), default=PrecipitationType.NONE, nullable=False)

    # Wind
    wind_speed_max = Column(Float, default=0.0, nullable=False)
    wind_gust_max = Column(Float, nullable=True)
    wind_direction_dominant = Column(Integer, default=0, nullable=False)

    # UV
    uv_index_max = Column(Float, default=0.0, nullable=False)
    uv_index_clear_sky_max = Column(Float, default=0.0, nullable=False)

    # Other
    humidity_mean = Column(Integer, default=0, nullable=False)
    pressure_mean = Column(Float, default=0.0, nullable=False)
    cloud_cover_mean = Column(Integer, default=0, nullable=False)
    visibility_mean = Column(Float, default=0.0, nullable=False)

    # Hourly breakdown (stored as JSON)
    hourly = Column(JSON, default=list, nullable=False)

    __table_args__ = (
        Index('ix_weather_daily_location_date', 'latitude', 'longitude', 'forecast_date'),
    )

    def to_entity(self):
        return WeatherDaily(
            date=self.forecast_date,
            temperature_min=self.temperature_min,
            temperature_max=self.temperature_max,
            temperature_morning=self.temperature_morning,
            temperature_noon=self.temperature_noon,
            temperature_evening=self.temperature_evening,
            temperature_night=self.temperature_night,
            feels_like_min=self.feels_like_min,
            feels_like_max=self.feels_like_max,
            sunrise=self.sunrise,
            sunset=self.sunset,
            daylight_duration=self.daylight_duration,
            sunshine_duration=self.sunshine_duration,
            condition=self.condition,
            condition_description=self.condition_description,
            precipitation_sum=self.precipitation_sum,
            precipitation_probability_max=self.precipitation_probability_max,
            precipitation_hours=self.precipitation_hours,
            precipitation_type=self.precipitation_type,
            wind_speed_max=self.wind_speed_max,
            wind_gust_max=self.wind_gust_max,
            wind_direction_dominant=self.wind_direction_dominant,
            uv_index_max=self.uv_index_max,
            uv_index_clear_sky_max=self.uv_index_clear_sky_max,
            humidity_mean=self.humidity_mean,
            pressure_mean=self.pressure_mean,
            cloud_cover_mean=self.cloud_cover_mean,
            visibility_mean=self.visibility_mean,
            hourly=[WeatherHourlyModel.from_dict(h) for h in self.hourly],
        )

    @classmethod
    def from_entity(cls, entity, latitude, longitude):
        return cls(
            latitude=latitude,
            longitude=longitude,
            forecast_date=entity.date,
            temperature_min=entity.temperature_min,
            temperature_max=entity.temperature_max,
            temperature_morning=entity.temperature_morning,
            temperature_noon=entity.temperature_noon,
            temperature_evening=entity.temperature_evening,
            temperature_night=entity.temperature_night,
            feels_like_min=entity.feels_like_min,
            feels_like_max=entity.feels_like_max,
            sunrise=entity.sunrise,
            sunset=entity.sunset,
            daylight_duration=entity.daylight_duration,
            sunshine_duration=entity.sunshine_duration,
            condition=entity.condition,
            condition_description=entity.condition_description,
            precipitation_sum=entity.precipitation_sum,
            precipitation_probability_max=entity.precipitation_probability_max,
            precipitation_hours=entity.precipitation_hours,
            precipitation_type=entity.precipitation_type,
            wind_speed_max=entity.wind_speed_max,
            wind_gust_max=entity.wind_gust_max,
            wind_direction_dominant=entity.wind_direction_dominant,
            uv_index_max=entity.uv_index_max,
            uv_index_clear_sky_max=entity.uv_index_clear_sky_max,
            humidity_mean=entity.humidity_mean,
            pressure_mean=entity.pressure_mean,
            cloud_cover_mean=entity.cloud_cover_mean,
            visibility_mean=entity.visibility_mean,
            hourly=[h.to_dict() for h in entity.hourly],
        )


class WeatherAlertModel(Base):
    """SQLAlchemy model for Weather Alert"""
    __tablename__ = "weather_alerts"

    id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(WeatherSeverity), default=WeatherSeverity.NONE, nullable=False)
    certainty = Column(String(50), default="unknown", nullable=False)
    urgency = Column(String(50), default="unknown", nullable=False)
    event = Column(String(100), nullable=False)
    effective = Column(DateTime, nullable=True)
    expires = Column(DateTime, nullable=True)
    sender = Column(String(255), nullable=False)
    areas = Column(JSON, default=list, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source = Column(String(50), default="open-meteo", nullable=False)

    def to_entity(self):
        from ....domain.value_objects.coordinates import Coordinates
        return WeatherAlert(
            id=self.id,
            title=self.title,
            description=self.description,
            severity=self.severity,
            certainty=self.certainty,
            urgency=self.urgency,
            event=self.event,
            effective=self.effective,
            expires=self.expires,
            sender=self.sender,
            areas=self.areas,
            coordinates=Coordinates(latitude=self.latitude, longitude=self.longitude) if self.latitude and self.longitude else None,
            source=self.source,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            severity=entity.severity,
            certainty=entity.certainty,
            urgency=entity.urgency,
            event=entity.event,
            effective=entity.effective,
            expires=entity.expires,
            sender=entity.sender,
            areas=entity.areas,
            latitude=entity.coordinates.latitude if entity.coordinates else None,
            longitude=entity.coordinates.longitude if entity.coordinates else None,
            source=entity.source,
        )


class WeatherForecastModel(Base):
    """SQLAlchemy model for Complete Weather Forecast"""
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location_name = Column(String(255), default="", nullable=False)
    timezone = Column(String(100), default="UTC", nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Current weather (JSON)
    current = Column(JSON, nullable=True)

    # Hourly forecast (JSON)
    hourly = Column(JSON, default=list, nullable=False)

    # Daily forecast (JSON)
    daily = Column(JSON, default=list, nullable=False)

    # Alerts (JSON)
    alerts = Column(JSON, default=list, nullable=False)

    # Source metadata
    source = Column(String(50), default="open-meteo", nullable=False)
    model = Column(String(50), default="best_match", nullable=False)
    units = Column(String(20), default="metric", nullable=False)

    __table_args__ = (
        Index('ix_weather_forecasts_location', 'latitude', 'longitude'),
    )

    def to_entity(self):
        from ....domain.value_objects.coordinates import Coordinates
        return WeatherForecast(
            coordinates=Coordinates(latitude=self.latitude, longitude=self.longitude),
            location_name=self.location_name,
            timezone=self.timezone,
            generated_at=self.generated_at,
            current=WeatherCurrentModel.from_dict(self.current) if self.current else None,
            hourly=[WeatherHourlyModel.from_dict(h) for h in self.hourly],
            daily=[WeatherDailyModel.from_dict(d) for d in self.daily],
            alerts=[WeatherAlertModel.from_dict(a) for a in self.alerts],
            source=self.source,
            model=self.model,
            units=self.units,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            latitude=entity.coordinates.latitude,
            longitude=entity.coordinates.longitude,
            location_name=entity.location_name,
            timezone=entity.timezone,
            generated_at=entity.generated_at,
            current=entity.current.to_dict() if entity.current else None,
            hourly=[h.to_dict() for h in entity.hourly],
            daily=[d.to_dict() for d in entity.daily],
            alerts=[a.to_dict() for a in entity.alerts],
            source=entity.source,
            model=entity.model,
            units=entity.units,
        )


# Add helper methods to WeatherHourlyModel and WeatherDailyModel
WeatherHourlyModel.from_dict = staticmethod(lambda d: WeatherHourly(
    timestamp=datetime.fromisoformat(d["timestamp"]),
    temperature=d["temperature"],
    feels_like=d["feels_like"],
    dew_point=d["dew_point"],
    humidity=d["humidity"],
    pressure=d["pressure"],
    wind_speed=d["wind_speed"],
    wind_direction=d["wind_direction"],
    wind_gust=d["wind_gust"],
    condition=WeatherCondition(d["condition"]),
    condition_description=d["condition_description"],
    cloud_cover=d["cloud_cover"],
    visibility=d["visibility"],
    precipitation=d["precipitation"],
    precipitation_type=PrecipitationType(d["precipitation_type"]),
    precipitation_probability=d["precipitation_probability"],
    uv_index=d["uv_index"],
))

WeatherHourlyModel.to_dict = lambda self: {
    "timestamp": self.timestamp.isoformat(),
    "temperature": self.temperature,
    "feels_like": self.feels_like,
    "dew_point": self.dew_point,
    "humidity": self.humidity,
    "pressure": self.pressure,
    "wind_speed": self.wind_speed,
    "wind_direction": self.wind_direction,
    "wind_gust": self.wind_gust,
    "condition": self.condition.value,
    "condition_description": self.condition_description,
    "cloud_cover": self.cloud_cover,
    "visibility": self.visibility,
    "precipitation": self.precipitation,
    "precipitation_type": self.precipitation_type.value,
    "precipitation_probability": self.precipitation_probability,
    "uv_index": self.uv_index,
}

WeatherDailyModel.from_dict = staticmethod(lambda d: WeatherDaily(
    date=date.fromisoformat(d["date"]),
    temperature_min=d["temperature_min"],
    temperature_max=d["temperature_max"],
    temperature_morning=d["temperature_morning"],
    temperature_noon=d["temperature_noon"],
    temperature_evening=d["temperature_evening"],
    temperature_night=d["temperature_night"],
    feels_like_min=d["feels_like_min"],
    feels_like_max=d["feels_like_max"],
    sunrise=datetime.fromisoformat(d["sunrise"]) if d["sunrise"] else None,
    sunset=datetime.fromisoformat(d["sunset"]) if d["sunset"] else None,
    daylight_duration=d["daylight_duration"],
    sunshine_duration=d["sunshine_duration"],
    condition=WeatherCondition(d["condition"]),
    condition_description=d["condition_description"],
    precipitation_sum=d["precipitation_sum"],
    precipitation_probability_max=d["precipitation_probability_max"],
    precipitation_hours=d["precipitation_hours"],
    precipitation_type=PrecipitationType(d["precipitation_type"]),
    wind_speed_max=d["wind_speed_max"],
    wind_gust_max=d["wind_gust_max"],
    wind_direction_dominant=d["wind_direction_dominant"],
    uv_index_max=d["uv_index_max"],
    uv_index_clear_sky_max=d["uv_index_clear_sky_max"],
    humidity_mean=d["humidity_mean"],
    pressure_mean=d["pressure_mean"],
    cloud_cover_mean=d["cloud_cover_mean"],
    visibility_mean=d["visibility_mean"],
    hourly=[WeatherHourlyModel.from_dict(h) for h in d["hourly"]],
))

WeatherDailyModel.to_dict = lambda self: {
    "date": self.date.isoformat(),
    "temperature_min": self.temperature_min,
    "temperature_max": self.temperature_max,
    "temperature_morning": self.temperature_morning,
    "temperature_noon": self.temperature_noon,
    "temperature_evening": self.temperature_evening,
    "temperature_night": self.temperature_night,
    "feels_like_min": self.feels_like_min,
    "feels_like_max": self.feels_like_max,
    "sunrise": self.sunrise.isoformat() if self.sunrise else None,
    "sunset": self.sunset.isoformat() if self.sunset else None,
    "daylight_duration": self.daylight_duration,
    "sunshine_duration": self.sunshine_duration,
    "condition": self.condition.value,
    "condition_description": self.condition_description,
    "precipitation_sum": self.precipitation_sum,
    "precipitation_probability_max": self.precipitation_probability_max,
    "precipitation_hours": self.precipitation_hours,
    "precipitation_type": self.precipitation_type.value,
    "wind_speed_max": self.wind_speed_max,
    "wind_gust_max": self.wind_gust_max,
    "wind_direction_dominant": self.wind_direction_dominant,
    "uv_index_max": self.uv_index_max,
    "uv_index_clear_sky_max": self.uv_index_clear_sky_max,
    "humidity_mean": self.humidity_mean,
    "pressure_mean": self.pressure_mean,
    "cloud_cover_mean": self.cloud_cover_mean,
    "visibility_mean": self.visibility_mean,
    "hourly": [h.to_dict() for h in self.hourly],
}

WeatherAlertModel.from_dict = staticmethod(lambda d: WeatherAlert(
    id=d["id"],
    title=d["title"],
    description=d["description"],
    severity=WeatherSeverity(d["severity"]),
    certainty=d["certainty"],
    urgency=d["urgency"],
    event=d["event"],
    effective=datetime.fromisoformat(d["effective"]) if d["effective"] else None,
    expires=datetime.fromisoformat(d["expires"]) if d["expires"] else None,
    sender=d["sender"],
    areas=d["areas"],
    coordinates=Coordinates(latitude=d["coordinates"]["lat"], longitude=d["coordinates"]["lng"]) if d["coordinates"] else None,
    source=d["source"],
))

WeatherAlertModel.to_dict = lambda self: {
    "id": self.id,
    "title": self.title,
    "description": self.description,
    "severity": self.severity.value,
    "certainty": self.certainty,
    "urgency": self.urgency,
    "event": self.event,
    "effective": self.effective.isoformat() if self.effective else None,
    "expires": self.expires.isoformat() if self.expires else None,
    "sender": self.sender,
    "areas": self.areas,
    "coordinates": {"lat": self.coordinates.latitude, "lng": self.coordinates.longitude} if self.coordinates else None,
    "source": self.source,
}
