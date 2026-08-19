class ApprovalDenied(ValueError):
    pass


def validate_approval(channel: str, confirmation: str) -> None:
    """Fail closed. A spoken command may request but can never grant approval."""
    if channel == "voice":
        raise ApprovalDenied("Voice approval is disabled; use the explicit visual approval control.")
    if channel != "ui":
        raise ApprovalDenied("Approval is accepted only through the visual approval boundary.")
    if confirmation != "APPROVE SYNTHETIC RESEARCH MISSION":
        raise ApprovalDenied("Exact approval confirmation is required.")

