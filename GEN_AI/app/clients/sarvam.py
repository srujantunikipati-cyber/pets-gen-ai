"""Deprecated Sarvam client retained for backwards compatibility."""


class SarvamClient:  # pragma: no cover - legacy stub
    """Legacy stub; use :mod:`app.clients.ai4bharat` instead."""

    def __init__(self, *_args, **_kwargs) -> None:
        raise RuntimeError(
            "SarvamClient is deprecated. Please switch to AI4BharatClient."
        )
