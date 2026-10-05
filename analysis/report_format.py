"""APA-style formatting of numbers for the results report (LaTeX).

APA rules used here: p-values with three decimals and no leading zero, "< .001" for very small values; values that
cannot exceed 1 (correlations, reliabilities) without a leading zero; other values with a leading zero; minus signs
typeset as real minus signs.
"""
import math


def tex(text):
    """Typeset hyphen-minus signs as real minus signs in LaTeX."""
    return text.replace("-", "$-$")


def number(value, digits=2):
    """A value that can exceed 1 in size (t, dz, means): leading zero kept."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "--"
    return tex(f"{value:.{digits}f}")


def bounded(value, digits=2):
    """A value between -1 and 1 (r, rho, reliability): no leading zero. Plain hyphen; use tex() for LaTeX."""
    text = f"{value:.{digits}f}"
    return text.replace("0.", ".", 1)


def p(value):
    """APA p-value with its relation sign: '< .001' or '= .049'."""
    if value < 0.001:
        return "< .001"
    return "= " + (f"{value:.3f}" if value >= 1 else bounded(value, 3))


def ci(low, high, between_minus_one_and_one=False, digits=2):
    """95% CI in square brackets."""
    if between_minus_one_and_one:
        return f"[{tex(bounded(low, digits))}, {tex(bounded(high, digits))}]"
    return f"[{number(low, digits)}, {number(high, digits)}]"
