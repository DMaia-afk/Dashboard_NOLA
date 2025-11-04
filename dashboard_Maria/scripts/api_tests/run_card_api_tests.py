#!/usr/bin/env python3
"""Run a suite of HTTP checks against the card APIs and write a JSON report.

Assumes a local dev server at http://localhost:8000 by default.
"""
import json
import os
import sys
import logging
from datetime import datetime

from api_test_client import fetch_json


BASE = os.environ.get('API_BASE', 'http://localhost:8000')

ENDPOINTS = {
    'card-faturamento-total': '/api/card-faturamento-total/',
    'card-ticket-medio': '/api/card-ticket-medio/',
    'card-vendas-por-dia-hora': '/api/card-vendas-por-dia-hora/',
    'card-produtos-mais-vendidos': '/api/card-produtos-mais-vendidos/',
    'card-produtos-menos-vendidos': '/api/card-produtos-menos-vendidos/',
    'card-produtos-mais-customizados': '/api/card-produtos-mais-customizados/',
    'card-itens-complementos-mais-vendidos': '/api/card-itens-complementos-mais-vendidos/',
    'card-taxa-cancelamento': '/api/card-taxa-cancelamento/',
    'card-taxa-desconto': '/api/card-taxa-desconto/',
    'card-performance-entrega-regiao': '/api/card-performance-entrega-regiao/',
    'card-mix-produtos': '/api/card-mix-produtos/',
    'card-clientes-frequentes': '/api/card-clientes-frequentes/',
    'card-clientes-ausentes': '/api/card-clientes-ausentes/',
    'card-novos-clientes': '/api/card-novos-clientes/',
    'card-retencao-clientes': '/api/card-retencao-clientes/',
    'card-lifetime-value': '/api/card-lifetime-value/',
    'card-performance-por-canal': '/api/card-performance-por-canal/',
    'card-performance-por-loja': '/api/card-performance-por-loja/',
    'card-anomalias-temporais': '/api/card-anomalias-temporais/',
    'card-previsao-demanda': '/api/card-previsao-demanda/',
    'card-produto-sazonal': '/api/card-produto-sazonal/',
    'card-crescimento-loja': '/api/card-crescimento-loja/',
    'card-anomalias-operacionais': '/api/card-anomalias-operacionais/',
    'card-analysis': '/api/card-analysis/',
    'chart-analysis': '/api/chart-analysis/',
    'recent-sales': '/api/recent-sales/',
    'lojas-list': '/api/lojas/',
}


def run_all():
    results = {}
    for name, path in ENDPOINTS.items():
        url = BASE.rstrip('/') + path
        logging.info('Checking %s -> %s', name, url)
        try:
            status, data = fetch_json(url)
        except Exception as e:
            logging.exception('ERROR checking %s', name)
            results[name] = { 'status': 'error', 'error': str(e) }
            continue
        ok = (status == 200 and (isinstance(data, (dict, list)) or isinstance(data, str)))
        brief = None
        if isinstance(data, dict):
            brief = { 'type': 'object', 'keys': list(data.keys())[:8] }
        elif isinstance(data, list):
            brief = { 'type': 'array', 'len': len(data) }
        elif isinstance(data, str):
            brief = { 'type': 'text', 'len': len(data) }
    results[name] = { 'status_code': status, 'ok': ok, 'brief': brief }
    logging.info('%s', 'OK' if ok else f'FAILED (status {status})')

    # write report
    report = { 'base': BASE, 'timestamp': datetime.utcnow().isoformat() + 'Z', 'results': results }
    with open('api_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logging.info('Report written to api_test_report.json')
    # summary
    passed = sum(1 for v in results.values() if v.get('ok'))
    total = len(results)
    logging.info('Passed %s/%s', passed, total)


if __name__ == '__main__':
    run_all()
