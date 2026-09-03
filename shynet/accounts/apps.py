class AccountsConfig:
    name = "accounts"

    def ready(self):
        from shynet import settings

        if not settings.ACCOUNT_SIGNUPS_ENABLED:
            from .adapter import DefaultAccountAdapter

            DefaultAccountAdapter.is_open_for_signup = lambda k, v: False
