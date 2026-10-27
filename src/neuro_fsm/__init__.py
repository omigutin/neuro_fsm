""" NeuroFSM — машина состояний с профилями для пайплайнов инференса нейросетей. """

from .configs import FsmConfig, ProfileConfig, StateConfig, HistoryWriterConfig
from .config_builder import FsmConfigBuilder, ProfileConfigBuilder
from .core import FsmManager, Fsm, State, ActiveProfileView
from .models import FsmResult, ProfileSwitcherStrategies, ProfileNames

__version__ = "0.2.0"

__all__ = [
    "FsmConfig",
    "ProfileConfig",
    "StateConfig",
    "HistoryWriterConfig",
    "FsmConfigBuilder",
    "ProfileConfigBuilder",
    "FsmManager",
    "Fsm",
    "State",
    "ActiveProfileView",
    "FsmResult",
    "ProfileSwitcherStrategies",
    "ProfileNames",
]
