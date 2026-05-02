class AiProviderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ProviderConfigurationError(AiProviderError):
    pass


class ProviderRequestError(AiProviderError):
    pass


class ProviderOutputError(AiProviderError):
    pass
