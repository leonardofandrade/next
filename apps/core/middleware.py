"""
Middleware para rastreamento de auditoria.
Armazena o usuário atual em um contexto thread-local para uso pelo AuditedModel.
"""
import threading

# Contexto thread-local para armazenar o usuário atual
_thread_locals = threading.local()


def get_current_user():
    """
    Retorna o usuário atual armazenado no contexto thread-local.
    """
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """
    Define o usuário atual no contexto thread-local.
    """
    _thread_locals.user = user


class AuditMiddleware:
    """
    Middleware que captura o usuário atual da requisição e o armazena
    no contexto thread-local para uso pelo AuditedModel.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Armazena o usuário atual no contexto thread-local
        if request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
        
        try:
            response = self.get_response(request)
        finally:
            # Limpa o contexto após a requisição
            set_current_user(None)
        
        return response

