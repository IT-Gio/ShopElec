from django import template

register = template.Library()  # only define once

@register.filter
def floatdiv(value, divisor):
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def stars10to5(avg_rating):
    """
    Converts a 10-point rating to a list of 5 stars: 'full', 'half', 'empty'.
    """
    try:
        avg_rating = float(avg_rating)
    except (ValueError, TypeError):
        return ["empty"] * 5

    stars = []
    five_scale = avg_rating / 2
    for i in range(1, 6):
        if five_scale >= i:
            stars.append("full")
        elif five_scale >= i - 0.5:
            stars.append("half")
        else:
            stars.append("empty")
    return stars
