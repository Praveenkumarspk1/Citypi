"""
External API Clients
"""
from .bge_m3_client import BGEM3Client
from .clip_client import CLIPClient
from .gemini_client import GeminiClient
from .gtfs_client import GTFSClient
from .nominatim_client import NominatimClient
from .open_meteo_client import OpenMeteoClient
from .overpass_client import OverpassClient
from .whisper_client import WhisperClient

__all__ = [
    "GeminiClient",
    "BGEM3Client",
    "WhisperClient",
    "CLIPClient",
    "OverpassClient",
    "NominatimClient",
    "OpenMeteoClient",
    "GTFSClient",
]
