"""Mathematical type system definitions."""

from enum import Enum, auto


class MathType(Enum):
    """Mathematical domain types for strongly-typed expression nodes."""
    INTEGER = auto()
    RATIONAL = auto()
    REAL = auto()
    BOOLEAN = auto()
    SEQUENCE = auto()

    def is_subtype_of(self, other: "MathType") -> bool:
        """Check if self can be implicitly promoted or used where other is expected."""
        if self == other:
            return True
        if self == MathType.INTEGER and other in (MathType.RATIONAL, MathType.REAL):
            return True
        if self == MathType.RATIONAL and other == MathType.REAL:
            return True
        return False

