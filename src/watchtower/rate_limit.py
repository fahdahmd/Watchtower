"""
Shared rate limiter, keyed by client IP. Applied per-route in the routers
(auth endpoints get the tightest limits — that's where brute-forcing and
account enumeration happen).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
