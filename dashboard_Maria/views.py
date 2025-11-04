from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Stores
import logging

# Endpoint para listar todas as lojas
class LojasListAPIView(APIView):
    def get(self, request):
        lojas = list(Stores.objects.values_list('name', flat=True))
        return Response({'lojas': lojas})
from rest_framework.views import APIView
from rest_framework.response import Response

class CardProdutosComItensMaisRemovidosAPIView(APIView):
    def get(self, request):
        
        with connection.cursor() as cursor:
            query = '''
                SELECT 
                    i.name AS complemento_removido,
                    array_agg(DISTINCT p.name) AS produtos_complemento
                FROM item_product_sales ips
                JOIN items i ON i.id = ips.item_id
                JOIN product_sales ps ON ps.id = ips.product_sale_id
                JOIN products p ON p.id = ps.product_id
                JOIN option_groups og ON og.id = ips.option_group_id
                JOIN sales s ON s.id = ps.sale_id
                WHERE s.sale_status_desc = 'COMPLETED'
                  AND og.name = 'Remover'
                GROUP BY i.name
                ORDER BY COUNT(*) DESC
                LIMIT 6;
            '''
            cursor.execute(query)
            rows = cursor.fetchall()
            produtos_removidos = [
                {
                    'complemento_removido': row[0],
                    'produtos_complemento': row[1]
                }
                for row in rows
            ]
        if not produtos_removidos:
            return Response({'produtos_removidos': [], 'message': 'Nenhum dado encontrado no banco.'})
        return Response({'produtos_removidos': produtos_removidos})
# views.py base para os 20 cards do CARD_IDEAS.md
from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connection
from datetime import datetime
from .utils import (get_complementos_mais_adicionados, get_complementos_mais_removidos, parse_filters)
from .utils import analyze_chart_data, get_itens_complementos_mais_vendidos, get_produtos_mais_vendidos

# API para complementos mais adicionados
class CardComplementosMaisAdicionadosAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        logging.getLogger('dashboard_Maria').info(f"[API Complementos Adicionados] loja={loja}, canal={canal}, data_inicio={data_inicio}, data_fim={data_fim}")
        
        data = get_complementos_mais_adicionados(loja, canal, data_inicio, data_fim)
        items = data['top_complementos']
        if not items:
            # Se não houver dados no período, retorna top global
            from .utils import get_top_complementos_global
            items = get_top_complementos_global('adicionados')
            if not items:
                return Response({'top_complementos': [], 'message': 'Nenhum dado encontrado no banco.'})
        return Response({'top_complementos': items})

# API para complementos mais removidos
class CardComplementosMaisRemovidosAPIView(APIView):
    def get(self, request):
        
        try:
            with connection.cursor() as cursor:
                query = '''
                    SELECT 
                        p.name AS produto_base,
                        i.name AS complemento_removido,
                        COUNT(*) AS vezes_removido,
                        SUM(ips.additional_price) AS receita_perdida
                    FROM product_sales ps
                    JOIN products p ON p.id = ps.product_id
                    JOIN item_product_sales ips ON ips.product_sale_id = ps.id
                    JOIN items i ON i.id = ips.item_id
                    JOIN option_groups og ON og.id = ips.option_group_id
                    JOIN sales s ON s.id = ps.sale_id
                    WHERE s.sale_status_desc = 'COMPLETED'
                      AND og.name = 'Remover'
                    GROUP BY p.name, i.name
                    ORDER BY vezes_removido DESC
                    LIMIT 6;
                '''
                cursor.execute(query)
                rows = cursor.fetchall()
                removidos = [
                    {
                        'produto_base': row[0],
                        'complemento_removido': row[1],
                        'vezes_removido': row[2],
                        'receita_perdida': float(row[3]) if row[3] is not None else 0.0
                    }
                    for row in rows
                ]
            if not removidos:
                return Response({'removidos': [], 'message': 'Nenhum dado encontrado no banco.'})
            return Response({'removidos': removidos})
        except Exception as e:
            # Log and return JSON error so frontend doesn't try to parse HTML error page
            import logging
            logging.getLogger('dashboard_Maria').exception('CardComplementosMaisRemovidosAPIView error: %s', e)
            return Response({'error': 'Erro ao gerar relatório de complementos removidos.'}, status=500)

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')


