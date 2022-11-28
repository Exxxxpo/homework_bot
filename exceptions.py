class StatusCodeError(Exception):
    """Исключение, для случаев, когда статус код сервера отличен от 200"""
    def __init__(self, *args, **kwargs):
        pass
