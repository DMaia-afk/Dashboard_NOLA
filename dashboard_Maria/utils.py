# utils.py - Funções otimizadas para os 20 cards do dashboard
from django.db import connection
from django.db.utils import OperationalError
import logging
from datetime import datetime, timedelta

def get_top_complementos_global(tipo='adicionados'):
	"""
	Retorna os complementos mais comuns globalmente (sem filtros de loja/canal/data).
	tipo = 'adicionados' (default) ou 'removidos'
	Retorna uma lista simples de dicionários: [ {'item': str, 'quantidade': int, 'receita': float}, ... ]
	"""
	filtro = "WHERE s.sale_status_desc = 'COMPLETED'"
	if tipo == 'removidos':
		filtro += " AND og.name ILIKE '%remover%'"
	else:
		filtro += " AND og.name NOT ILIKE '%remover%'"

	sql = f"""
		SELECT i.name AS item, COUNT(*) AS vezes, SUM(ips.additional_price) AS receita
		FROM item_product_sales ips
		JOIN items i ON i.id = ips.item_id
		JOIN option_groups og ON og.id = ips.option_group_id
		JOIN product_sales ps ON ps.id = ips.product_sale_id
		JOIN sales s ON s.id = ps.sale_id
		{filtro}
		GROUP BY i.name
		ORDER BY vezes DESC
		LIMIT 10
	"""
	try:
		result = run_query(sql, [])
		top = []
		for r in result:
			top.append({
				'item': r[0],
				'quantidade': int(r[1]) if r[1] is not None else 0,
				'receita': float(r[2]) if r[2] is not None else 0.0
			})
		return top
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('[get_top_complementos_global] Exception')
		return []

def get_complementos_mais_removidos(loja, canal, data_inicio, data_fim):
	filtro_sql = ["s.sale_status_desc = 'COMPLETED'", "og.name ILIKE '%remover%'"]
	params = []
	if loja:
		loja = loja.strip()
		if loja:
			filtro_sql.append("st.name = %s")
			params.append(loja)
	if canal:
		canal = canal.strip()
		if canal:
			filtro_sql.append("ch.name = %s")
			params.append(canal)
	data_inicio = str(data_inicio).strip() if data_inicio else None
	data_fim = str(data_fim).strip() if data_fim else None
	try:
		datetime.strptime(data_inicio, '%Y-%m-%d')
		datetime.strptime(data_fim, '%Y-%m-%d')
		filtro_sql.append("DATE(s.created_at) BETWEEN %s AND %s")
		params.extend([data_inicio, data_fim])
	except Exception:
		
		return {'top_complementos': []}
	where_clause = " WHERE " + " AND ".join(filtro_sql)
	sql = f'''
		SELECT i.name AS item, COUNT(*) AS vezes_removido, SUM(ips.additional_price) AS receita_gerada
		FROM item_product_sales ips
		JOIN items i ON i.id = ips.item_id
		JOIN option_groups og ON og.id = ips.option_group_id
		JOIN product_sales ps ON ps.id = ips.product_sale_id
		JOIN sales s ON s.id = ps.sale_id
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{where_clause}
		GROUP BY i.name
		ORDER BY vezes_removido DESC
	'''
	try:
		result = run_query(sql, params)
		top_complementos = []
		for r in result:
			if r and len(r) >= 3 and r[0] is not None:
				item = r[0]
				quantidade = int(r[1]) if r[1] is not None else 0
				receita = float(r[2]) if r[2] is not None else 0.0
				top_complementos.append({'item': item, 'quantidade': quantidade, 'receita': receita})
		return {'top_complementos': top_complementos}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('[get_complementos_mais_removidos] Exception')
		return {'top_complementos': []}

def get_complementos_mais_adicionados(loja, canal, data_inicio, data_fim):
	"""
	Compat shim: retorna complementos mais adicionados no período.
	Proxy para get_itens_complementos_mais_vendidos (comportamento 'adicionados').
	Retorna {'top_complementos': [...]} 
	"""
	try:
		
		res = get_itens_complementos_mais_vendidos(loja, canal, data_inicio, data_fim, request=None)
		
		if isinstance(res, dict) and 'top_complementos' in res:
			return res
		# se a função proxy retornou uma lista, envolva-a
		if isinstance(res, list):
			return {'top_complementos': res}
		# caso contrário vazio
		return {'top_complementos': []}
	except Exception:
		logging.getLogger('dashboard_Maria').exception('[get_complementos_mais_adicionados] Exception')
		return {'top_complementos': []}

def parse_filters(request):
	"""
	Extrai filtros de loja, canal e período da request.
	"""
	loja = request.GET.get('loja')
	canal = request.GET.get('canal')
	data_inicio = request.GET.get('data_inicio')
	data_fim = request.GET.get('data_fim')
	
	min_date = datetime.strptime('2025-05-03', '%Y-%m-%d').date()
	max_date = datetime.now().date() - timedelta(days=1)
	if not data_inicio:
		data_inicio = min_date.strftime('%Y-%m-%d')
	if not data_fim:
		data_fim = max_date.strftime('%Y-%m-%d')
	# Garante que os filtros não ultrapassem os limites
	data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
	data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
	if data_inicio_dt < min_date:
		data_inicio = min_date.strftime('%Y-%m-%d')
	if data_fim_dt > max_date:
		data_fim = max_date.strftime('%Y-%m-%d')
	return loja, canal, data_inicio, data_fim

def run_query(sql, params=None):
	"""
	Executa uma query SQL e retorna todos os resultados.
	"""
	logger = logging.getLogger('dashboard_Maria')
	with connection.cursor() as cursor:
		
		if params is None:
			_bind_params = []
		elif isinstance(params, (list, tuple)):
			_bind_params = params
		else:
			
			_bind_params = [params]
		try:
			
			try:
				placeholder_count = sql.count('%s')
			except Exception:
				placeholder_count = None
			if placeholder_count is not None and isinstance(placeholder_count, int):
				if placeholder_count > len(_bind_params):
					
					logger.error('run_query: placeholder count (%d) > params provided (%d) — aborting execution to avoid IndexError', placeholder_count, len(_bind_params))
					return []
			cursor.execute(sql, _bind_params)
			return cursor.fetchall()
		except OperationalError as e:
			
			exc_name = type(e).__name__
			exc_msg = str(e)
			hint = (
				"Possible causes: PostgreSQL server ran out of disk space or /dev/shm (shared memory) is full. "
				"On Linux check `df -h` and `df -h /dev/shm`; for Docker increase `--shm-size` or remount `/dev/shm` with a larger size. "
				"You can also inspect PostgreSQL server logs and kernel shm settings (kernel.shmmax / kernel.shmall)."
			)
			try:
				logger.exception(
					"OperationalError in run_query (%s): %s | SQL: %.200s | params_len=%d | hint: %s",
					exc_name, exc_msg, sql, len(_bind_params), hint
				)
			except Exception:
				# Logging de fallback se a formatação do SQL/params falhar por algum motivo
				logger.exception("OperationalError in run_query (%s): %s | hint: %s", exc_name, exc_msg, hint)
			return []
		except Exception as e:
			# Exceção genérica ao executar query (ex., ProgrammingError, InterfaceError, etc.)
			try:
				params_preview = repr(_bind_params)[:800]
				logger.exception("Error executing query in run_query: %s | SQL: %.400s | params=%s", e, sql, params_preview)
			except Exception:
				# Logger de fallback se a formatação falhar
				logger.exception("Error executing query in run_query and failed to format SQL/params: %s", e)
			return []

def run_query_one(sql, params=None):
	"""
	Executa uma query SQL e retorna o primeiro resultado.
	"""
	logger = logging.getLogger('dashboard_Maria')
	with connection.cursor() as cursor:
		try:
			cursor.execute(sql, params or [])
			return cursor.fetchone()
		except OperationalError as e:
			
			exc_name = type(e).__name__
			exc_msg = str(e)
			hint = (
				"Possible causes: PostgreSQL server ran out of disk or shared memory (/dev/shm). "
				"Check server disk usage (df -h) and /dev/shm size; in Docker adjust --shm-size."
			)
			logger.exception("OperationalError in run_query_one (%s): %s | hint: %s", exc_name, exc_msg, hint)
			return None
		except Exception as e:
			logger.exception("Error executing query in run_query_one: %s", e)
			return None

def filter_sales(loja, canal, data_inicio, data_fim):
	"""
	Monta filtro SQL para vendas por loja, canal e período.
	"""
	filtro = "WHERE s.sale_status_desc = 'COMPLETED'"
	params = []
	if loja:
		filtro += " AND st.name = %s"
		params.append(loja)
	if canal:
		filtro += " AND ch.name = %s"
		params.append(canal)
	filtro += " AND DATE(s.created_at) BETWEEN %s AND %s"
	params.extend([data_inicio, data_fim])
	return filtro, params

