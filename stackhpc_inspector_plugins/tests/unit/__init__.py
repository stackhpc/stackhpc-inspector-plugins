# NOTE(TheJulia): This is to force oslo_service from trying to use eventlet.
from oslo_service import backend
backend.init_backend(backend.BackendType.THREADING)
