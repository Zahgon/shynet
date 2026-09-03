class DashboardConfig:
    name = "dashboard"

    def ready(self):
        from shynet import settings

        if not settings.ACCOUNT_SIGNUPS_ENABLED:
            # Normally you'd do this in settings.py, but this must be done _after_ apps are enabled
            from accounts.adapter import DefaultAccountAdapter

            DefaultAccountAdapter.is_open_for_signup = lambda k, v: False
