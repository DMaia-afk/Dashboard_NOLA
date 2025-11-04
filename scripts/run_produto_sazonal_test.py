#!/usr/bin/env python3
"""Runner para testar o endpoint/função get_produto_sazonal localmente.

Inicializa Django, chama a função e grava o JSON em scripts/test_outputs/.
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path


def bootstrap_django():
    """Ensure project root is on sys.path and configure Django settings."""
    here = Path(__file__).resolve()
    project_root = here.parent.parent
    sys.path.insert(0, str(project_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard_nola.settings')
    try:
        import django
        django.setup()
    except Exception:
        logging.exception('Failed to bootstrap Django')
        raise


def parse_args():
    p = argparse.ArgumentParser(description='Run get_produto_sazonal and save output to file')
    p.add_argument('--loja', default='', help='Nome da loja (obrigatório para análise sazonal)')
    p.add_argument('--canal', default='', help='Nome do canal (opcional)')
    p.add_argument('--data_inicio', default='2025-05-03', help='Data início YYYY-MM-DD')
    p.add_argument('--data_fim', default=datetime.now().strftime('%Y-%m-%d'), help='Data fim YYYY-MM-DD')
    p.add_argument('--out', default='', help='Arquivo de saída (JSON). Se omitido grava em scripts/test_outputs/ with timestamp')
    return p.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    bootstrap_django()

    try:
        from dashboard_Maria.utils import get_produto_sazonal
    except Exception:
        logging.exception('Failed to import get_produto_sazonal')
        sys.exit(2)

    loja = args.loja
    canal = args.canal
    data_inicio = args.data_inicio
    data_fim = args.data_fim

    logging.info('Calling get_produto_sazonal(loja=%r, canal=%r, data_inicio=%s, data_fim=%s)', loja, canal, data_inicio, data_fim)
    try:
        res = get_produto_sazonal(loja, canal, data_inicio, data_fim)
    except Exception:
        logging.exception('Error while running get_produto_sazonal')
        raise

    out_path = args.out
    out_dir = Path(__file__).parent / 'test_outputs'
    out_dir.mkdir(parents=True, exist_ok=True)
    if not out_path:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_loja = loja.replace(' ', '_') if loja else 'all'
        out_path = out_dir / f'produto_sazonal_{safe_loja}_{ts}.json'
    else:
        out_path = Path(out_path)

    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        logging.info('Saved output to %s', out_path)
    except Exception:
        logging.exception('Failed to write output file')
        sys.exit(3)


if __name__ == '__main__':
    main()
