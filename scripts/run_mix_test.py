import os, sys, json
import logging
import traceback
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard_nola.settings')
import django
django.setup()
from dashboard_Maria import utils


def run():
    """Run a single example invocation of get_mix_produtos and save result to file."""
    logging.basicConfig(level=logging.INFO)
    loja = 'Castro - Costa'
    data_inicio = '2025-09-01'
    data_fim = '2025-10-31'
    logging.info('Calling get_mix_produtos with %s %s %s', loja, data_inicio, data_fim)
    try:
        res = utils.get_mix_produtos(loja, None, data_inicio, data_fim)
        out = os.path.join(os.path.dirname(__file__), 'test_outputs', f'mix_produtos_{loja.replace(" ","_")}_{data_inicio}_{data_fim}.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        logging.info('Saved to %s', out)
    except Exception:
        logging.exception('Error while running get_mix_produtos')


if __name__ == '__main__':
    run()
