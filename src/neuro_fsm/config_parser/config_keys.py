__all__ = ['ConfigKeys']


class ConfigKeys:
    """ Названия настроек, могут быть распарсены """

    STATES = "STATES"
    ENABLE = "ENABLE"
    PROFILE_NAME = "NAME"
    INIT_STATES = "INIT_STATES"
    DEFAULT_STATES = "DEFAULT_STATES"
    EXPECTED_SEQUENCES = "EXPECTED_SEQUENCES"
    STATE_PROFILES = "STATE_PROFILES"
    PROFILE_SWITCHER_STRATEGY = "PROFILE_SWITCHER_STRATEGY"

    ALL = {
        STATES,
        ENABLE,
        INIT_STATES,
        DEFAULT_STATES,
        EXPECTED_SEQUENCES,
        STATE_PROFILES,
        PROFILE_SWITCHER_STRATEGY,
    }

    @classmethod
    def __iter__(cls):
        return iter(cls.ALL)

    @classmethod
    def __contains__(cls, item):
        return item in cls.ALL

    @classmethod
    def __getitem__(cls, key: str) -> str:
        if key in cls.ALL:
            return key
        raise KeyError(f"Invalid config key: {key}")

    @classmethod
    def values(cls) -> set[str]:
        return cls.ALL.copy()

    @classmethod
    def as_list(cls) -> list[str]:
        return list(cls.ALL)
