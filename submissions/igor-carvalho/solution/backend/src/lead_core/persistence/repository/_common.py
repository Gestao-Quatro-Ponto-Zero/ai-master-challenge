"""Utilidades compartilhadas pelos repositórios."""


def as_dict(obj, exclude: tuple[str, ...] = ()) -> dict:
    """Linha ORM -> dict simples (os services nunca recebem objetos ORM)."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name not in exclude}
