export interface WeatherData {
  lat: number;
  lng: number;
  temperature: number | null;
  humidity: number | null;
  wind_speed: number | null;
  weather_description: string | null;
}

export interface WeatherForecast {
  lat: number;
  lng: number;
  forecast: ForecastDay[];
}

export interface ForecastDay {
  date: string;
  temperature_max: number;
  temperature_min: number;
  precipitation_probability: number;
  weather_code: number;
  weather_description: string;
}
