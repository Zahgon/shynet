"""
WSGI config for the shynet project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

from .app import create_app

application = create_app()
