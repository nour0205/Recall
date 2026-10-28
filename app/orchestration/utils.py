def build_study_hint(sources):
    """Point the student back to the notes the answer came from, in ranking order."""
    if not sources:
        return None
    document_ids = dict.fromkeys(s.document_id for s in sources)
    return f"Review the relevant material in: {', '.join(document_ids)}"
