class ResourceNotFound(Exception):
    pass


class DeletionFailed(Exception):
    pass


class ResourceAlreadyExists(Exception):
    pass


class UnknownError(Exception):
    pass


class InvalidPermissionsError(Exception):
    pass


class UpdateFailed(Exception):
    pass


class AuthenticationError(Exception):
    pass


class ConfigurationError(Exception):
    pass
