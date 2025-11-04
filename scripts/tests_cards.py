from django.test import TestCase
from django.urls import reverse


class CardsAPISmokeTests(TestCase):
    """Smoke tests for card API endpoints: ensure they return 200 and JSON-like responses.

    These are lightweight sanity checks that help catch routing/500 errors after refactors.
    """

    endpoints = [
        # cards principais (nomes vêm de dashboard_Maria/urls.py)
        'card-faturamento-total',
        'card-ticket-medio',
        'card-vendas-por-dia-hora',
        'card-produtos-mais-vendidos',
        'card-produtos-menos-vendidos',
        'card-produtos-mais-customizados',
        'card-itens-complementos-mais-vendidos',
        'card-taxa-cancelamento',
        'card-taxa-desconto',
        'card-performance-entrega-regiao',
        'card-mix-produtos',
        'card-clientes-frequentes',
        'card-clientes-ausentes',
        'card-novos-clientes',
        'card-retencao-clientes',
        'card-lifetime-value',
        'card-performance-por-canal',
        'card-performance-por-loja',
        'card-anomalias-temporais',
        'card-previsao-demanda',
        # insights / agregados
        'card-produto-sazonal',
        'card-crescimento-loja',
        'card-anomalias-operacionais',
        'card-analysis',
        'chart-analysis',
        # auxiliares
        'recent-sales',
        'lojas-list',
    ]

    def test_card_endpoints_return_200_and_json(self):
        for name in self.endpoints:
            with self.subTest(card=name):
                try:
                    url = reverse(name)
                except Exception as e:
                    self.fail(f"Reverse failed for '{name}': {e}")
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200, msg=f"{name} returned {resp.status_code}")
                # permitir tanto um objeto JSON quanto array; garantir que o parsing não lance erro
                try:
                    _ = resp.json()
                except Exception as e:
                    self.fail(f"{name} did not return parseable JSON: {e}")
