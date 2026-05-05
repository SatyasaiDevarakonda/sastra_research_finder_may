from app.core.config import THEMATIC_AREAS

print(f'Total themes in config: {len(THEMATIC_AREAS)}')
print('All theme names:')
for i, theme in enumerate(THEMATIC_AREAS.keys(), 1):
    print(f'{i}. {theme}')