class AdoWrapperException(Exception):
    pass


class ResourceNotFound(AdoWrapperException):
    pass


class DeletionFailed(AdoWrapperException):
    pass


class ResourceAlreadyExists(AdoWrapperException):
    pass


class UnknownError(AdoWrapperException):
    pass


class InvalidPermissionsError(AdoWrapperException):
    pass


class UpdateFailed(AdoWrapperException):
    pass


class AuthenticationError(AdoWrapperException):
    pass


class ConfigurationError(AdoWrapperException):
    pass


class NoElevatedPrivilegesError(AdoWrapperException):
    pass
