from __future__ import annotations


class _NoOpSeverityLevel:
    BLOCKER = "blocker"
    CRITICAL = "critical"
    NORMAL = "normal"
    MINOR = "minor"
    TRIVIAL = "trivial"


class _NoOpDynamic:
    def __getattr__(self, _name):
        def _noop(*_args, **_kwargs):
            return None

        return _noop


class _NoOpAllure:
    severity_level = _NoOpSeverityLevel
    dynamic = _NoOpDynamic()

    def __getattr__(self, _name):
        def _decorator(*_args, **_kwargs):
            if _args and callable(_args[0]) and len(_args) == 1 and not _kwargs:
                return _args[0]

            def _wrap(func):
                return func

            return _wrap

        return _decorator


try:
    import allure as allure
except ImportError:
    allure = _NoOpAllure()

