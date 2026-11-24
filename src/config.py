from enum import Enum
import configparser
import re
import pathlib
from dataclasses import dataclass
from typing import Optional
from qgis.core import QgsSettings, QgsApplication


PLUGIN_DIR = pathlib.Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# FORK-EINSTELLUNGEN: Woher der Loader seine Kataloge holt.
# Owner und Repo werden aus "repository=" in metadata.txt gelesen
# (z. B. https://github.com/winky/geobasis_loader/). Die Werte hier sind nur
# Rückfallwerte, falls metadata.txt keinen GitHub-Link enthält.
# ---------------------------------------------------------------------------
GITHUB_OWNER = "DEIN-GITHUB-NAME"
GITHUB_REPO = "geobasis_loader"
GITHUB_BRANCH = "main"
CATALOG_DIR_IN_REPO = "kataloge"

# Eigener Schlüssel für QGIS-Einstellungen, Presets und Logger, damit der Fork
# neben dem Original-GeoBasis_Loader installiert sein kann, ohne sich zu stören.
SETTINGS_PREFIX = "geobasis_loader_ffm"

PLUGIN_USER_DIR = pathlib.Path(QgsApplication.qgisSettingsDirPath()) / SETTINGS_PREFIX

RESOURCES_DIR = PLUGIN_DIR / "resources"
PRESETS_DIR = PLUGIN_USER_DIR / "presets"

@dataclass(frozen=True)
class PluginInfo:
    name: str = ""
    version: str = ""
    icon: str = ""
    icon_path: Optional[pathlib.Path] = None
    description: str = ""
    qgis_min_version: str = ""
    qgis_max_version: str = ""
    author: str = ""
    email: str = ""
    homepage: str = ""
    repository: str = ""
    tracker: str = ""

def read_metadata(metadata_path: Optional[pathlib.Path] = None) -> PluginInfo:
    path = metadata_path or (PLUGIN_DIR / "metadata.txt")
    if not path.exists():
        return PluginInfo()

    parser = configparser.ConfigParser()
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error:
        return PluginInfo()

    section = parser["general"] if parser.has_section("general") else {}
    name = section.get("name", "")
    name = name.replace("_", " ") if name else ""
    icon = section.get("icon", "")
    icon_path = (PLUGIN_DIR / icon) if icon else None

    return PluginInfo(
        name=name,
        version=section.get("version", ""),
        icon=icon,
        icon_path=icon_path,
        description=section.get("description", ""),
        qgis_min_version=section.get("qgisMinimumVersion", ""),
        qgis_max_version=section.get("qgisMaximumVersion", ""),
        author=section.get("author", ""),
        email=section.get("email", ""),
        homepage=section.get("homepage", ""),
        repository=section.get("repository", ""),
        tracker=section.get("tracker", ""),
    )

plugin_info = read_metadata()

_repo_match = re.search(r"github\.com/([^/]+)/([^/?#]+)", plugin_info.repository or "")
if _repo_match:
    GITHUB_OWNER = _repo_match.group(1)
    GITHUB_REPO = _repo_match.group(2).removesuffix(".git")

PLUGIN_NAME = plugin_info.name
PLUGIN_NAME_AND_VERSION = PLUGIN_NAME + ' (v' + plugin_info.version + ')'

REQUEST_TIMEOUT_MS = 10000
PLUGIN_LOGGER_NAME = SETTINGS_PREFIX
TOOLBAR_NAME = "geoObserverTools"
LOGGING_SUCCESS_LEVEL = 25
PRESET_FORMAT_VERSION = 7.00
BOOKMARK_GROUP_NAME = plugin_info.name
STAR_PREFIX = "\u2605 "  # ★
SEARCH_HIGHLIGHT_COLOR = "#DA0000"  # Red, for highlight text when searching in the panel
GRAYED_OUT_COLOR = "#808080"  # Gray, for items from other catalogs

CURRENT_CATALOG_SCORE_BONUS = 1000  # Score bonus for entries from the currently selected catalog

CATALOG_OVERVIEW = "GeoBasis_Loader_v6_Kataloge.json"
CATALOG_OVERVIEW_NAME = "catalog_overview"

class ServerHosts(str, Enum):
    # Server 1: raw.githubusercontent.com (kein API-Ratenlimit, ca. 5 Min. CDN-Cache)
    GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{CATALOG_DIR_IN_REPO}/{{name}}"
    # Server 2: GitHub Contents API (sofort aktuell, aber max. 60 Anfragen/Stunde ohne Login)
    GITHUB = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{CATALOG_DIR_IN_REPO}/{{name}}?ref={GITHUB_BRANCH}"
    
    @classmethod
    def get_all_servers(cls) -> list[str]:
        return [a.value for a in cls]
    
    @classmethod
    def get_enabled_servers(cls) -> list[str]:
        servers = []
        qgs_settings = QgsSettings()
        server_index = qgs_settings.value(QgsSettingsKeys.SERVERS, 0, type=int)
        all_servers = cls.get_all_servers()
        if server_index == 0 or server_index > len(all_servers):
            servers = all_servers
        else:
            servers.append(all_servers[server_index - 1])
            
        return servers
    
class QgsSettingsKeys(str, Enum):
    CURRENT_CATALOG = SETTINGS_PREFIX + '/current_catalog'
    AUTOMATIC_CRS = SETTINGS_PREFIX + '/automatic_crs'
    SERVERS = SETTINGS_PREFIX + '/servers'
    SHOW_GBL_PANEL = SETTINGS_PREFIX + '/show_gbl_panel'
    DISPLAY_HIGHLIGHT_FAVORITES = SETTINGS_PREFIX + '/display_highlight_favorites'
    PROPERTY_FAVORITE = SETTINGS_PREFIX + '/properties/favorite'
    PROPERTY_INVISIBLE = SETTINGS_PREFIX + '/properties/invisible'
    PROPERTY_DISABLED = SETTINGS_PREFIX + '/properties/disabled'
