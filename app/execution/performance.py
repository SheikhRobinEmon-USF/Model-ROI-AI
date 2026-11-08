"""Request-scoped reuse of model inventory and anonymous judge decisions."""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, field


@dataclass
class RunState:
    inventory: list | None = None
    verdicts: dict = field(default_factory=dict)
    notify: object = None

current = ContextVar("modelroi_run", default=None)


@contextmanager
def run_scope(notify=None):
    token = current.set(RunState(notify=notify))
    try:
        yield
    finally:
        current.reset(token)


def emit(event, **data):
    state = current.get()
    if state and state.notify:
        state.notify({"event": event, **data})


def rate_once(judge, task, answer):
    state = current.get()
    if state is None:
        return judge(task, answer)
    key = (task, answer)
    if key not in state.verdicts:
        state.verdicts[key] = judge(task, answer)
    return deepcopy(state.verdicts[key])
