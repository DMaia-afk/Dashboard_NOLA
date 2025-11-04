"""Test runner for dashboard cards.

This script imports `dashboard_Maria.utils`, calls a set of card helper functions with
default parameters, saves outputs to `scripts/test_outputs/` and produces a short summary.
"""
import os
import sys
import json
import traceback
import inspect
from datetime import datetime, timedelta
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
    logging.exception('ERROR: failed to setup Django')
    sys.exit(2)

from dashboard_Maria import utils

DEFAULTS = {
    'loja': None,
    'canal': None,
    'data_inicio': '2025-05-03',
    'data_fim': (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d'),
    'page': 1,
    'mes_inicio': None,
    'mes_fim': None,
    'granularity': 'month',
    'request': None,
}

FUNC_NAMES = [
    'get_faturamento_total',
    'get_ticket_medio',
    'get_vendas_por_dia_hora',
    'get_produtos_mais_vendidos',
    'get_produtos_menos_vendidos',
    'get_produtos_mais_customizados',
    'get_itens_complementos_mais_vendidos',
    'get_taxa_cancelamento',
    'get_taxa_cancelamento_detailed',
    'get_taxa_desconto',
    'get_taxa_desconto_detailed',
    'get_performance_entrega_regiao',
    'get_mix_produtos',
    'get_clientes_frequentes',
    'get_clientes_ausentes',
    'get_novos_clientes',
    'get_retencao_clientes',
    'get_lifetime_value',
    'get_performance_por_canal',
    'get_performance_por_loja',
    'get_anomalias_temporais',
    'get_previsao_demanda',
    'get_produto_sazonal',
    'get_crescimento_loja',
]

OUT_DIR = os.path.join(os.path.dirname(__file__), 'test_outputs')
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

summary = []

for name in FUNC_NAMES:
    func = getattr(utils, name, None)
    if func is None:
        summary.append({'function': name, 'status': 'missing'})
        logging.warning('[MISSING] %s not found in utils', name)
        continue

    sig = inspect.signature(func)
    call_kwargs = {}
    for p in sig.parameters.values():
        if p.name in DEFAULTS:
            call_kwargs[p.name] = DEFAULTS[p.name]
        else:
            if p.default is inspect._empty:
                call_kwargs[p.name] = None

    logging.info('Calling %s with args: %s', name, call_kwargs)
    try:
        res = func(**call_kwargs)
        try:
            dump = json.dumps(res, ensure_ascii=False, indent=2, default=lambda o: repr(o))
            with open(os.path.join(OUT_DIR, f'{name}.json'), 'w', encoding='utf-8') as f:
                f.write(dump)
            summary.append({'function': name, 'status': 'ok', 'output_file': os.path.join('scripts', 'test_outputs', f'{name}.json')})
            logging.info('[OK] %s -> saved to %s', name, f'{name}.json')
        except Exception:
            with open(os.path.join(OUT_DIR, f'{name}.txt'), 'w', encoding='utf-8') as f:
                f.write(repr(res))
            summary.append({'function': name, 'status': 'ok_non_json', 'file': os.path.join('scripts', 'test_outputs', f'{name}.txt')})
            logging.info('[OK] %s -> non-json result saved to %s', name, f'{name}.txt')
    except Exception:
        tb = traceback.format_exc()
        with open(os.path.join(OUT_DIR, f'{name}_error.txt'), 'w', encoding='utf-8') as f:
            f.write(tb)
        summary.append({'function': name, 'status': 'error', 'error_file': os.path.join('scripts', 'test_outputs', f'{name}_error.txt')})
        logging.exception('[ERROR] %s -> exception occurred (details in %s)', name, f'{name}_error.txt')

logging.info('--- Test summary ---')
for s in summary:
    logging.info('%s', s)

logging.info('Outputs saved to %s', OUT_DIR)
logging.info('Done')
