"""Database migration extension shared by the application factory and CLI."""

from flask_migrate import Migrate


migrate = Migrate(compare_type=True)