# Funções otimizadas para cada card
def get_faturamento_total(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	
	sql_total = f"""
		SELECT SUM(s.total_amount) AS valor_total
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
	"""
	result_total = run_query_one(sql_total, params)
	valor_total = float(result_total[0]) if result_total and result_total[0] else 0.0

	# Faturamento por mês
	sql_mensal = f"""
		SELECT DATE_TRUNC('month', s.created_at) AS mes, SUM(s.total_amount) AS faturamento
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY mes
		ORDER BY mes
	"""
	result_mensal = run_query(sql_mensal, params)
	faturamento_mensal = [
		{'mes': r[0].strftime('%Y-%m'), 'faturamento': float(r[1])} for r in result_mensal
	]
	return {
		'valor_total': valor_total,
		'faturamento_mensal': faturamento_mensal
	}

def get_ticket_medio(loja, canal, data_inicio, data_fim):
	"""
	Retorna o ticket médio geral e por canal, incluindo min/max para formar um intervalo.
	Estrutura retornada:
	{
		'ticket_medio': float,
		'por_canal': [ {'canal': str, 'ticket_medio': float, 'min_ticket': float, 'max_ticket': float}, ... ]
	}
	"""
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# Ticket médio geral + mediana e total de vendas
	sql_overall = f"""
		SELECT AVG(s.total_amount) AS ticket_medio,
			percentile_cont(0.5) WITHIN GROUP (ORDER BY s.total_amount) AS median_ticket,
			COUNT(*) AS total_vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
	"""
	overall = run_query_one(sql_overall, params)
	overall_avg = float(overall[0]) if overall and overall[0] is not None else 0.0
	overall_median = float(overall[1]) if overall and overall[1] is not None else 0.0
	total_vendas = int(overall[2]) if overall and overall[2] is not None else 0

	# Ticket médio por canal com mediana/min/max e contagem
	sql_canal = f"""
		SELECT ch.name,
			AVG(s.total_amount) AS avg_ticket,
			percentile_cont(0.5) WITHIN GROUP (ORDER BY s.total_amount) AS median_ticket,
			MIN(s.total_amount) AS min_ticket,
			MAX(s.total_amount) AS max_ticket,
			COUNT(*) AS vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY ch.name
		ORDER BY avg_ticket DESC
		"""
	result = run_query(sql_canal, params)
	por_canal = []
	# total_vendas pode ser zero (sem dados); evitar divisão por zero
	total_vendas_safe = total_vendas if total_vendas else sum([int(r[5]) if r and len(r) > 5 and r[5] is not None else 0 for r in result])
	for r in result:
		try:
			canal_nome = r[0]
			avg_ticket = float(r[1]) if r[1] is not None else 0.0
			median_ticket = float(r[2]) if r[2] is not None else 0.0
			min_ticket = float(r[3]) if r[3] is not None else 0.0
			max_ticket = float(r[4]) if r[4] is not None else 0.0
			vendas = int(r[5]) if r[5] is not None else 0
			# share do canal nas vendas totais e % diff em relação ao geral
			share = (vendas / total_vendas_safe * 100.0) if total_vendas_safe else 0.0
			pct_diff = ((avg_ticket - overall_avg) / overall_avg * 100.0) if overall_avg else 0.0
			low_volume = True if total_vendas_safe and (share < 5.0) else False
			por_canal.append({
				'canal': canal_nome,
				'ticket_medio': round(avg_ticket,2),
				'median_ticket': round(median_ticket,2),
				'min_ticket': round(min_ticket,2),
				'max_ticket': round(max_ticket,2),
				'vendas': vendas,
				'share_percent': round(share,2),
				'pct_diff_vs_overall': round(pct_diff,2),
				'low_volume': low_volume
			})
		except Exception:
			continue

	return {'ticket_medio': round(overall_avg,2), 'ticket_median': round(overall_median,2), 'total_vendas': total_vendas, 'por_canal': por_canal}

def get_vendas_por_dia_hora(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT EXTRACT(DOW FROM s.created_at) AS dia_semana, EXTRACT(HOUR FROM s.created_at) AS hora, COUNT(*) AS vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY dia_semana, hora
		ORDER BY dia_semana, hora
		"""
	result = run_query(sql, params)
	# Monta estrutura tanto para heatmap quanto para charts simples
	heatmap = [ {'dia_semana': int(r[0]), 'hora': int(r[1]), 'vendas': int(r[2])} for r in result ]
	# Labels legíveis: ex "Seg 11h"
	day_names = {0: 'Dom', 1: 'Seg', 2: 'Ter', 3: 'Qua', 4: 'Qui', 5: 'Sex', 6: 'Sáb'}
	labels = [ f"{day_names.get(item['dia_semana'], item['dia_semana'])} {item['hora']}h" for item in heatmap ]
	valores = [ item['vendas'] for item in heatmap ]
	return {'heatmap': heatmap, 'labels': labels, 'valores': valores}

def get_produtos_mais_vendidos(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT p.name, SUM(ps.quantity) AS quantidade, SUM(ps.quantity * ps.base_price) AS receita
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN product_sales ps ON ps.sale_id = s.id
		JOIN products p ON p.id = ps.product_id
		{filtro}
		GROUP BY p.name
		ORDER BY receita DESC
		LIMIT 10
	"""
	result = run_query(sql, params)
	return {'top_produtos': [ {'produto': r[0], 'quantidade': int(r[1]), 'receita': float(r[2])} for r in result ]}

def get_produtos_menos_vendidos(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT p.name, SUM(ps.quantity) AS quantidade, SUM(ps.quantity * ps.base_price) AS receita
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN product_sales ps ON ps.sale_id = s.id
		JOIN products p ON p.id = ps.product_id
		{filtro}
		GROUP BY p.name
		ORDER BY receita ASC
		LIMIT 10
	"""
	result = run_query(sql, params)
	return {'bottom_produtos': [ {'produto': r[0], 'quantidade': int(r[1]), 'receita': float(r[2])} for r in result ]}


# Card 6: Produtos Mais Customizados
def get_produtos_mais_customizados(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# Query primária baseada em observações registradas em product_sales
	sql = f"""
		SELECT p.name, COUNT(DISTINCT ps.observations) AS customizacoes, SUM(ps.quantity * ps.base_price) AS receita
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN product_sales ps ON ps.sale_id = s.id
		JOIN products p ON p.id = ps.product_id
		{filtro} AND ps.observations IS NOT NULL AND ps.observations != ''
		GROUP BY p.name
		ORDER BY customizacoes DESC
		LIMIT 10
	"""
	result = run_query(sql, params)
	if result and len(result) > 0:
		return {'top_customizacoes': [ {'produto': r[0], 'customizacoes': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in result ]}

	# Fallback: se não houver observações textuais, inferir customizações pelos itens associados (item_product_sales)
	try:
		fallback_sql = f"""
			SELECT p.name, COUNT(ips.id) AS customizacoes, SUM(ps.quantity * ps.base_price) AS receita
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			JOIN product_sales ps ON ps.sale_id = s.id
			JOIN products p ON p.id = ps.product_id
			JOIN item_product_sales ips ON ips.product_sale_id = ps.id
			{filtro}
			GROUP BY p.name
			ORDER BY customizacoes DESC
			LIMIT 10
		"""
		fb_result = run_query(fallback_sql, params)
		if fb_result and len(fb_result) > 0:
			return {'top_customizacoes': [ {'produto': r[0], 'customizacoes': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in fb_result ]}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('[get_produtos_mais_customizados] fallback exception')

	# Sem dados
	return {'top_customizacoes': []}

# Card 7: Itens/Complementos Mais Vendidos
def get_itens_complementos_mais_vendidos(loja, canal, data_inicio, data_fim, request=None):
	import logging
	logger = logging.getLogger("dashboard_maria")
	try:
		tipo = None
		# Suporte ao filtro via query param: ?tipo=adicionados ou ?tipo=removidos
		import inspect
		frame = inspect.currentframe()
		if request is None:
			request = frame.f_back.f_locals.get('request')
		logger.info(f"[Complementos] Parâmetros recebidos: loja={loja}, canal={canal}, data_inicio={data_inicio}, data_fim={data_fim}, request={request}")
		if request:
			tipo = request.GET.get('tipo', 'adicionados')   
		logger.info(f"[Complementos] Tipo de filtro: {tipo}")
		filtro_sql = "WHERE s.sale_status_desc = 'COMPLETED'"
		params = []
		if loja:
			filtro_sql += " AND st.name = %s"
			params.append(loja)
		if canal:
			filtro_sql += " AND ch.name = %s"
			params.append(canal)
		filtro_sql += " AND DATE(s.created_at) BETWEEN %s AND %s"
		params.extend([data_inicio, data_fim])

		if tipo == 'removidos':
			sql = f'''
				SELECT i.name AS item, COUNT(*) AS times_removed, SUM(ips.additional_price) AS receita
				FROM item_product_sales ips
				JOIN items i ON i.id = ips.item_id
				JOIN option_groups og ON og.id = ips.option_group_id
				JOIN product_sales ps ON ps.id = ips.product_sale_id
				JOIN sales s ON s.id = ps.sale_id
				JOIN stores st ON st.id = s.store_id
				JOIN channels ch ON ch.id = s.channel_id
				{filtro_sql} AND og.name ILIKE '%remover%'
				GROUP BY i.name
				ORDER BY times_removed DESC
				LIMIT 10
			'''
			logger.info(f"[Complementos] Executando SQL (removidos): {sql}")
			result = run_query(sql, params)
			logger.info(f"[Complementos] Resultados removidos: {result}")
			if not result or len(result) == 0:
				return {'top_complementos': []}
			safe_result = [r for r in result if r and len(r) >= 3 and r[0] is not None]
			return {'top_complementos': [ {'item': r[0], 'quantidade': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in safe_result]}
		else:
			sql = f'''
				SELECT i.name AS item, COUNT(*) AS times_added, SUM(ips.additional_price) AS receita
				FROM item_product_sales ips
				JOIN items i ON i.id = ips.item_id
				JOIN option_groups og ON og.id = ips.option_group_id
				JOIN product_sales ps ON ps.id = ips.product_sale_id
				JOIN sales s ON s.id = ps.sale_id
				JOIN stores st ON st.id = s.store_id
				JOIN channels ch ON ch.id = s.channel_id
				{filtro_sql} AND og.name NOT ILIKE '%remover%'
				GROUP BY i.name
				ORDER BY times_added DESC
				LIMIT 10
			'''
			logger.info(f"[Complementos] Executando SQL (adicionados): {sql}")
			result = run_query(sql, params)
			logger.info(f"[Complementos] Resultados adicionados: {result}")
			if not result or len(result) == 0:
				return {'top_complementos': []}
			safe_result = [r for r in result if r and len(r) >= 3 and r[0] is not None]
			return {'top_complementos': [ {'item': r[0], 'quantidade': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in safe_result]}
	except Exception as e:
		logger.error(f"[Complementos] Erro: {e}")
		return {'top_complementos': []}

# Card 8: Taxa de Cancelamento
def get_taxa_cancelamento(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# Total de vendas
	sql_total = f"""
		SELECT COUNT(*) FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		WHERE DATE(s.created_at) BETWEEN %s AND %s
	"""
	total = run_query_one(sql_total, [data_inicio, data_fim])
	# Canceladas
	sql_cancel = f"""
		SELECT COUNT(*) FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		WHERE s.sale_status_desc = 'CANCELLED' AND DATE(s.created_at) BETWEEN %s AND %s
	"""
	canceladas = run_query_one(sql_cancel, [data_inicio, data_fim])
	taxa = (canceladas[0] / total[0] * 100) if total and total[0] else 0.0
	return {'taxa_cancelamento': round(taxa,2)}


def get_taxa_cancelamento_detailed(loja, canal, data_inicio, data_fim):
	"""Return detailed cancellation metrics for the Taxa de Cancelamento card.

	Structure returned:
	{
	  'taxa_cancelamento': float,
	  'timeseries': { 'labels': [...], 'values': [...] },  # % canceled per month
	  'por_canal': [ {'canal': str, 'pct': float, 'n_canceladas': int, 'n_vendas': int}, ... ],
	  'top_produtos_em_vendas_canceladas': [ {'produto': str, 'quantidade': int, 'receita': float}, ... ],
	  'buckets': [ {'label': str, 'count': int}, ... ]  # buckets by cancelled sale amount
	}
	"""
	try:
		# build a where clause that does NOT force sale_status_desc = 'COMPLETED'
		where_parts = []
		params = []
		# date range always required
		where_parts.append("DATE(s.created_at) BETWEEN %s AND %s")
		params.extend([data_inicio, data_fim])
		if loja:
			where_parts.append("st.name = %s")
			params.append(loja)
		if canal:
			where_parts.append("ch.name = %s")
			params.append(canal)
		where_clause = "WHERE " + " AND ".join(where_parts)

		# overall rate
		sql_total = f"""
			SELECT COUNT(*) FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			WHERE DATE(s.created_at) BETWEEN %s AND %s
		"""
		total = run_query_one(sql_total, [data_inicio, data_fim])
		sql_cancel = f"""
			SELECT COUNT(*) FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			WHERE s.sale_status_desc = 'CANCELLED' AND DATE(s.created_at) BETWEEN %s AND %s
		"""
		canceladas = run_query_one(sql_cancel, [data_inicio, data_fim])
		taxa = (canceladas[0] / total[0] * 100) if total and total[0] else 0.0

		# timeseries per month: percentage cancelled per month
		sql_ts = f"""
			SELECT TO_CHAR(DATE_TRUNC('month', s.created_at), 'YYYY-MM') AS mes,
				   SUM(CASE WHEN s.sale_status_desc = 'CANCELLED' THEN 1 ELSE 0 END) AS n_canceladas,
				   COUNT(*) AS n_vendas
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{where_clause}
			GROUP BY mes
			ORDER BY mes
		"""
		res_ts = run_query(sql_ts, params)
		labels = [r[0] for r in res_ts]
		values = [ (r[1] / r[2] * 100.0) if r[2] else 0.0 for r in res_ts ]

		# breakdown by channel
		sql_canal = f"""
			SELECT ch.name, SUM(CASE WHEN s.sale_status_desc = 'CANCELLED' THEN 1 ELSE 0 END) AS n_canceladas, COUNT(*) AS n_vendas
			FROM sales s
			JOIN channels ch ON ch.id = s.channel_id
			JOIN stores st ON st.id = s.store_id
			{where_clause}
			GROUP BY ch.name
			ORDER BY n_canceladas DESC
		"""
		res_canal = run_query(sql_canal, params)
		por_canal = []
		for r in res_canal:
			nome = r[0]
			n_cancel = int(r[1]) if r[1] is not None else 0
			n_tot = int(r[2]) if r[2] is not None else 0
			pct = (n_cancel / n_tot * 100.0) if n_tot else 0.0
			por_canal.append({'canal': nome, 'pct': round(pct,2), 'n_canceladas': n_cancel, 'n_vendas': n_tot})

		# top products within cancelled sales
		sql_top_prod = f"""
			SELECT p.name, SUM(ps.quantity) AS quantidade, SUM(ps.quantity * ps.base_price) AS receita
			FROM product_sales ps
			JOIN sales s ON s.id = ps.sale_id
			JOIN products p ON p.id = ps.product_id
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{where_clause} AND s.sale_status_desc = 'CANCELLED'
			GROUP BY p.name
			ORDER BY quantidade DESC
			LIMIT 5
		"""
		res_top = run_query(sql_top_prod, params)
		top_produtos = [ {'produto': r[0], 'quantidade': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in res_top ]

		# buckets by cancelled sale amount (BRL): 0-20,20-50,50-100,100-200,200+
		sql_buckets = f"""
			SELECT bucket, COUNT(*) FROM (
				SELECT CASE
					WHEN s.total_amount IS NULL OR s.total_amount <= 20 THEN '0-20'
					WHEN s.total_amount <= 50 THEN '20-50'
					WHEN s.total_amount <= 100 THEN '50-100'
					WHEN s.total_amount <= 200 THEN '100-200'
					ELSE '200+'
				END AS bucket
				FROM sales s
				JOIN stores st ON st.id = s.store_id
				JOIN channels ch ON ch.id = s.channel_id
				{where_clause} AND s.sale_status_desc = 'CANCELLED'
			) t
			GROUP BY bucket
			ORDER BY COUNT(*) DESC
		"""
		res_b = run_query(sql_buckets, params)
		bucket_map = { r[0]: int(r[1]) for r in res_b }
		order = ['0-20', '20-50', '50-100', '100-200', '200+']
		buckets = [ {'label': lab, 'count': bucket_map.get(lab, 0)} for lab in order ]

		monetary = compute_monetary_impact_cancelamentos(loja, canal, data_inicio, data_fim)
		cancelled_amount = monetary.get('total_lost_revenue') if isinstance(monetary, dict) else None
		total_revenue = monetary.get('total_revenue') if isinstance(monetary, dict) else None
		total_cancelled_count = monetary.get('n_cancelled') if isinstance(monetary, dict) else None

		return {
			'taxa_cancelamento': round(taxa,2),
			'timeseries': { 'labels': labels, 'values': [ round(v,2) for v in values ] },
			'por_canal': por_canal,
			'top_produtos_em_vendas_canceladas': top_produtos,
			'buckets': buckets,
			'monetary_impact': monetary,
			'cancelled_amount': cancelled_amount,
			'total_revenue': total_revenue,
			'total_cancelled_count': total_cancelled_count
		}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('get_taxa_cancelamento_detailed error: %s', e)
		return {'taxa_cancelamento': round(taxa if 'taxa' in locals() else 0.0,2), 'timeseries': {'labels':[], 'values':[]}, 'por_canal': [], 'top_produtos_em_vendas_canceladas': [], 'buckets': [], 'monetary_impact': {'total_lost_revenue': 0.0, 'n_cancelled': 0, 'pct_of_revenue': 0.0}}

# Card 9: Taxa de Desconto
def get_taxa_desconto(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql_total = f"""
		SELECT COUNT(*) FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		WHERE DATE(s.created_at) BETWEEN %s AND %s
	"""
	total = run_query_one(sql_total, [data_inicio, data_fim])
	sql_desc = f"""
		SELECT COUNT(*) FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		WHERE s.total_discount > 0 AND DATE(s.created_at) BETWEEN %s AND %s
	"""
	descontos = run_query_one(sql_desc, [data_inicio, data_fim])
	taxa = (descontos[0] / total[0] * 100) if total and total[0] else 0.0
	return {'taxa_desconto': round(taxa,2)}


def get_taxa_desconto_detailed(loja, canal, data_inicio, data_fim):
	"""Return detailed discount metrics for the Taxa de Desconto card.

	Returns structure:
	{
		'taxa_desconto': float,
		'timeseries': { 'labels': [...], 'values': [...] },  # percentual por mês
		'por_canal': [ {'canal': str, 'pct': float, 'n_descontos': int, 'n_vendas': int}, ... ],
		'top_produtos_com_desconto': [ {'produto': str, 'quantidade': int, 'receita': float}, ... ],
		'buckets': [ {'label': '0-5%', 'count': int}, ... ]
	}
	"""
	try:
		filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
		# overall rate (reuse existing logic)
		sql_total = f"""
			SELECT COUNT(*) FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			WHERE DATE(s.created_at) BETWEEN %s AND %s
		"""
		total = run_query_one(sql_total, [data_inicio, data_fim])
		sql_desc = f"""
			SELECT COUNT(*) FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			WHERE s.total_discount > 0 AND DATE(s.created_at) BETWEEN %s AND %s
		"""
		descontos = run_query_one(sql_desc, [data_inicio, data_fim])
		taxa = (descontos[0] / total[0] * 100) if total and total[0] else 0.0

		# timeseries per month (% of sales in that month that had discount)
		sql_ts = f"""
			SELECT TO_CHAR(DATE_TRUNC('month', s.created_at), 'YYYY-MM') AS mes,
				   SUM(CASE WHEN s.total_discount > 0 THEN 1 ELSE 0 END) AS n_descontos,
				   COUNT(*) AS n_vendas
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro}
			GROUP BY mes
			ORDER BY mes
		"""
		res_ts = run_query(sql_ts, params)
		labels = [r[0] for r in res_ts]
		values = [ (r[1] / r[2] * 100.0) if r[2] else 0.0 for r in res_ts ]

		# breakdown by channel: percent of that channel's sales that had discount
		sql_canal = f"""
			SELECT ch.name, SUM(CASE WHEN s.total_discount > 0 THEN 1 ELSE 0 END) AS n_descontos, COUNT(*) AS n_vendas
			FROM sales s
			JOIN channels ch ON ch.id = s.channel_id
			JOIN stores st ON st.id = s.store_id
			{filtro}
			GROUP BY ch.name
			ORDER BY n_descontos DESC
		"""
		res_canal = run_query(sql_canal, params)
		por_canal = []
		for r in res_canal:
			nome = r[0]
			n_des = int(r[1]) if r[1] is not None else 0
			n_tot = int(r[2]) if r[2] is not None else 0
			pct = (n_des / n_tot * 100.0) if n_tot else 0.0
			por_canal.append({'canal': nome, 'pct': round(pct,2), 'n_descontos': n_des, 'n_vendas': n_tot})

		# top products involved in discounted sales (count of product quantities within sales that had discounts)
		sql_top_prod = f"""
			SELECT p.name, SUM(ps.quantity) AS quantidade, SUM(ps.quantity * ps.base_price) AS receita
			FROM product_sales ps
			JOIN sales s ON s.id = ps.sale_id
			JOIN products p ON p.id = ps.product_id
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro} AND s.total_discount > 0
			GROUP BY p.name
			ORDER BY quantidade DESC
			LIMIT 5
		"""
		res_top = run_query(sql_top_prod, params)
		top_produtos = [ {'produto': r[0], 'quantidade': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in res_top ]

		# buckets for relative discount percent per sale (total_discount / total_amount *100)
		# ranges: 0-5,5-10,10-20,20-50,50+
		sql_buckets = f"""
			SELECT bucket, COUNT(*) FROM (
				SELECT CASE
					WHEN s.total_amount IS NULL OR s.total_amount = 0 THEN '0%'
					WHEN (s.total_discount / NULLIF(s.total_amount,0.0) * 100.0) <= 5 THEN '0-5%'
					WHEN (s.total_discount / NULLIF(s.total_amount,0.0) * 100.0) <= 10 THEN '5-10%'
					WHEN (s.total_discount / NULLIF(s.total_amount,0.0) * 100.0) <= 20 THEN '10-20%'
					WHEN (s.total_discount / NULLIF(s.total_amount,0.0) * 100.0) <= 50 THEN '20-50%'
					ELSE '50%+'
				END AS bucket
				FROM sales s
				JOIN stores st ON st.id = s.store_id
				JOIN channels ch ON ch.id = s.channel_id
				{filtro}
			) t
			GROUP BY bucket
			ORDER BY COUNT(*) DESC
		"""
		res_b = run_query(sql_buckets, params)
		# Normalize to a predictable order
		order = ['0%', '0-5%', '5-10%', '10-20%', '20-50%', '50%+']
		bucket_map = { r[0]: int(r[1]) for r in res_b }
		buckets = [ {'label': lab, 'count': bucket_map.get(lab, 0)} for lab in order ]

		return {
			'taxa_desconto': round(taxa,2),
			'timeseries': { 'labels': labels, 'values': [ round(v,2) for v in values ] },
			'por_canal': por_canal,
			'top_produtos_com_desconto': top_produtos,
			'buckets': buckets,
			'monetary_impact': compute_monetary_impact_descontos(loja, canal, data_inicio, data_fim)
		}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('get_taxa_desconto_detailed error: %s', e)
		return {'taxa_desconto': round(taxa if 'taxa' in locals() else 0.0,2), 'timeseries': {'labels':[], 'values':[]}, 'por_canal': [], 'top_produtos_com_desconto': [], 'buckets': [], 'monetary_impact': {'total_discount': 0.0, 'avg_discount_per_sale': 0.0, 'pct_of_revenue': 0.0}}

# Card 10: Performance de Entrega por Região
def get_performance_entrega_regiao(loja, canal, data_inicio, data_fim):
	try:
		filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
		sql = f"""
			SELECT da.city, da.neighborhood, AVG(s.delivery_seconds)/60.0 AS tempo_medio_min
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			JOIN delivery_addresses da ON da.sale_id = s.id
			{filtro}
			GROUP BY da.city, da.neighborhood
			ORDER BY tempo_medio_min DESC
		"""
		result = run_query(sql, params)
		return {'tempo_entrega': [ {'cidade': r[0], 'bairro': r[1], 'tempo_medio_min': float(r[2])} for r in result if r[0] and r[1] and r[2] is not None ]}
	except Exception as e:
		return {'tempo_entrega': []}

# Card 11: Mix de Produtos
def get_mix_produtos(loja, canal, data_inicio, data_fim):
	# Compute top product combos across all completed sales.
	# Strategy:
	# 1) For each sale, build a deterministic combo key by concatenating product
	#    names ordered alphabetically using STRING_AGG(... ORDER BY p.name).
	# 2) Only consider combos with 2 or more distinct products (we're interested
	#    in products sold together).
	# 3) Aggregate combo frequencies in SQL and return the top N combos.

	# Apply loja/canal/data filters using filter_sales so the frontend filters work
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)

	sql = f"""
		WITH combos_per_sale AS (
			SELECT s.id AS sale_id,
				   STRING_AGG(DISTINCT p.name, '||' ORDER BY p.name) AS combo_key,
				   COUNT(DISTINCT p.id) AS produto_count
			FROM sales s
			JOIN product_sales ps ON ps.sale_id = s.id
			JOIN products p ON p.id = ps.product_id
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro}
			GROUP BY s.id
		)
		SELECT combo_key, COUNT(*) AS vezes
		FROM combos_per_sale
		WHERE produto_count >= 2
		GROUP BY combo_key
		ORDER BY vezes DESC
		LIMIT 200
	"""

	result = run_query(sql, params)
	combos = []
	for r in result:
		combo_key = r[0] or ''
		vezes = int(r[1]) if r[1] is not None else 0
		# restore product list from combo_key (separator '||')
		produtos = [p.strip() for p in combo_key.split('||') if p and p.strip()]
		if produtos:
			combos.append({'produtos': produtos, 'quantidade': vezes})

	# frontend expects 'top_combos' for this endpoint (renderMixProdutosCard)
	return {'top_combos': combos}


# Card 12: Clientes Frequentes
def get_clientes_frequentes(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT c.customer_name, COUNT(*) AS compras, AVG(s.total_amount) AS ticket_medio
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN customers c ON c.id = s.customer_id
		{filtro}
		GROUP BY c.customer_name
		ORDER BY compras DESC
		LIMIT 10
	"""
	result = run_query(sql, params)
	return {'top_clientes': [ {'cliente': r[0], 'compras': int(r[1]), 'ticket_medio': float(r[2])} for r in result ]}

