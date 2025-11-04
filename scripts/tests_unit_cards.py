from django.test import TestCase
from django.urls import reverse


class UnitTestsCardAPIs(TestCase):
    """Unit tests for each card API endpoint.

    Each test method targets a single named URL (as defined in dashboard_Maria/urls.py)
    and asserts the endpoint responds with HTTP 200 and returns JSON (parseable).
    """

    def assert_endpoint_json_ok(self, name):
        try:
            url = reverse(name)
        except Exception as e:
            self.fail(f"reverse('{name}') failed: {e}")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200, msg=f"{name} returned {resp.status_code}")
        try:
            _ = resp.json()
        except Exception as e:
            self.fail(f"{name} did not return parseable JSON: {e}")

    def test_card_faturamento_total(self):
        self.assert_endpoint_json_ok('card-faturamento-total')

    def test_card_ticket_medio(self):
        self.assert_endpoint_json_ok('card-ticket-medio')

    def test_card_vendas_por_dia_hora(self):
        self.assert_endpoint_json_ok('card-vendas-por-dia-hora')

    def test_card_produtos_mais_vendidos(self):
        self.assert_endpoint_json_ok('card-produtos-mais-vendidos')

    def test_card_produtos_menos_vendidos(self):
        self.assert_endpoint_json_ok('card-produtos-menos-vendidos')

    def test_card_produtos_mais_customizados(self):
        self.assert_endpoint_json_ok('card-produtos-mais-customizados')

    def test_card_itens_complementos_mais_vendidos(self):
        self.assert_endpoint_json_ok('card-itens-complementos-mais-vendidos')

    def test_card_taxa_cancelamento(self):
        self.assert_endpoint_json_ok('card-taxa-cancelamento')

    def test_card_taxa_desconto(self):
        self.assert_endpoint_json_ok('card-taxa-desconto')

    def test_card_performance_entrega_regiao(self):
        self.assert_endpoint_json_ok('card-performance-entrega-regiao')

    def test_card_mix_produtos(self):
        self.assert_endpoint_json_ok('card-mix-produtos')

    def test_card_clientes_frequentes(self):
        self.assert_endpoint_json_ok('card-clientes-frequentes')

    def test_card_clientes_ausentes(self):
        self.assert_endpoint_json_ok('card-clientes-ausentes')

    def test_card_novos_clientes(self):
        self.assert_endpoint_json_ok('card-novos-clientes')

    def test_card_retencao_clientes(self):
        self.assert_endpoint_json_ok('card-retencao-clientes')

    def test_card_lifetime_value(self):
        self.assert_endpoint_json_ok('card-lifetime-value')

    def test_card_performance_por_canal(self):
        self.assert_endpoint_json_ok('card-performance-por-canal')

    def test_card_performance_por_loja(self):
        self.assert_endpoint_json_ok('card-performance-por-loja')

    def test_card_anomalias_temporais(self):
        self.assert_endpoint_json_ok('card-anomalias-temporais')

    def test_card_previsao_demanda(self):
        self.assert_endpoint_json_ok('card-previsao-demanda')

    def test_card_produto_sazonal(self):
        self.assert_endpoint_json_ok('card-produto-sazonal')

    def test_card_crescimento_loja(self):
        self.assert_endpoint_json_ok('card-crescimento-loja')

    def test_card_anomalias_operacionais(self):
        self.assert_endpoint_json_ok('card-anomalias-operacionais')

    def test_card_analysis(self):
        self.assert_endpoint_json_ok('card-analysis')

    def test_chart_analysis(self):
        self.assert_endpoint_json_ok('chart-analysis')

    def test_recent_sales(self):
        self.assert_endpoint_json_ok('recent-sales')

    def test_lojas_list(self):
        self.assert_endpoint_json_ok('lojas-list')
