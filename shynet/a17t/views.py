"""The a17t blueprint.

It carries no routes; it exists so that the `a17t/` template partials are on the
template search path.
"""

from flask import Blueprint

a17t = Blueprint("a17t", __name__, template_folder="templates")
