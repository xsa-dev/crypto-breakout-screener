"""Единый инстанс Jinja2Templates для админки.

Вынесен в отдельный модуль, чтобы и `auth.py`, и `routes.py` пользовались одним
объектом без циклических импортов через `app.py`.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

_TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
