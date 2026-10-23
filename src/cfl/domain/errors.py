"""Errores del dominio."""


class DomainError(Exception):
    """Base de los errores de negocio."""


class InvalidTransactionIdError(DomainError, ValueError):
    """El identificador no cumple el formato RMX-AAAA-NNNNNN."""


class DataSourceError(DomainError):
    """El origen de datos no se pudo leer o está corrupto."""
