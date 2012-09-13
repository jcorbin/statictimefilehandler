A principled rotating file log handler for Python's logging module:
- no log files will be moved or unlinked
- that means that roll-off isn't the concern of the logging handler
- log filenames are computed from the created field of a LogRecord

Oh and for convenience a symlink to the latest log file can optionally be maintained.