# New simple template views: Sales map and Calendar
class SalesMapView(View):
    """Renders an interactive sales map page. The frontend will attempt
    to fetch real sales points (if an endpoint is available) and falls
    back to a simulated realtime feed for local development."""
    def get(self, request):
        return render(request, 'map.html')


class CalendarView(View):
    """Renders a full-year calendar where users can view holidays and
    add per-day annotations. Notes are stored in browser localStorage
    by the frontend (no server persistence by default)."""
    def get(self, request):
        return render(request, 'calendar.html')
    

# Estrutura base para os 20 endpoints dos cards
# Cada classe abaixo representa um card do arquivo CARD_IDEAS.md
# Implemente a lógica de cada card conforme a necessidade

from .utils import (
    parse_filters,
    get_faturamento_total,
    get_ticket_medio,
    get_vendas_por_dia_hora,
    get_produtos_mais_vendidos,
    get_produtos_menos_vendidos,
    get_produtos_mais_customizados,
    get_itens_complementos_mais_vendidos,
    get_taxa_cancelamento,
    get_taxa_desconto,
    get_performance_entrega_regiao,
    get_mix_produtos,
    get_clientes_frequentes,
    get_clientes_ausentes,
    get_novos_clientes,
    get_retencao_clientes,
    get_lifetime_value,
    get_performance_por_canal,
    get_performance_por_loja,
    get_anomalias_temporais,
    get_previsao_demanda,
)

from .utils import analyze_card


class CardAnalysisAPIView(APIView):
    """POST endpoint that receives a card_id and filters and returns a short analysis

    Expected JSON body: { 'card_id': 'card-clientes-frequentes', 'loja': 'Loja X', 'canal': 'App', 'data_inicio': 'YYYY-MM-DD', 'data_fim': 'YYYY-MM-DD' }
    """
    def post(self, request):
        body = request.data or {}
        card_id = body.get('card_id')
        loja = body.get('loja')
        canal = body.get('canal')
        data_inicio = body.get('data_inicio')
        data_fim = body.get('data_fim')
        if not card_id or not data_inicio or not data_fim:
            return Response({'error': 'card_id, data_inicio and data_fim are required'}, status=400)
        
        try:
            session = request.session
            last_card = session.get('last_analysis_card')
            if last_card and last_card != card_id:
                # clear previous analysis state
                session.pop('last_analysis', None)
                session.pop('last_analysis_card', None)
            # compute new analysis
            analysis = analyze_card(card_id, loja, canal, data_inicio, data_fim)
            # store in session for possible later retrieval (ephemeral)
            try:
                session['last_analysis'] = analysis
                session['last_analysis_card'] = card_id
                session.modified = True
            except Exception:
                # If session backend not available or read-only, ignore storing
                pass
            return Response({'analysis': analysis})
        except Exception as e:
            import logging
            logging.getLogger('dashboard_Maria').exception('CardAnalysisAPIView error: %s', e)
            return Response({'error': 'Failed to compute analysis'}, status=500)


