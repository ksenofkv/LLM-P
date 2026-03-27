# test_model.py
import sys
from pathlib import Path

# Добавляем корень проекта в путь, если скрипт запускается не оттуда
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.api.deps import get_openrouter_service

print(f'🔹 Модель в настройках: {settings.openrouter_model}')
service = get_openrouter_service()
print(f'🔹 Модель в сервисе: {service._default_model}')

if settings.openrouter_model == service._default_model:
    print('✅ Модель из .env корректно передаётся в сервис!')
else:
    print('❌ Несовпадение! Проверьте deps.py')