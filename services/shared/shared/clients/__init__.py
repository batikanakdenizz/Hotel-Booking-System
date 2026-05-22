"""Async client wrappers for the four external datastores.

Each datastore lives in its own submodule:

- ``shared.clients.postgres`` (requires the [postgres] extra)
- ``shared.clients.mongo``    (requires the [mongo] extra)
- ``shared.clients.redis``    (requires the [redis] extra)
- ``shared.clients.rabbitmq`` (requires the [rabbitmq] extra)

We deliberately do NOT re-export from any submodule at the package level so
that ``from shared.clients.mongo import X`` does not transitively force
SQLAlchemy (or any other unrelated dependency) into the importing service.
"""