# Card 13: Clientes Ausentes
def get_clientes_ausentes(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT c.customer_name, MAX(s.created_at) AS ultima_compra
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN customers c ON c.id = s.customer_id
		{filtro}
		GROUP BY c.customer_name
		HAVING MAX(s.created_at) < %s
		ORDER BY ultima_compra ASC
		LIMIT 10
	"""
	# Considera clientes que não compram há mais de 30 dias
	from datetime import timedelta
	ref_date = datetime.strptime(data_fim, '%Y-%m-%d') - timedelta(days=30)
	result = run_query(sql, params + [ref_date.strftime('%Y-%m-%d')])
	clientes = [ {'cliente': r[0], 'ultima_compra': str(r[1])} for r in result ]
	# If filters included a specific loja and a date range but there are no results,
	# return an info message so the frontend can inform the user explicitly.
	if (not clientes) and (loja and data_inicio and data_fim):
		loja_nome = (loja or '').strip()
		return {'clientes_ausentes': [], 'info': f'Nenhum cliente ausente encontrado para a loja "{loja_nome}" no período selecionado.'}
	return {'clientes_ausentes': clientes}

# Card 14: Novos Clientes
def get_novos_clientes(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT c.customer_name, MIN(s.created_at) AS primeira_compra, AVG(s.total_amount) AS ticket_medio
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN customers c ON c.id = s.customer_id
		{filtro}
		GROUP BY c.customer_name
		HAVING MIN(s.created_at) BETWEEN %s AND %s
		ORDER BY primeira_compra DESC
		LIMIT 10
	"""
	result = run_query(sql, params + [data_inicio, data_fim])
	novos = [ {'cliente': r[0], 'primeira_compra': str(r[1]), 'ticket_medio': float(r[2])} for r in result ]
	if (not novos) and (loja and data_inicio and data_fim):
		loja_nome = (loja or '').strip()
		return {'novos_clientes': [], 'info': f'Nenhum novo cliente encontrado para a loja "{loja_nome}" no período selecionado.'}
	return {'novos_clientes': novos}

# Card 15: Retenção de Clientes
def get_retencao_clientes(loja, canal, data_inicio, data_fim, mes_inicio=None, mes_fim=None):
	"""
	Retenção acumulada por coorte (mês). Retorna uma matriz compatível com o front-end:
	{'matriz': [ ['Loja','Mês','Clientes Coorte','Clientes Ativos','Taxa de Retenção (%)'], ... ]}
	Exige parâmetro `loja` (nome da loja).
	"""
	# Build the base filter WITHOUT embedding the loja name so we can
	# control how many times the loja parameter appears in the SQL (we
	# need to reuse the loja placeholder in multiple sub-clauses).
	filtro, params = filter_sales(None, canal, data_inicio, data_fim)
	# Garante que só retorna dados da loja informada
	loja_nome = (loja or '').strip()
	if not loja_nome:
		return {'matriz': [], 'info': 'É preciso informar a loja para visualizar a retenção.'}
	# Add loja constraint to the meses clause (first appearance) and
	# we will also bind loja twice more for the other WHEREs below.
	filtro_loja = filtro + " AND st.name = %s"
	params_loja = params + [loja_nome]

	sql = f"""
		WITH
		meses AS (
			SELECT DISTINCT DATE_TRUNC('month', s.created_at) AS mes
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro_loja}
		),
		coorte_acumulada AS (
			SELECT
				m.mes,
				s.store_id,
				s.customer_id
			FROM meses m
			JOIN sales s ON s.sale_status_desc = 'COMPLETED'
				AND s.customer_id IS NOT NULL
				AND DATE_TRUNC('month', s.created_at) <= m.mes
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			WHERE st.name = %s
			GROUP BY m.mes, s.store_id, s.customer_id
		),
		clientes_ativos AS (
			SELECT
				ca.mes,
				ca.store_id,
				COUNT(DISTINCT s.customer_id) AS clientes_ativos
			FROM coorte_acumulada ca
			JOIN sales s ON s.sale_status_desc = 'COMPLETED'
				AND s.customer_id = ca.customer_id
				AND s.store_id = ca.store_id
				AND DATE_TRUNC('month', s.created_at) = ca.mes
			GROUP BY ca.mes, ca.store_id
		),
		clientes_coorte AS (
			SELECT
				mes,
				store_id,
				COUNT(DISTINCT customer_id) AS clientes_coorte
			FROM coorte_acumulada
			GROUP BY mes, store_id
		)
		SELECT st.name AS loja, TO_CHAR(ca.mes, 'YYYY-MM') AS mes, cc.clientes_coorte, ca.clientes_ativos,
			ROUND((ca.clientes_ativos::numeric / NULLIF(cc.clientes_coorte, 0)) * 100, 2) AS taxa_retencao
		FROM clientes_ativos ca
		JOIN clientes_coorte cc ON cc.mes = ca.mes AND cc.store_id = ca.store_id
		JOIN stores st ON st.id = ca.store_id
		WHERE st.name = %s
		ORDER BY ca.mes, st.name;
	"""

	# Executa a query e monta a matriz
	# The SQL references the loja name in three places (meses, coorte_acumulada WHERE and final WHERE)
	# so we must provide the loja parameter three times in the same order as the placeholders.
	result = run_query(sql, params_loja + [loja_nome, loja_nome])
	if not result:
		return {'matriz': [], 'info': 'Nenhum dado de retenção encontrado para os filtros informados.'}

	header = ['Loja', 'Mês', 'Clientes Coorte', 'Clientes Ativos', 'Taxa de Retenção (%)']
	matriz = [header]
	for r in result:
		matriz.append([
			r[0], # loja
			r[1], # mes
			int(r[2]) if r[2] is not None else 0, # clientes_coorte
			int(r[3]) if r[3] is not None else 0, # clientes_ativos
			float(r[4]) if r[4] is not None else 0.0 # taxa_retencao
		])

	# Filtra matriz pelo intervalo de meses, se informado (formato 'YYYYMM' ou 'YYYY-MM')
	if mes_inicio or mes_fim:
		def normalize(m):
			return m.replace('-', '')
		mi = mes_inicio.replace('-', '') if mes_inicio else None
		mf = mes_fim.replace('-', '') if mes_fim else None
		matriz_filtrada = [header] + [row for row in matriz[1:] if ((not mi or normalize(row[1]) >= mi) and (not mf or normalize(row[1]) <= mf))]
		return {'matriz': matriz_filtrada}

	return {'matriz': matriz}

# Card 16: Lifetime Value (LTV)
def get_lifetime_value(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# LTV por cliente (top clientes)
	sql = f"""
		SELECT c.customer_name, SUM(s.total_amount) AS ltv
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN customers c ON c.id = s.customer_id
		{filtro}
		GROUP BY c.customer_name
		ORDER BY ltv DESC
		LIMIT 10
	"""
	result = run_query(sql, params)
	ltv_medio = sum([r[1] for r in result])/len(result) if result else 0.0
	ltv_clientes = [ {'cliente': r[0], 'ltv': float(r[1])} for r in result ]

	# LTV por canal (métrica A): faturamento total do canal / clientes únicos do canal
	sql_canal = f"""
		SELECT ch.name AS canal, SUM(s.total_amount) AS faturamento_canal, COUNT(DISTINCT s.customer_id) AS clientes_unicos
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY ch.name
		ORDER BY faturamento_canal DESC
	"""
	res_canal = run_query(sql_canal, params)
	ltv_por_canal = []
	for r in res_canal:
		canal = r[0]
		faturamento = float(r[1]) if r[1] is not None else 0.0
		clientes_unicos = int(r[2]) if r[2] is not None else 0
		ltv_c = round((faturamento / clientes_unicos) if clientes_unicos else 0.0, 2)
		ltv_por_canal.append({'canal': canal, 'ltv': ltv_c, 'faturamento': faturamento, 'clientes_unicos': clientes_unicos})

	return {'ltv_medio': round(ltv_medio,2), 'ltv_clientes': ltv_clientes, 'ltv_por_canal': ltv_por_canal}

# Card 17: Performance por Canal
def get_performance_por_canal(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT ch.name, SUM(s.total_amount) AS faturamento, AVG(s.total_amount) AS ticket_medio, COUNT(*) AS vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY ch.name
		ORDER BY faturamento DESC
	"""
	result = run_query(sql, params)
	return {'comparativo_canal': [ {'canal': r[0], 'faturamento': float(r[1]), 'ticket_medio': float(r[2]), 'vendas': int(r[3])} for r in result ]}

# Card 18: Performance por Loja
def get_performance_por_loja(loja, canal, data_inicio, data_fim, granularity=None):
	"""
	Quando `granularity == 'month'` retorna uma monthly timeseries para faturamento/vendas/avg_ticket
	e também a estrutura de crescimento semelhante a `get_crescimento_loja`.

	Caso contrário, preserva o comportamento anterior (comparativo por loja).
	"""
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)

	if granularity == 'month':
		sql = f"""
			SELECT TO_CHAR(DATE_TRUNC('month', s.created_at), 'YYYY-MM') AS mes,
				   SUM(s.total_amount) AS faturamento,
				   COUNT(*) AS vendas
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro}
			GROUP BY mes
			ORDER BY mes ASC
		"""
		result = run_query(sql, params)
		monthly = []
		for r in result:
			mes = r[0]
			fatur = float(r[1]) if r[1] is not None else 0.0
			vendas = int(r[2]) if r[2] is not None else 0
			avg_ticket = (fatur / vendas) if vendas else 0.0
			monthly.append({'mes': mes, 'faturamento': round(fatur, 2), 'vendas': vendas, 'avg_ticket': round(avg_ticket, 2)})

		# compute pct changes and combined growth (70% revenue / 30% sales)
		revenue_weight = 0.7
		sales_weight = 0.3
		crescimento = []
		for i in range(1, len(monthly)):
			prev = monthly[i-1]
			cur = monthly[i]
			try:
				rev_pct = (cur['faturamento'] - prev['faturamento']) / prev['faturamento'] * 100.0 if prev['faturamento'] else None
			except Exception:
				rev_pct = None
			try:
				sel_pct = (cur['vendas'] - prev['vendas']) / prev['vendas'] * 100.0 if prev['vendas'] else None
			except Exception:
				sel_pct = None

			if rev_pct is None and sel_pct is None:
				combined = None
			else:
				rev_val = rev_pct if rev_pct is not None else 0.0
				sel_val = sel_pct if sel_pct is not None else 0.0
				combined = revenue_weight * rev_val + sales_weight * sel_val

			crescimento.append({
				'mes': cur['mes'],
				'crescimento_revenue_pct': round(rev_pct,2) if rev_pct is not None else None,
				'crescimento_sales_pct': round(sel_pct,2) if sel_pct is not None else None,
				'crescimento_combined_pct': round(combined,2) if combined is not None else None,
				'current': cur,
				'previous': prev
			})

		return {'monthly': monthly, 'crescimento_loja': crescimento, 'weights': {'revenue': revenue_weight, 'sales': sales_weight}}

	# default behaviour: comparativo por loja (legacy)
	sql = f"""
		SELECT st.name, SUM(s.total_amount) AS faturamento, AVG(s.total_amount) AS ticket_medio, COUNT(*) AS vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY st.name
		ORDER BY faturamento DESC
	"""
	result = run_query(sql, params)
	return {'comparativo_loja': [ {'loja': r[0], 'faturamento': float(r[1]), 'ticket_medio': float(r[2]), 'vendas': int(r[3])} for r in result ]}

# Card 19: Anomalias Temporais
def get_anomalias_temporais(loja, canal, data_inicio, data_fim):
	# Now detect anomalies per store so we can show which loja had a spike/drop
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# Gather vendas per dia per loja
	sql = f"""
		SELECT DATE(s.created_at) AS dia, st.name AS loja, COUNT(*) AS vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY dia, st.name
		ORDER BY dia ASC, st.name ASC
	"""
	rows = run_query(sql, params)
	# Organize by loja to compute per-store mean
	from collections import defaultdict
	store_series = defaultdict(list)
	for r in rows:
		# r: (dia, loja, vendas)
		try:
			dia = r[0]
			loja_nome = r[1]
			vendas = int(r[2]) if r[2] is not None else 0
			store_series[loja_nome].append({'dia': dia, 'vendas': vendas})
		except Exception:
			continue

	alertas = []
	# For each store, compute mean and flag anomalies
	for loja_nome, series in store_series.items():
		vals = [s['vendas'] for s in series]
		if not vals:
			continue
		mean = sum(vals) / len(vals)
		for s in series:
			v = s['vendas']
			if mean and v > mean * 1.5:
				alertas.append({'dia': str(s['dia']), 'tipo': 'pico', 'vendas': v, 'loja': loja_nome})
			elif mean and v < mean * 0.5:
				alertas.append({'dia': str(s['dia']), 'tipo': 'queda', 'vendas': v, 'loja': loja_nome})

	# Sort alerts by date desc so the most recent anomalies appear first
	alertas = sorted(alertas, key=lambda x: x['dia'], reverse=True)
	return {'alertas': alertas}

# Card 20: Previsão de Demanda
def get_previsao_demanda(loja, canal, data_inicio, data_fim):
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# Simples: média móvel dos últimos 7 dias
	sql = f"""
		SELECT DATE(s.created_at) AS dia, COUNT(*) AS vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY dia
		ORDER BY dia ASC
	"""
	result = run_query(sql, params)
	vendas = [ {'dia': str(r[0]), 'vendas': r[1]} for r in result ]
	# Previsão simples: média dos últimos 7 dias
	ultimos_7 = vendas[-7:] if len(vendas) >= 7 else vendas
	media = sum([v['vendas'] for v in ultimos_7])/len(ultimos_7) if ultimos_7 else 0
	return {'grafico_previsao': vendas, 'previsao_media_7d': round(media,2)}

# Funções agregadas/insights para os novos endpoints

def get_produto_sazonal(loja, canal, data_inicio, data_fim):
	# Exemplo: produtos que só vendem em certos meses
	loja = (loja or '').strip()
	if not loja:
		return {'labels': [], 'valores': [], 'top_products': [], 'sazonalidade': [], 'analysis': {'message': 'É preciso informar a loja para visualizar a sazonalidade.'}, 'feriados': [], 'info': 'É preciso informar a loja para visualizar a sazonalidade.'}

	# use the standard sales filter (completed sales within date range and optional loja/canal)
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)

	# 1) Monthly totals (labels/valores) across all products for the period
	sql_months = f"""
		SELECT TO_CHAR(DATE_TRUNC('month', s.created_at), 'YYYY-MM') AS mes, SUM(ps.quantity) AS quantidade
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN product_sales ps ON ps.sale_id = s.id
		JOIN products p ON p.id = ps.product_id
		{filtro}
		GROUP BY mes
		ORDER BY mes
	"""
	res_months = run_query(sql_months, params)
	labels = [r[0] for r in res_months]
	valores = [int(r[1]) if r[1] is not None else 0 for r in res_months]

	# 2) Top products in the period (quantity + revenue)
	sql_top = f"""
		SELECT p.name, SUM(ps.quantity) AS quantidade, SUM(ps.quantity * ps.base_price) AS receita
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN product_sales ps ON ps.sale_id = s.id
		JOIN products p ON p.id = ps.product_id
		{filtro}
		GROUP BY p.name
		ORDER BY quantidade DESC
		LIMIT 5
	"""
	res_top = run_query(sql_top, params)
	top_products = [ {'produto': r[0], 'quantidade': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in res_top ]

	# 3) Detailed sazonalidade per product-month (keeps previous behavior but limited)
	sql_sazonal = f"""
		SELECT p.name, EXTRACT(MONTH FROM s.created_at) AS mes, SUM(ps.quantity) AS quantidade
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		JOIN product_sales ps ON ps.sale_id = s.id
		JOIN products p ON p.id = ps.product_id
		{filtro}
		GROUP BY p.name, mes
		ORDER BY p.name, mes
	"""
	res_sazonal = run_query(sql_sazonal, params)
	sazonalidade = [ {'produto': r[0], 'mes': int(r[1]) if r[1] is not None else None, 'quantidade': int(r[2]) if r[2] is not None else 0} for r in res_sazonal ]

	# 4) Analysis of the monthly trend (reuse analyze_chart_data)
	analysis = {}
	try:
		if labels and valores:
			analysis = analyze_chart_data(labels, valores)
		else:
			analysis = {'message': 'Dados insuficientes para análise (necessário ao menos 1 mês com dados).'}
	except Exception:
		analysis = {'message': 'Erro ao analisar dados de sazonalidade.'}

	# 5) Holiday keyword matching: determine which common holidays fall inside the
	# selected date range (approx by month) and search for products sold in that
	# store+period whose names match holiday-specific keywords.
	try:
		# build month set for the date range
		di = datetime.strptime(data_inicio, '%Y-%m-%d').date()
		df = datetime.strptime(data_fim, '%Y-%m-%d').date()
		months = set()
		y, m = di.year, di.month
		while (y < df.year) or (y == df.year and m <= df.month):
			months.add(m)
			m += 1
			if m > 12:
				m = 1
				y += 1

		# Map months to holidays (approximation) and define keyword lists
		month_holiday_map = {
			12: ['Natal'],
			4: ['Pascoa'],
			5: ['Dia das Mães'],
			6: ['Dia dos Namorados'],
			10: ['Halloween'],
			2: ['Carnaval'],
			3: ['Carnaval'],
			11: ['Black Friday']
		}
		holiday_keywords = {
			'Natal': ['panetone', 'panettone', 'ceia', 'peru', 'panetones', 'panetão', 'panetón', 'panetone'],
			'Pascoa': ['ovo de pascoa', 'ovo de páscoa', 'ovos de pascoa', 'ovos de páscoa', 'chocolate', 'colomba'],
			'Dia das Mães': ['dia das maes', 'dia das mães', 'mae', 'mãe', 'presente mae', 'presente mãe', 'kit mae'],
			'Dia dos Namorados': ['dia dos namorados', 'namorados', 'combo casal', 'jantar romantico', 'romantico'],
			'Halloween': ['halloween', 'abobora', 'fantasia', 'doces'],
			'Carnaval': ['carnaval', 'fantasia', 'confete', 'serpentina'],
			'Black Friday': ['black friday', 'blackfriday', 'oferta black', 'desconto']
		}

		holidays_in_range = set()
		for mon in months:
			if mon in month_holiday_map:
				holidays_in_range.update(month_holiday_map[mon])

		feriados = []
		for hol in sorted(list(holidays_in_range)):
			kws = holiday_keywords.get(hol, [])
			if not kws:
				continue
			# build query to count distinct products matching any keyword within the period and store
			ilike_clauses = ' OR '.join(["p.name ILIKE %s" for _ in kws])
			sql_count = f"""
				SELECT COUNT(DISTINCT p.id) FROM product_sales ps
				JOIN products p ON p.id = ps.product_id
				JOIN sales s ON s.id = ps.sale_id
				JOIN stores st ON st.id = s.store_id
				JOIN channels ch ON ch.id = s.channel_id
				{filtro} AND ({ilike_clauses})
			"""
			kws_params = [f"%{kw}%" for kw in kws]
			try:
				cnt_res = run_query_one(sql_count, params + kws_params)
				product_count = int(cnt_res[0]) if cnt_res and cnt_res[0] is not None else 0
			except Exception:
				product_count = 0

			# top products for this holiday (limit 5)
			sql_top_h = f"""
				SELECT p.name, SUM(ps.quantity) AS quantidade, SUM(ps.quantity * ps.base_price) AS receita
				FROM product_sales ps
				JOIN products p ON p.id = ps.product_id
				JOIN sales s ON s.id = ps.sale_id
				JOIN stores st ON st.id = s.store_id
				JOIN channels ch ON ch.id = s.channel_id
				{filtro} AND ({ilike_clauses})
				GROUP BY p.name
				ORDER BY quantidade DESC
				LIMIT 5
			"""
			try:
				res_h = run_query(sql_top_h, params + kws_params)
				top_h = [ {'produto': r[0], 'quantidade': int(r[1]) if r[1] is not None else 0, 'receita': float(r[2]) if r[2] is not None else 0.0} for r in res_h ]
			except Exception:
				top_h = []

			feriados.append({'holiday': hol, 'keywords': kws, 'product_count': product_count, 'top_products': top_h})
	except Exception:
		feriados = []

	# Ensure predictable shapes and types for the frontend
	# Round receita in top_products to 2 decimals
	for tp in top_products:
		try:
			tp['receita'] = round(float(tp.get('receita', 0.0)), 2)
			tp['quantidade'] = int(tp.get('quantidade', 0))
		except Exception:
			tp['receita'] = 0.0
			tp['quantidade'] = 0

	# Add user-friendly message when there are fewer than 2 months
	if not labels or len(labels) < 2:
		analysis['message'] = analysis.get('message') or 'É preciso pelo menos 2 meses de dados para detectar sazonalidade confiável.'

	# New: compute products that sell more specifically during holiday months
	# Build a consolidated list of holiday month numbers (integers)
	try:
		# `months` was built earlier as the set of month numbers in the range
		# and `month_holiday_map` maps month -> holiday names. Use that map
		# to select the month numbers which are considered holiday months.
		holiday_months = sorted([m for m in months if m in month_holiday_map]) if 'months' in locals() and 'month_holiday_map' in locals() else []
	except Exception:
		holiday_months = []

	holiday_top_products = []
	if holiday_months:
		# Build placeholders for IN (...) clause
		placeholders = ','.join(['%s'] * len(holiday_months))
		# Query totals for products during holiday months within the selected date range
		h_sql = f"""
			SELECT p.name, SUM(ps.quantity) AS quantidade_holiday, SUM(ps.quantity * ps.base_price) AS receita_holiday
			FROM product_sales ps
			JOIN products p ON p.id = ps.product_id
			JOIN sales s ON s.id = ps.sale_id
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro} AND EXTRACT(MONTH FROM s.created_at) IN ({placeholders})
			GROUP BY p.name
			ORDER BY quantidade_holiday DESC
			LIMIT 100
		"""
		try:
			h_results = run_query(h_sql, params + holiday_months)
		except Exception:
			h_results = []

		# Get baseline (non-holiday months) totals for the same products in the period
		# Build a map of product -> holiday_qty and then fetch baseline per product
		prod_names = [r[0] for r in h_results if r and r[0]]
		if prod_names:
			# placeholders for product names
			prod_placeholders = ','.join(['%s'] * len(prod_names))
			b_sql = f"""
				SELECT p.name, SUM(ps.quantity) AS quantidade_baseline, SUM(ps.quantity * ps.base_price) AS receita_baseline
				FROM product_sales ps
				JOIN products p ON p.id = ps.product_id
				JOIN sales s ON s.id = ps.sale_id
				JOIN stores st ON st.id = s.store_id
				JOIN channels ch ON ch.id = s.channel_id
				{filtro} AND (EXTRACT(MONTH FROM s.created_at) NOT IN ({placeholders})) AND p.name IN ({prod_placeholders})
				GROUP BY p.name
			"""
			try:
				b_results = run_query(b_sql, params + holiday_months + prod_names)
			except Exception:
				b_results = []

			# Map baseline by product
			baseline_map = { r[0]: {'quantidade_baseline': int(r[1]) if r[1] is not None else 0, 'receita_baseline': float(r[2]) if r[2] is not None else 0.0} for r in b_results }

			# Build consolidated list with lift percentage
			for r in h_results:
				if not r or not r[0]:
					continue
				nome = r[0]
				q_h = int(r[1]) if r[1] is not None else 0
				rec_h = float(r[2]) if r[2] is not None else 0.0
				base = baseline_map.get(nome, {})
				q_b = int(base.get('quantidade_baseline', 0)) if base else 0
				rec_b = float(base.get('receita_baseline', 0.0)) if base else 0.0
				if q_b:
					try:
						lift = (q_h - q_b) / q_b * 100.0
					except Exception:
						lift = None
				else:
					lift = None
				holiday_top_products.append({
					'produto': nome,
					'quantidade_holiday': q_h,
					'receita_holiday': round(rec_h,2),
					'quantidade_baseline': q_b,
					'receita_baseline': round(rec_b,2),
					'lift_pct': round(lift,2) if (lift is not None) else None
				})

			# sort by lift_pct desc (None last) then by quantidade_holiday desc
			holiday_top_products = sorted(holiday_top_products, key=lambda x: ((-999999 if x['lift_pct'] is None else -x['lift_pct']), -x['quantidade_holiday']))


	# Final payload
	return {
		'labels': labels,
		'valores': valores,
		'top_products': top_products,
		'sazonalidade': sazonalidade,
		'analysis': analysis,
		'feriados': feriados,
		'holiday_top_products': holiday_top_products,
		'info': None
	}
    
	# Note: legacy return above; below we could extend with holiday-aware matches.

def get_ranking_global(loja, canal, data_inicio, data_fim):
	# Ranking de lojas por faturamento
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT st.name, SUM(s.total_amount) AS faturamento
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY st.name
		ORDER BY faturamento DESC
		LIMIT 10
	"""
	result = run_query(sql, params)
	return {'ranking_global': [ {'loja': r[0], 'faturamento': float(r[1])} for r in result ]}

def get_crescimento_loja(loja, canal, data_inicio, data_fim):
	# Crescimento percentual mês a mês
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# We'll compute monthly faturamento and vendas, then derive pct changes for both.
	# Final growth score = weighted combination: revenue_weight*revenue_pct + sales_weight*sales_pct
	revenue_weight = 0.7
	sales_weight = 0.3

	sql = f"""
		SELECT TO_CHAR(DATE_TRUNC('month', s.created_at), 'YYYY-MM') AS mes,
			SUM(s.total_amount) AS faturamento,
			COUNT(*) AS vendas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		{filtro}
		GROUP BY mes
		ORDER BY mes ASC
	"""

	result = run_query(sql, params)
	# normalize results
	monthly = []
	for r in result:
		mes = r[0]
		fatur = float(r[1]) if r[1] is not None else 0.0
		vendas = int(r[2]) if r[2] is not None else 0
		avg_ticket = (fatur / vendas) if vendas else 0.0
		monthly.append({'mes': mes, 'faturamento': round(fatur,2), 'vendas': vendas, 'avg_ticket': round(avg_ticket,2)})

	# compute percent changes and combined growth
	crescimento = []
	for i in range(1, len(monthly)):
		prev = monthly[i-1]
		cur = monthly[i]
		# revenue pct
		try:
			if prev['faturamento']:
				rev_pct = (cur['faturamento'] - prev['faturamento']) / prev['faturamento'] * 100.0
			else:
				rev_pct = None
		except Exception:
			rev_pct = None
		# sales pct
		try:
			if prev['vendas']:
				sel_pct = (cur['vendas'] - prev['vendas']) / prev['vendas'] * 100.0
			else:
				sel_pct = None
		except Exception:
			sel_pct = None

		# Combined: if both are None, combined=None; otherwise compute weighted sum (replace None with 0 for computation)
		if rev_pct is None and sel_pct is None:
			combined = None
		else:
			rev_val = rev_pct if rev_pct is not None else 0.0
			sel_val = sel_pct if sel_pct is not None else 0.0
			combined = revenue_weight * rev_val + sales_weight * sel_val

		crescimento.append({
			'mes': cur['mes'],
			'crescimento_revenue_pct': round(rev_pct,2) if rev_pct is not None else None,
			'crescimento_sales_pct': round(sel_pct,2) if sel_pct is not None else None,
			'crescimento_combined_pct': round(combined,2) if combined is not None else None,
			'current': cur,
			'previous': prev
		})

	return {'crescimento_loja': crescimento, 'monthly': monthly, 'weights': {'revenue': revenue_weight, 'sales': sales_weight}}

def get_mix_produtos_global(loja, canal, data_inicio, data_fim):
	"""
	Return top product combos globally (pairs/triads).

	This function ignores the incoming loja/canal/date filters and computes
	a global aggregation of product combos sold together in completed sales.
	We limit to combos with 2 or 3 distinct products (pairs and triads) which
	are often the most actionable.
	"""

	min_size = 2
	max_size = 3
	limit = 20

	sql = """
		WITH combos_per_sale AS (
			SELECT s.id AS sale_id,
			       STRING_AGG(DISTINCT p.name, '||' ORDER BY p.name) AS combo_key,
			       COUNT(DISTINCT p.id) AS produto_count
			FROM sales s
			JOIN product_sales ps ON ps.sale_id = s.id
			JOIN products p ON p.id = ps.product_id
			WHERE s.sale_status_desc = 'COMPLETED'
			GROUP BY s.id
		)
		SELECT combo_key, produto_count, COUNT(*) AS vezes
		FROM combos_per_sale
		WHERE produto_count BETWEEN %s AND %s
		GROUP BY combo_key, produto_count
		ORDER BY vezes DESC
		LIMIT %s
	"""

	result = run_query(sql, [min_size, max_size, limit])
	combos = []
	for r in result:
		combo_key = r[0] or ''
		produto_count = int(r[1]) if r[1] is not None else 0
		vezes = int(r[2]) if r[2] is not None else 0
		produtos = [p.strip() for p in combo_key.split('||') if p and p.strip()]
		if produto_count >= min_size and produtos:
			combos.append({'produtos': produtos, 'quantidade': vezes})

	return {'mix_produtos_global': combos}

def get_anomalias_operacionais(loja, canal, data_inicio, data_fim):
	# Exemplo: vendas canceladas, atrasos, etc
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	sql = f"""
		SELECT DATE(s.created_at) AS dia, COUNT(*) AS canceladas
		FROM sales s
		JOIN stores st ON st.id = s.store_id
		JOIN channels ch ON ch.id = s.channel_id
		WHERE s.sale_status_desc = 'CANCELLED' AND DATE(s.created_at) BETWEEN %s AND %s
		GROUP BY dia
		ORDER BY dia ASC
	"""
	result = run_query(sql, [data_inicio, data_fim])
	return {'anomalias_operacionais': [ {'dia': str(r[0]), 'canceladas': int(r[1])} for r in result ]}


def analyze_chart_data(labels, values):
	"""Analyze arrays of labels and numeric values and return summary analysis.

	Returns dict with: mean, max (label,value), min (label,value), diff_abs, diff_pct, message
	"""
	try:
		if not labels or not values or len(labels) != len(values):
			return {'error': 'labels and values must be arrays of same length'}
		nums = []
		for v in values:
			try:
				nums.append(float(v))
			except Exception:
				nums.append(0.0)
		n = len(nums)
		total = sum(nums)
		mean = total / n if n else 0.0
		max_idx = max(range(n), key=lambda i: nums[i])
		min_idx = min(range(n), key=lambda i: nums[i])
		max_val = nums[max_idx]
		min_val = nums[min_idx]
		max_label = labels[max_idx]
		min_label = labels[min_idx]
		diff_abs = max_val - min_val
		diff_pct = (diff_abs / min_val * 100.0) if min_val else None

		# Build human-friendly messages (Portuguese)
		parts = []
		parts.append(f"Média dos itens: {round(mean,2)}")
		parts.append(f"Maior: {max_label} ({round(max_val,2)})")
		parts.append(f"Menor: {min_label} ({round(min_val,2)})")
		if diff_pct is None:
			parts.append(f"Diferença absoluta: {round(diff_abs,2)} (não é possível calcular % porque o menor é zero)")
		else:
			parts.append(f"Diferença: {round(diff_abs,2)} ({round(diff_pct,2)}%) entre maior e menor")

		# pico relativo ao resto
		above_mean = sum(1 for x in nums if x > mean)
		below_mean = n - above_mean
		parts.append(f"Itens acima da média: {above_mean}; itens abaixo da média: {below_mean}.")

		message = ' / '.join(parts)

		return {
			'mean': round(mean,2),
			'max': {'label': max_label, 'value': round(max_val,2)},
			'min': {'label': min_label, 'value': round(min_val,2)},
			'diff_abs': round(diff_abs,2),
			'diff_pct': round(diff_pct,2) if diff_pct is not None else None,
			'above_mean': above_mean,
			'below_mean': below_mean,
			'message': message
		}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('analyze_chart_data error: %s', e)
		return {'error': 'Internal error during chart analysis'}

# Monetary impact helpers
def compute_monetary_impact_descontos(loja, canal, data_inicio, data_fim):
	"""Compute monetary impact of discounts in the selected period:
	returns total_discount (BRL), avg_discount_per_sale, pct_of_revenue."""
	try:
		filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
		sql = f"""
			SELECT COALESCE(SUM(s.total_discount),0) AS total_discount,
				   COALESCE(AVG(NULLIF(s.total_discount,0)),0) AS avg_discount_per_sale,
				   COALESCE(SUM(s.total_amount),0) AS total_revenue
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro}
		"""
		res = run_query_one(sql, params)
		total_discount = float(res[0]) if res and res[0] is not None else 0.0
		avg_discount = float(res[1]) if res and res[1] is not None else 0.0
		total_revenue = float(res[2]) if res and res[2] is not None else 0.0
		pct_of_revenue = (total_discount / total_revenue * 100.0) if total_revenue else 0.0
		return {'total_discount': round(total_discount,2), 'avg_discount_per_sale': round(avg_discount,2), 'pct_of_revenue': round(pct_of_revenue,2)}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('compute_monetary_impact_descontos error: %s', e)
		return {'total_discount': 0.0, 'avg_discount_per_sale': 0.0, 'pct_of_revenue': 0.0}

def compute_monetary_impact_cancelamentos(loja, canal, data_inicio, data_fim):
	"""Compute monetary impact of cancelled sales: total_lost_revenue (BRL), n_cancelled, pct_of_revenue."""
	try:
		# total revenue in period and total amount of cancelled sales
		# Build base filter to compute total revenue
		base_filtro, base_params = filter_sales(loja, canal, data_inicio, data_fim)
		# total revenue for period
		sql_tot = f"SELECT COALESCE(SUM(s.total_amount),0) FROM sales s JOIN stores st ON st.id = s.store_id JOIN channels ch ON ch.id = s.channel_id {base_filtro}"
		res_tot = run_query_one(sql_tot, base_params)
		total_revenue = float(res_tot[0]) if res_tot and res_tot[0] is not None else 0.0

		# cancelled sales: sum and count
		sql_cancel = f"SELECT COALESCE(SUM(s.total_amount),0), COUNT(*) FROM sales s JOIN stores st ON st.id = s.store_id JOIN channels ch ON ch.id = s.channel_id WHERE s.sale_status_desc = 'CANCELLED' AND DATE(s.created_at) BETWEEN %s AND %s"
		# For cancelled we need to pass date range; include loja/canal if present
		params = [data_inicio, data_fim]
		if loja:
			sql_cancel = sql_cancel.replace("WHERE", "WHERE st.name = %s AND", 1)
			params = [loja] + params
		if canal:
			sql_cancel = sql_cancel.replace("WHERE", "WHERE ch.name = %s AND", 1)
			params = [canal] + params
		res_cancel = run_query_one(sql_cancel, params)
		total_lost = float(res_cancel[0]) if res_cancel and res_cancel[0] is not None else 0.0
		n_cancel = int(res_cancel[1]) if res_cancel and res_cancel[1] is not None else 0
		pct_of_revenue = (total_lost / total_revenue * 100.0) if total_revenue else 0.0
		return {'total_lost_revenue': round(total_lost,2), 'n_cancelled': n_cancel, 'pct_of_revenue': round(pct_of_revenue,2), 'total_revenue': round(total_revenue,2)}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('compute_monetary_impact_cancelamentos error: %s', e)
		return {'total_lost_revenue': 0.0, 'n_cancelled': 0, 'pct_of_revenue': 0.0, 'total_revenue': 0.0}


# -------------------------
# Dynamic analysis helpers
# -------------------------
def _compute_previous_period(data_inicio, data_fim):
	"""Return previous period start/end strings (YYYY-MM-DD) matching the same length immediately before data_inicio."""
	try:
		di = datetime.strptime(data_inicio, '%Y-%m-%d').date()
		df = datetime.strptime(data_fim, '%Y-%m-%d').date()
	except Exception:
		return None, None
	length = (df - di).days + 1
	prev_end = di - timedelta(days=1)
	prev_start = prev_end - timedelta(days=length-1)
	return prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d')


def get_total_clientes_frequentes(loja, canal, data_inicio, data_fim):
	"""Return the count of customers with 2 or more purchases in the period.

	This is a lightweight metric used by the dynamic analyzer (not the top list).
	"""
	filtro, params = filter_sales(loja, canal, data_inicio, data_fim)
	# Count customers with at least 2 purchases in the period
	sql = f"""
		SELECT COUNT(*) FROM (
			SELECT s.customer_id, COUNT(*) as compras
			FROM sales s
			JOIN stores st ON st.id = s.store_id
			JOIN channels ch ON ch.id = s.channel_id
			{filtro}
			GROUP BY s.customer_id
			HAVING COUNT(*) >= 2
		) sub
	"""
	res = run_query_one(sql, params)
	return int(res[0]) if res and res[0] is not None else 0


def analyze_card(card_id, loja, canal, data_inicio, data_fim):
	"""Generic analyzer that computes current vs previous period and returns an analysis dict.

	Supported card_ids: 'card-faturamento-total', 'card-ticket-medio',
	'card-clientes-frequentes', 'card-taxa-cancelamento'.

	Returns: { 'metric_name': str, 'current': number, 'previous': number, 'pct_change': float, 'message': str }
	"""
	prev_start, prev_end = _compute_previous_period(data_inicio, data_fim)
	if not prev_start:
		return {'error': 'Invalid date range'}

	try:
		if card_id == 'card-faturamento-total':
			cur = get_faturamento_total(loja, canal, data_inicio, data_fim).get('valor_total', 0.0)
			prev = get_faturamento_total(loja, canal, prev_start, prev_end).get('valor_total', 0.0)
			name = 'Faturamento (R$)'

		elif card_id == 'card-ticket-medio':
			cur = get_ticket_medio(loja, canal, data_inicio, data_fim).get('ticket_medio', 0.0)
			prev = get_ticket_medio(loja, canal, prev_start, prev_end).get('ticket_medio', 0.0)
			name = 'Ticket Médio (R$)'

		elif card_id == 'card-clientes-frequentes':
			cur = get_total_clientes_frequentes(loja, canal, data_inicio, data_fim)
			prev = get_total_clientes_frequentes(loja, canal, prev_start, prev_end)
			name = 'Clientes Frequentes (count)'

		elif card_id == 'card-taxa-cancelamento':
			cur = get_taxa_cancelamento(loja, canal, data_inicio, data_fim).get('taxa_cancelamento', 0.0)
			prev = get_taxa_cancelamento(loja, canal, prev_start, prev_end).get('taxa_cancelamento', 0.0)
			name = 'Taxa de Cancelamento (%)'

		else:
			# Fallback: try to call get_performance_por_canal and sum numeric metrics if present
			data_cur = None
			try:
				# try generic cards
				from importlib import import_module
				# best-effort: call function with a mapping
				func_map = {
					'card-performance-por-canal': get_performance_por_canal,
					'card-performance-por-loja': get_performance_por_loja,
				}
				if card_id in func_map:
					data_cur = func_map[card_id](loja, canal, data_inicio, data_fim)
					data_prev = func_map[card_id](loja, canal, prev_start, prev_end)
					# try to sum first numeric field across rows
					key = next(iter(data_cur.keys()), None)
					if key and isinstance(data_cur.get(key), list):
						cur = sum([sum([v for v in row.values() if isinstance(v, (int, float))]) for row in data_cur.get(key)])
						prev = sum([sum([v for v in row.values() if isinstance(v, (int, float))]) for row in data_prev.get(key)])
						name = f'Aggregated metric {key}'
					else:
						return {'error': 'Unsupported card for generic analysis'}
				else:
					return {'error': 'Unsupported card for analysis'}
			except Exception:
				return {'error': 'Unsupported card for analysis'}

		# compute pct change safely
		try:
			if prev:
				pct = (cur - prev) / prev * 100.0
			else:
				pct = None
		except Exception:
			pct = None

		# human-friendly message
		if pct is None:
			if cur == prev:
				message = f'{name}: sem alteração detectada (valor atual: {cur}).'
			else:
				message = f'{name}: valor atual {cur} (sem comparação disponível para período anterior).'
		else:
			sign = 'aumentou' if pct > 0 else 'diminuiu' if pct < 0 else 'permaneceu estável'
			message = f'{name} {sign} {abs(round(pct,2))}% em relação ao período anterior ({prev_start} — {prev_end}).'

		return {
			'metric_name': name,
			'current': cur,
			'previous': prev,
			'pct_change': round(pct,2) if (pct is not None) else None,
			'message': message,
			'prev_period': {'start': prev_start, 'end': prev_end}
		}
	except Exception as e:
		logging.getLogger('dashboard_Maria').exception('analyze_card error: %s', e)
		return {'error': 'Internal error while analyzing card'}
