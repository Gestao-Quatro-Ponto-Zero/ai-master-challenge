"""Base declarativa. O DDL vem do arquivo schema_v1.sql; o ORM nunca cria nem altera tabelas."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
