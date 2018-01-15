class FontieException(Exception):
    def __init__(self, code, message, original_exception=None):
        super(FontieException, self).__init__(message)
        self.code = code
        self.message = message
        self.original_exception = original_exception
