import os
import sys
import json
import logging

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard_nola.settings')

logging.basicConfig(level=logging.INFO)

try:
    import django
    django.setup()
except Exception as e:
    logging.exception('FAILED to setup Django: %s', e)
    sys.exit(2)

try:
    from dashboard_Maria.utils import get_performance_por_loja
    data_inicio = '2025-05-03'
    data_fim = '2025-10-31'
    loja = None
    canal = None
    logging.info('Calling get_performance_por_loja with loja=%r canal=%r data_inicio=%s data_fim=%s granularity=month', loja, canal, data_inicio, data_fim)
    res = get_performance_por_loja(loja, canal, data_inicio, data_fim, granularity='month')
    logging.info('Result: %s', json.dumps(res, ensure_ascii=False, indent=2))
except Exception:
    logging.exception('Exception while calling get_performance_por_loja')
    sys.exit(3)

logging.info('Runner finished successfully')
