__all__ = ['register_all_field_converters']

from ..state_profiles import StateProfileName
from ...models import StatesTupleTuple, StatesDict
# from ..state_profiles import StatesProfileConfig, StateProfileConfigTuple
from ...models import StateMeta, StateParams, StatesTuple, StatesDict
from .field_converter import FieldConverter
from ..state_profiles.states_profile import StatesProfile


def register_all_field_converters():
    FieldConverter.register(StateMeta, lambda d: StateMeta(**d))
    FieldConverter.register(StateParams, lambda d: StateParams(**d))
    FieldConverter.register(StatesProfile, lambda d: StatesProfile(**d))
    # FieldConverter.register(StateProfileName, lambda d: StateProfileName(**d))

    FieldConverter.register(
        StatesTuple,
        lambda value: FieldConverter.to_mapped_tuple(value, lambda d: FieldConverter.convert(d, StateMeta))
    )

    FieldConverter.register(
        StatesDict,
        lambda value: FieldConverter.to_mapped_dict(value, lambda d: FieldConverter.convert(d, int))
    )
    FieldConverter.register(
        StatesDict,
        lambda value: FieldConverter.to_mapped_dict(value, lambda d: FieldConverter.convert(d, int))
    )

    FieldConverter.register(
        StatesTupleTuple,
        lambda value: FieldConverter.to_mapped_tuple(value, lambda d: FieldConverter.convert(d, StatesTuple)
        )
    )

    # FieldConverter.register(
    #     StateProfileConfigTuple,
    #     lambda lst: tuple(FieldConverter.convert(item, StatesProfileConfig) for item in lst)
    # )