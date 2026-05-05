import os
import sys
sys.path.insert(0, os.getcwd())

from app.core.database import SessionLocal, init_db
from app.services.theme_service import get_all_themes
from app.core.config import THEMATIC_AREAS

db = SessionLocal()

# Get all themes
domains = get_all_themes(db)

print(f"=== THEMES CHECK ===")
print(f"Config themes: {len(THEMATIC_AREAS)}")

total_themes = 0
for domain in domains:
    theme_count = len(domain.get('themes', []))
    total_themes += theme_count
    
print(f"DB themes: {total_themes}")

# Check if all config themes are in DB
config_themes = set(THEMATIC_AREAS.keys())
db_theme_names = set()
for domain in domains:
    for t in domain.get('themes', []):
        db_theme_names.add(t['name'])

missing = config_themes - db_theme_names
if missing:
    print(f"Missing themes: {missing}")
else:
    print("OK: All config themes are in DB")

db.close()