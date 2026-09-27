"""Safe, transport-independent business errors."""


class ApplicationError(Exception):
    code = "application_error"
    message = "The operation could not be completed."


class NotFound(ApplicationError):
    code = "not_found"
    message = "The resource was not found."


class PermissionDenied(ApplicationError):
    code = "permission_denied"
    message = "You do not have permission to perform this action."


class Conflict(ApplicationError):
    code = "conflict"
    message = "The operation conflicts with the current resource state."


class LastAdminConflict(Conflict):
    code = "last_admin"
    message = "A workspace must keep at least one Admin."


class InvalidAssignment(ApplicationError):
    code = "invalid_assignee"
    message = "The assignee must be an eligible member of this workspace."


class InvalidInput(ApplicationError):
    code = "invalid_input"
    message = "The input is invalid."


class Unauthenticated(ApplicationError):
    code = "unauthenticated"
    message = "Valid authentication is required."


class DependencyUnavailable(ApplicationError):
    code = "dependency_unavailable"
    message = "The service is temporarily unavailable."


class RateLimited(ApplicationError):
    code = "rate_limited"
    message = "Too many requests. Please try again later."

    def __init__(self, retry_after: int) -> None:
        super().__init__(self.message)
        self.retry_after = retry_after
