from django.db.utils import OperationalError
from django.http import JsonResponse
import logging


class DBResourceErrorMiddleware:
    """Middleware que captura erros de recurso do banco (OperationalError / DiskFull)
    e retorna um JSON 503 amigável ao frontend em vez da página HTML 500.

    Mantemos logs detalhados para depuração do time de infra.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('dashboard_Maria')

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        try:
            exc_text = str(exception) or ''
        except Exception:
            exc_text = ''

        # Heurística segura: capta OperationalError explicitamente ou mensagens
        # que contenham indicativos de shared memory / disk full geradas pelo PG
        if isinstance(exception, OperationalError) or 'no space left on device' in exc_text.lower() or 'shared memory' in exc_text.lower():
            # Log completo para os operadores
            try:
                self.logger.exception('Database resource error intercepted: %s', exception)
            except Exception:
                # Garantir que o middleware não quebre por falha de logging
                pass

            # Mensagem amigável para o frontend/usuário
            return JsonResponse({
                'error': 'Serviço temporariamente indisponível por problema de recursos do banco de dados. Tente novamente mais tarde.'
            }, status=503)

        # Não tratado: permita que outras exceções sigam para o handler default
        return None
