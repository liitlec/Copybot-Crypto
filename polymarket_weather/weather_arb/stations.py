"""Stations de résolution : ICAO -> coordonnées exactes + fuseau.

Ordre de résolution :
  1. data/stations.json (surcharge manuelle, prioritaire)
  2. table intégrée ci-dessous (aéroports utilisés par les marchés Polymarket)
  3. géocodage Open-Meteo du nom de station (moins fiable, marqué "geocoded")
Si rien ne marche, la station est inconnue et le marché est ignoré (WX_REQUIRE_STATION=1).

Coordonnées au 1/100e de degré (~1 km) : largement suffisant face à une grille de 9-25 km.
À vérifier/compléter dans data/stations.json pour toute nouvelle ville.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from . import http
from .config import OPEN_METEO_GEOCODING
from .store import read_json, write_json


@dataclass
class Station:
    icao: str
    name: str
    lat: float
    lon: float
    tz: str
    source: str = "builtin"  # builtin | override | geocoded

    @property
    def iem_id(self) -> str:
        """Identifiant IEM : 3 lettres pour les ASOS US (KLGA -> LGA), ICAO sinon."""
        if len(self.icao) == 4 and self.icao.startswith("K"):
            return self.icao[1:]
        return self.icao


# icao: (nom, lat, lon, tz)
BUILTIN: dict[str, tuple[str, float, float, str]] = {
    # Amérique du Nord
    "KLGA": ("New York LaGuardia", 40.78, -73.87, "America/New_York"),
    "KJFK": ("New York JFK", 40.64, -73.78, "America/New_York"),
    "KNYC": ("New York Central Park", 40.78, -73.97, "America/New_York"),
    "KORD": ("Chicago O'Hare", 41.98, -87.90, "America/Chicago"),
    "KMDW": ("Chicago Midway", 41.79, -87.75, "America/Chicago"),
    "KMIA": ("Miami Intl", 25.79, -80.29, "America/New_York"),
    "KATL": ("Atlanta Hartsfield", 33.64, -84.43, "America/New_York"),
    "KDAL": ("Dallas Love Field", 32.85, -96.85, "America/Chicago"),
    "KDFW": ("Dallas/Fort Worth", 32.90, -97.04, "America/Chicago"),
    "KSEA": ("Seattle-Tacoma", 47.45, -122.31, "America/Los_Angeles"),
    "KLAX": ("Los Angeles Intl", 33.94, -118.41, "America/Los_Angeles"),
    "KSFO": ("San Francisco Intl", 37.62, -122.38, "America/Los_Angeles"),
    "KLAS": ("Las Vegas Harry Reid", 36.08, -115.15, "America/Los_Angeles"),
    "KPHX": ("Phoenix Sky Harbor", 33.43, -112.01, "America/Phoenix"),
    "KDEN": ("Denver Intl", 39.86, -104.67, "America/Denver"),
    "KAUS": ("Austin Bergstrom", 30.19, -97.67, "America/Chicago"),
    "KHOU": ("Houston Hobby", 29.65, -95.28, "America/Chicago"),
    "KIAH": ("Houston Bush", 29.99, -95.34, "America/Chicago"),
    "KBOS": ("Boston Logan", 42.37, -71.01, "America/New_York"),
    "KDCA": ("Washington National", 38.85, -77.04, "America/New_York"),
    "KPHL": ("Philadelphia Intl", 39.87, -75.24, "America/New_York"),
    "KMSP": ("Minneapolis-St Paul", 44.88, -93.22, "America/Chicago"),
    "CYYZ": ("Toronto Pearson", 43.68, -79.62, "America/Toronto"),
    "CYUL": ("Montreal Trudeau", 45.47, -73.74, "America/Toronto"),
    "CYVR": ("Vancouver Intl", 49.20, -123.18, "America/Vancouver"),
    "MMMX": ("Mexico City Intl", 19.44, -99.07, "America/Mexico_City"),
    # Amérique du Sud
    "SAEZ": ("Buenos Aires Ezeiza", -34.82, -58.54, "America/Argentina/Buenos_Aires"),
    "SABE": ("Buenos Aires Aeroparque", -34.56, -58.42, "America/Argentina/Buenos_Aires"),
    "SBGR": ("Sao Paulo Guarulhos", -23.44, -46.47, "America/Sao_Paulo"),
    "SCEL": ("Santiago Arturo Merino Benitez", -33.39, -70.79, "America/Santiago"),
    "SKBO": ("Bogota El Dorado", 4.70, -74.15, "America/Bogota"),
    "SPJC": ("Lima Jorge Chavez", -12.02, -77.11, "America/Lima"),
    # Europe
    "EGLC": ("London City Airport", 51.51, 0.06, "Europe/London"),
    "EGLL": ("London Heathrow", 51.47, -0.45, "Europe/London"),
    "EGKK": ("London Gatwick", 51.15, -0.18, "Europe/London"),
    "LFPG": ("Paris Charles de Gaulle", 49.01, 2.55, "Europe/Paris"),
    "LFPO": ("Paris Orly", 48.72, 2.38, "Europe/Paris"),
    "LFPB": ("Paris Le Bourget", 48.97, 2.44, "Europe/Paris"),
    "EDDM": ("Munich", 48.35, 11.79, "Europe/Berlin"),
    "EDDB": ("Berlin Brandenburg", 52.37, 13.50, "Europe/Berlin"),
    "EHAM": ("Amsterdam Schiphol", 52.31, 4.77, "Europe/Amsterdam"),
    "LEMD": ("Madrid Barajas", 40.47, -3.56, "Europe/Madrid"),
    "LEBL": ("Barcelona El Prat", 41.30, 2.08, "Europe/Madrid"),
    "LIRF": ("Rome Fiumicino", 41.80, 12.24, "Europe/Rome"),
    "LIMC": ("Milan Malpensa", 45.63, 8.73, "Europe/Rome"),
    "LIML": ("Milan Linate", 45.45, 9.28, "Europe/Rome"),
    "EPWA": ("Warsaw Chopin", 52.17, 20.97, "Europe/Warsaw"),
    "LTAC": ("Ankara Esenboga", 40.13, 33.00, "Europe/Istanbul"),
    "LTFM": ("Istanbul Airport", 41.26, 28.74, "Europe/Istanbul"),
    "UUEE": ("Moscow Sheremetyevo", 55.97, 37.41, "Europe/Moscow"),
    # Moyen-Orient / Afrique
    "LLBG": ("Tel Aviv Ben Gurion", 32.01, 34.89, "Asia/Jerusalem"),
    "OMDB": ("Dubai Intl", 25.25, 55.37, "Asia/Dubai"),
    "HECA": ("Cairo Intl", 30.12, 31.41, "Africa/Cairo"),
    "FAOR": ("Johannesburg OR Tambo", -26.14, 28.25, "Africa/Johannesburg"),
    # Asie
    "RKSI": ("Seoul Incheon", 37.46, 126.44, "Asia/Seoul"),
    "RKSS": ("Seoul Gimpo", 37.56, 126.79, "Asia/Seoul"),
    "RKPK": ("Busan Gimhae", 35.18, 128.94, "Asia/Seoul"),
    "RJTT": ("Tokyo Haneda", 35.55, 139.78, "Asia/Tokyo"),
    "RJAA": ("Tokyo Narita", 35.76, 140.39, "Asia/Tokyo"),
    "RJBB": ("Osaka Kansai", 34.43, 135.24, "Asia/Tokyo"),
    "ZSPD": ("Shanghai Pudong", 31.14, 121.81, "Asia/Shanghai"),
    "ZSSS": ("Shanghai Hongqiao", 31.20, 121.34, "Asia/Shanghai"),
    "ZBAA": ("Beijing Capital", 40.08, 116.58, "Asia/Shanghai"),
    "ZGSZ": ("Shenzhen Bao'an", 22.64, 113.81, "Asia/Shanghai"),
    "ZGGG": ("Guangzhou Baiyun", 23.39, 113.30, "Asia/Shanghai"),
    "ZUUU": ("Chengdu Shuangliu", 30.58, 103.95, "Asia/Shanghai"),
    "ZUCK": ("Chongqing Jiangbei", 29.72, 106.64, "Asia/Shanghai"),
    "ZHHH": ("Wuhan Tianhe", 30.78, 114.21, "Asia/Shanghai"),
    "VHHH": ("Hong Kong Intl", 22.31, 113.92, "Asia/Hong_Kong"),
    "RCTP": ("Taipei Taoyuan", 25.08, 121.23, "Asia/Taipei"),
    "RCSS": ("Taipei Songshan", 25.07, 121.55, "Asia/Taipei"),
    "WSSS": ("Singapore Changi", 1.36, 103.99, "Asia/Singapore"),
    "VTBS": ("Bangkok Suvarnabhumi", 13.69, 100.75, "Asia/Bangkok"),
    "WMKK": ("Kuala Lumpur Intl", 2.75, 101.71, "Asia/Kuala_Lumpur"),
    "VIDP": ("Delhi Indira Gandhi", 28.56, 77.10, "Asia/Kolkata"),
    "VILK": ("Lucknow Chaudhary Charan Singh", 26.76, 80.89, "Asia/Kolkata"),
    "VABB": ("Mumbai Chhatrapati Shivaji", 19.09, 72.87, "Asia/Kolkata"),
    # Océanie
    "NZWN": ("Wellington Intl", -41.33, 174.81, "Pacific/Auckland"),
    "NZAA": ("Auckland Intl", -37.01, 174.79, "Pacific/Auckland"),
    "YSSY": ("Sydney Kingsford Smith", -33.95, 151.18, "Australia/Sydney"),
    "YMML": ("Melbourne Tullamarine", -37.67, 144.84, "Australia/Melbourne"),
}


class StationRegistry:
    def __init__(self, override_path: Path | None = None, allow_geocoding: bool = True):
        self.override_path = Path(override_path) if override_path else None
        self.allow_geocoding = allow_geocoding
        self._overrides: dict[str, dict] = read_json(self.override_path, {}) if self.override_path else {}

    def get(self, icao: str | None, name_hint: str | None = None) -> Station | None:
        if icao:
            icao = icao.upper()
            if icao in self._overrides:
                o = self._overrides[icao]
                return Station(icao, o.get("name", icao), float(o["lat"]), float(o["lon"]), o["tz"],
                               o.get("source", "override"))
            if icao in BUILTIN:
                name, lat, lon, tz = BUILTIN[icao]
                return Station(icao, name, lat, lon, tz, "builtin")
        if self.allow_geocoding and name_hint:
            st = self._geocode(name_hint, icao)
            if st and self.override_path:
                # On persiste pour vérification manuelle (source="geocoded").
                self._overrides[st.icao] = {k: v for k, v in asdict(st).items() if k != "icao"}
                write_json(self.override_path, self._overrides)
            return st
        return None

    @staticmethod
    def _geocode(name: str, icao: str | None) -> Station | None:
        try:
            data = http.get(OPEN_METEO_GEOCODING, {"name": name, "count": 5, "format": "json"})
        except RuntimeError:
            return None
        results = data.get("results") or []
        # Priorité aux aéroports (code GeoNames AIRP).
        results.sort(key=lambda r: r.get("feature_code") != "AIRP")
        if not results:
            return None
        r = results[0]
        return Station(icao or f"GEO:{name}", r.get("name", name), float(r["latitude"]),
                       float(r["longitude"]), r.get("timezone", "UTC"), "geocoded")
