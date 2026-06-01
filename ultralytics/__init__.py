# Ultralytics YOLO 🚀, AGPL-3.0 license

__version__ = "8.1.2"

from ultralytics.utils import SETTINGS as settings
from ultralytics.utils.checks import check_yolo as checks
from ultralytics.utils.downloads import download

__all__ = "__version__", "checks", "download", "settings"