class ChartAnalysisAPIView(APIView):
    """POST endpoint that analyzes chart data (labels + values) or derives them for known cards.

    Payload examples:
    - { labels: [...], values: [...] }
    - { card_id: 'card-produtos-mais-vendidos', loja: 'Loja X', data_inicio: 'YYYY-MM-DD', data_fim: 'YYYY-MM-DD' }
    """
    def post(self, request):
        body = request.data or {}
        labels = body.get('labels')
        values = body.get('values')
        card_id = body.get('card_id')
        loja = body.get('loja')
        canal = body.get('canal')
        data_inicio = body.get('data_inicio')
        data_fim = body.get('data_fim')

        try:
            if labels and values:
                res = analyze_chart_data(labels, values)
                return Response({'analysis': res})
            if not card_id:
                return Response({'error': 'Provide labels+values or a card_id to derive data'}, status=400)
            if not data_inicio or not data_fim:
                return Response({'error': 'data_inicio and data_fim are required when deriving from card_id'}, status=400)

            # Map known cards to utils functions that return lists
            if card_id == 'card-produtos-mais-vendidos':
                data = get_produtos_mais_vendidos(loja, canal, data_inicio, data_fim)
                items = data.get('top_produtos', [])
                labels = [i.get('produto') for i in items]
                values = [i.get('quantidade') for i in items]
            elif card_id in ('card-itens-complementos-mais-vendidos', 'card-complementos-mais-adicionados'):
                data = get_itens_complementos_mais_vendidos(loja, canal, data_inicio, data_fim)
                items = data.get('top_complementos', [])
                # compat: item key may be 'item' or 'adicional'
                labels = [i.get('item') or i.get('adicional') for i in items]
                values = [i.get('quantidade') or i.get('vezes_utilizado') or i.get('times_added') for i in items]
            elif card_id in ('card-complementos-mais-removidos', 'card-complementos-mais-removidos'):
                # reuse the above function with tipo=removidos
                data = get_itens_complementos_mais_vendidos(loja, canal, data_inicio, data_fim)
                items = data.get('top_complementos', [])
                labels = [i.get('item') for i in items]
                values = [i.get('quantidade') for i in items]
            else:
                return Response({'error': 'Unsupported card_id for automatic chart derivation'}, status=400)

            if not labels or not values:
                return Response({'error': 'No data found for card'}, status=404)

            res = analyze_chart_data(labels, values)
            return Response({'analysis': res, 'labels': labels, 'values': values})
        except Exception as e:
            import logging
            logging.getLogger('dashboard_Maria').exception('ChartAnalysisAPIView error: %s', e)
            return Response({'error': 'Failed to analyze chart data'}, status=500)


import logging
from .models import DashboardLayout
from .models import Sales, DeliveryAddresses, Stores
from django.utils import timezone


class RecentSalesAPIView(APIView):
    """Returns recent sales with latitude/longitude resolved.

    Response: JSON array of objects: { lat, lng, amount, city, store_name, timestamp }
    Query params:
      - limit: int (default 200)
      - since: ISO datetime string to filter newer than this
    """
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 200))
        except Exception:
            limit = 200
        since = request.GET.get('since')
        qs = Sales.objects.filter(sale_status_desc__iexact='COMPLETED').order_by('-created_at')
        if since:
            try:
                dt = timezone.datetime.fromisoformat(since)
                qs = qs.filter(created_at__gt=dt)
            except Exception:
                pass
        results = []
        count = 0
        for s in qs.iterator():
            if count >= limit:
                break
            lat = None
            lng = None
            city = None
            # Prefer delivery address coordinates when available
            try:
                da = DeliveryAddresses.objects.filter(sale=s).first()
                if da and da.latitude and da.longitude:
                    lat = float(da.latitude)
                    lng = float(da.longitude)
                    city = da.city or da.neighborhood or None
            except Exception:
                da = None
            if lat is None or lng is None:
                try:
                    st = s.store
                    if st and st.latitude and st.longitude:
                        lat = float(st.latitude)
                        lng = float(st.longitude)
                        city = st.city or st.district or None
                except Exception:
                    pass
            if lat is None or lng is None:
                # skip sales without any coordinates
                continue
            results.append({
                'lat': lat,
                'lng': lng,
                'amount': float(s.total_amount) if s.total_amount is not None else None,
                'city': city,
                'store_name': getattr(s.store, 'name', None),
                'timestamp': s.created_at.isoformat() if getattr(s, 'created_at', None) else None,
            })
            count += 1
        return Response(results)


