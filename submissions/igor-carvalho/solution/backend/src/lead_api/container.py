"""Composição das dependências (injeção manual). Tudo que muda entre produção e teste entra aqui."""
from __future__ import annotations

from dataclasses import dataclass

from .limiter import RateLimiter
from .services.deals import DealQueryService
from .services.feedback import FeedbackService
from .services.auth import AuthService
from .services.jobs import JobRunner, JobService
from .services.summary import SummaryService
from .services.whatif import WhatIfService
from .settings import Settings
from .store import ScoreStore


@dataclass
class Container:
    settings: Settings
    store: ScoreStore
    deals: DealQueryService
    whatif: WhatIfService
    summary: SummaryService
    feedback: FeedbackService
    jobs: JobService
    auth: AuthService
    runner: JobRunner
    limiter: RateLimiter
