"""Project-specific exceptions for meaorganoid."""


class MEAValueError(ValueError):
    """Raised when MEA data values are invalid for the requested operation."""


class MEASchemaError(ValueError):
    """Raised when an input file does not match the expected MEA schema."""


class MEAQCError(ValueError):
    """Raised when QC computation cannot be completed."""
