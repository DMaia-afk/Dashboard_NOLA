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
except Exception:
    logging.exception('FAILED to setup Django')
    sys.exit(2)

try:
    from dashboard_Maria.utils import get_taxa_cancelamento_detailed
    data_inicio = '2025-05-03'
    data_fim = '2025-05-10'
    logging.info('Calling get_taxa_cancelamento_detailed with %s %s', data_inicio, data_fim)
    res = get_taxa_cancelamento_detailed(None, None, data_inicio, data_fim)
    logging.info('%s', json.dumps(res, ensure_ascii=False, indent=2))
except Exception:
    logging.exception('Exception while calling get_taxa_cancelamento_detailed')
    sys.exit(3)

logging.info('Runner finished successfully')