class DashboardLayoutAPIView(APIView):
    """GET returns the saved layout for the current user/session.

    POST accepts JSON payload { layout: { order: [...], visibility: {...} } }
    and persists it either to the user record (if authenticated) or to the
    session_key.
    """
    def get(self, request):
        try:
            if request.user and request.user.is_authenticated:
                obj = DashboardLayout.objects.filter(user=request.user).order_by('-updated_at').first()
            else:
                # ensure session exists
                if not request.session.session_key:
                    request.session.save()
                sk = request.session.session_key
                obj = DashboardLayout.objects.filter(session_key=sk).order_by('-updated_at').first()
            if obj:
                return Response({'layout': obj.layout})
            return Response({'layout': {}})
        except Exception as e:
            logging.getLogger('dashboard_Maria').exception('DashboardLayoutAPIView GET error: %s', e)
            return Response({'layout': {}}, status=500)

    def post(self, request):
        try:
            payload = request.data or {}
            layout = payload.get('layout') if isinstance(payload, dict) else payload
            if not isinstance(layout, dict):
                # allow clients to send top-level order/visibility
                layout = {
                    'order': payload.get('order') if isinstance(payload, dict) else None,
                    'visibility': payload.get('visibility') if isinstance(payload, dict) else None
                }
            if request.user and request.user.is_authenticated:
                obj, _ = DashboardLayout.objects.update_or_create(user=request.user, defaults={'layout': layout})
            else:
                if not request.session.session_key:
                    request.session.save()
                sk = request.session.session_key
                obj, _ = DashboardLayout.objects.update_or_create(session_key=sk, defaults={'layout': layout})
            return Response({'status': 'ok', 'layout': obj.layout})
        except Exception as e:
            logging.getLogger('dashboard_Maria').exception('DashboardLayoutAPIView POST error: %s', e)
            return Response({'error': 'failed to save layout'}, status=500)

class CardProdutosMenosVendidosAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_produtos_menos_vendidos(loja, canal, data_inicio, data_fim)
        return Response(data)


class CardFaturamentoTotalAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_faturamento_total(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardTicketMedioAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_ticket_medio(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardVendasPorDiaHoraAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_vendas_por_dia_hora(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardProdutosMaisVendidosAPIView(APIView):
    def get(self, request):
        try:
            loja, canal, data_inicio, data_fim = parse_filters(request)
            data = get_produtos_mais_vendidos(loja, canal, data_inicio, data_fim)
            return Response(data)
        except Exception as e:
            # Evita 500 HTML e retorna JSON de erro para o frontend poder tratar
            import logging
            logging.getLogger('dashboard_Maria').exception('Erro CardProdutosMaisVendidosAPIView: %s', e)
            return Response({'error': 'Erro ao gerar relatório de produtos mais vendidos.'}, status=500)


class CardProdutosMaisCustomizadosAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_produtos_mais_customizados(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardItensComplementosMaisVendidosAPIView(APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            query = '''
                SELECT 
                    p.name AS produto_base,
                    i.name AS adicional,
                    COUNT(*) AS vezes_utilizado,
                    SUM(ips.additional_price) AS receita_gerada
                FROM product_sales ps
                JOIN products p ON p.id = ps.product_id
                JOIN item_product_sales ips ON ips.product_sale_id = ps.id
                JOIN items i ON i.id = ips.item_id
                JOIN option_groups og ON og.id = ips.option_group_id
                JOIN sales s ON s.id = ps.sale_id
                WHERE s.sale_status_desc = 'COMPLETED'
                  AND og.name = 'Adicionais'
                GROUP BY p.name, i.name
                ORDER BY vezes_utilizado DESC
                LIMIT 6;
            '''
            cursor.execute(query)
            rows = cursor.fetchall()
            adicionais = [
                {
                    'produto_base': row[0],
                    'adicional': row[1],
                    'vezes_utilizado': row[2],
                    'receita_gerada': float(row[3]) if row[3] is not None else 0.0
                }
                for row in rows
            ]
        if not adicionais:
            return Response({'adicionais': [], 'message': 'Nenhum dado encontrado no banco.'})
        return Response({'adicionais': adicionais})

class CardTaxaCancelamentoAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        detail = request.GET.get('detail')
        try:
            if detail and detail.lower() in ('1', 'true', 'yes'):
                from .utils import get_taxa_cancelamento_detailed
                data = get_taxa_cancelamento_detailed(loja, canal, data_inicio, data_fim)
                return Response(data)
            data = get_taxa_cancelamento(loja, canal, data_inicio, data_fim)
            return Response(data)
        except Exception as e:
            import logging
            logging.getLogger('dashboard_Maria').exception('CardTaxaCancelamentoAPIView error: %s', e)
            return Response({'error': 'Erro ao gerar taxa de cancelamento.'}, status=500)

class CardTaxaDescontoAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        detail = request.GET.get('detail')
        try:
            if detail and detail.lower() in ('1', 'true', 'yes'):
                from .utils import get_taxa_desconto_detailed
                data = get_taxa_desconto_detailed(loja, canal, data_inicio, data_fim)
                return Response(data)
            # default compact response
            data = get_taxa_desconto(loja, canal, data_inicio, data_fim)
            return Response(data)
        except Exception as e:
            import logging
            logging.getLogger('dashboard_Maria').exception('CardTaxaDescontoAPIView error: %s', e)
            return Response({'error': 'Erro ao gerar taxa de desconto.'}, status=500)

class CardPerformanceEntregaRegiaoAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        page = int(request.GET.get('page', 1))
        per_page = 5
        data = get_performance_entrega_regiao(loja, canal, data_inicio, data_fim)
        items = data['tempo_entrega']
        total_pages = max(1, (len(items) + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = items[start:end]
        return Response({'tempo_entrega': paginated, 'page': page, 'total': total_pages})

class CardMixProdutosAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        try:
            page = int(request.GET.get('page', 1))
        except Exception:
            page = 1
        per_page = 5
        try:
            # Allow clients to request a max number of items via ?max_items=N or in the POST body
            try:
                max_items = int(request.GET.get('max_items') or request.data.get('max_items') or 10)
            except Exception:
                max_items = 10

            data = get_mix_produtos(loja, canal, data_inicio, data_fim)

            # Accept multiple shapes from utils: {'top_combos': [...] } or {'combos': [...] } or a bare list
            combos_raw = []
            if isinstance(data, dict):
                combos_raw = data.get('top_combos') or data.get('combos') or []
            elif isinstance(data, (list, tuple)):
                combos_raw = list(data)

            normalized = []
            # Build two representations for compatibility:
            # - top_combos: list of { produtos: [...], quantidade: N }
            # - combos (paginated): list of { combinacao: 'A, B', quantidade: N }
            for c in combos_raw:
                if isinstance(c, dict):
                    # prefer explicit produtos array
                    produtos = c.get('produtos') if isinstance(c.get('produtos'), (list, tuple)) else None
                    if produtos is None:
                        # maybe the old shape stores a single string under 'combinacao'
                        comb = c.get('combinacao') or c.get('combo') or c.get('produtos_combined')
                        if isinstance(comb, str):
                            produtos = [p.trim() for p in comb.split(',')] if comb else []
                        else:
                            produtos = []
                    quantidade = c.get('quantidade') if c.get('quantidade') is not None else (c.get('qty') or c.get('count') or 0)
                else:
                    # unsupported raw item type — coerce to string
                    produtos = [str(c)]
                    quantidade = 0
                try:
                    quantidade = int(quantidade)
                except Exception:
                    quantidade = 0
                normalized.append({'produtos': produtos, 'quantidade': quantidade})

            # server-side slicing by max_items keeps payload small for clients
            top_combos = normalized[:max_items]

            # also prepare paginated "combos" for older frontend clients that expect a string
            combos_str = [{'combinacao': ', '.join(c.get('produtos') or []), 'quantidade': c.get('quantidade', 0)} for c in normalized]
            total_pages = max(1, (len(combos_str) + per_page - 1) // per_page)
            page = max(1, min(page, total_pages))
            start = (page - 1) * per_page
            end = start + per_page
            paginated = combos_str[start:end]

            return Response({'top_combos': top_combos, 'combos': paginated, 'page': page, 'total': total_pages})
        except Exception as e:
            import logging
            logging.getLogger('dashboard_Maria').exception('CardMixProdutosAPIView error: %s', e)
            return Response({'error': 'Erro ao gerar relatório de mix de produtos.'}, status=500)

class CardClientesFrequentesAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_clientes_frequentes(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardClientesAusentesAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        page = int(request.GET.get('page', 1))
        per_page = 5
        data = get_clientes_ausentes(loja, canal, data_inicio, data_fim)
        items = data['clientes_ausentes']
        total_pages = max(1, (len(items) + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = items[start:end]
        return Response({'clientes_ausentes': paginated, 'page': page, 'total': total_pages})

class CardNovosClientesAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        page = int(request.GET.get('page', 1))
        per_page = 5
        data = get_novos_clientes(loja, canal, data_inicio, data_fim)
        items = data['novos_clientes']
        
        items = sorted(items, key=lambda x: x['primeira_compra'], reverse=True)
        total_pages = max(1, (len(items) + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = items[start:end]
        return Response({'novos_clientes': paginated, 'page': page, 'total': total_pages})

class CardRetencaoClientesAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        mes_inicio = request.GET.get('mes_inicio')
        mes_fim = request.GET.get('mes_fim')
        data = get_retencao_clientes(loja, canal, data_inicio, data_fim, mes_inicio, mes_fim)
        return Response(data)
        mes_inicio = request.GET.get('mes_inicio')
        mes_fim = request.GET.get('mes_fim')
        if not loja or not data_inicio or not data_fim:
            return Response({
                'matriz': [],
                'info': 'É preciso informar loja + data inicial + data final para que o card retorne resultados.'
            }, status=400)
        data = get_retencao_clientes(loja, canal, data_inicio, data_fim, mes_inicio, mes_fim)
        return Response(data)

class CardLifetimeValueAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_lifetime_value(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardPerformancePorCanalAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_performance_por_canal(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardPerformancePorLojaAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        page = int(request.GET.get('page', 1))
        per_page = 5
        data = get_performance_por_loja(loja, canal, data_inicio, data_fim)
        items = data['comparativo_loja']
        total_pages = max(1, (len(items) + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = items[start:end]
        return Response({'comparativo_loja': paginated, 'page': page, 'total': total_pages})

class CardAnomaliasTemporaisAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_anomalias_temporais(loja, canal, data_inicio, data_fim)
        return Response(data)

class CardPrevisaoDemandaAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        data = get_previsao_demanda(loja, canal, data_inicio, data_fim)
        return Response(data)


# --- Novos endpoints agregados/insights ---
class CardProdutoSazonalAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        from .utils import get_produto_sazonal
        data = get_produto_sazonal(loja, canal, data_inicio, data_fim)
        return Response(data)


class CardCrescimentoLojaAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        from .utils import get_performance_por_loja
        data = get_performance_por_loja(loja, canal, data_inicio, data_fim, granularity='month')

        monthly = data.get('monthly', []) if isinstance(data, dict) else []
        crescimento = data.get('crescimento_loja', []) if isinstance(data, dict) else []

        labels = [m.get('mes') for m in monthly]
        revenue = [m.get('faturamento') for m in monthly]
        sales = [m.get('vendas') for m in monthly]

        cres_map = { c.get('mes'): c.get('crescimento_combined_pct') for c in crescimento }
        combined_series = [ cres_map.get(lbl, None) for lbl in labels ]

        latest = None
        message = ''
        trend = 'stable'
        if crescimento:
            latest = crescimento[-1]
            comb = latest.get('crescimento_combined_pct')
            rev = latest.get('crescimento_revenue_pct')
            sel = latest.get('crescimento_sales_pct')
            if comb is not None:
                if comb > 0:
                    trend = 'up'
                elif comb < 0:
                    trend = 'down'
                else:
                    trend = 'stable'
            # human readable message
            try:
                mes = latest.get('mes')
                message = f"Mês {mes}: crescimento combinado {round(comb,2) if comb is not None else 'N/A'}% (receita {round(rev,2) if rev is not None else 'N/A'}%, vendas {round(sel,2) if sel is not None else 'N/A'}%)"
            except Exception:
                message = ''

        payload = {
            'monthly': monthly,
            'chart': {
                'labels': labels,
                'revenue': revenue,
                'sales': sales
            },
            'series': {
                'combined_pct': combined_series
            },
            'latest': latest,
            'trend': trend,
            'message': message,
            'weights': data.get('weights') if isinstance(data, dict) else None
        }

        return Response(payload)

class CardMixProdutosGlobalAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        return Response({'error': 'Endpoint removido. Use /api/card-mix-produtos/.'}, status=410)

class CardAnomaliasOperacionaisAPIView(APIView):
    def get(self, request):
        loja, canal, data_inicio, data_fim = parse_filters(request)
        from .utils import get_anomalias_operacionais
        data = get_anomalias_operacionais(loja, canal, data_inicio, data_fim)
        return Response(data)


 

