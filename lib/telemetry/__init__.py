from .transaction_middleware import TransactionMiddleware

# Shared middleware instance (single per Python process)
transaction_middleware = TransactionMiddleware()
