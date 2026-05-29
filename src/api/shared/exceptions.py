class LockException(Exception):
    pass


class ClusterNotLockedException(LockException):
    pass


class ClusterLockNotFoundException(LockException):
    pass


class LockTokenMismatchException(LockException):
    pass


class ReleaseNotFoundException(Exception):
    pass


class InvalidProviderException(Exception):
    pass
