"""The tool's failures and their exit codes (plan §4).  The API raises these; only the CLI exits."""


class Error(Exception):
    exit_code = 1


class NotFound(Error):
    """No tree at the expected place, or git missing or too old."""
    exit_code = 2


class Refused(Error):
    """A precondition does not hold: the chain does not link, the tree has a .git, a patch target is
    a symlink, a patch file cannot be read, a name is unknown ..."""
    exit_code = 3


class ChainBroken(Refused):
    """The feature directories do not link into one chain on this tree (decision 3)."""


class Busy(Error):
    """The lock on the tree was not obtained within the timeout."""


class WriteFailed(Error):
    """git could not finish writing a copy, or a file or work directory could not be read or written."""
