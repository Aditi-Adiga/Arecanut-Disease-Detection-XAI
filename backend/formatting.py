def percentage_label(probability):
    """Display a softmax score without rounding it to apparent certainty."""
    value = float(probability)
    if value > 0.999:
        return ">99.9"
    if 0 < value < 0.001:
        return "<0.1"
    return f"{value * 100:.1f}"
