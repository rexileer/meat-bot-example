import typing

from aiogram.contrib.middlewares.i18n import I18nMiddleware


class LocaleManager:
    __instance = None
    __init = False

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(LocaleManager, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        if not self.__init:
            self._i18n_gettext = None
            self.__init = True

    def set_middleware(self, middleware: I18nMiddleware):
        self._i18n_gettext = middleware.gettext

    def __call__(self, msg_id: str, locale="ru", set_locale: bool = False) -> typing.Union[str, "Locale"]:
        if set_locale:
            return Locale(msg_id, locale)

        return self._i18n_gettext(msg_id, locale=locale)


class Locale:
    def __init__(self, msg_id: str, locale="ru"):
        self.msg_id = msg_id
        self.locale = locale

    def set(self, locale=None):
        if locale is None:
            locale = self.locale

        locale_manager = LocaleManager()

        return locale_manager(self.msg_id, locale)
