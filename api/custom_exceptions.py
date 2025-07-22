class PDFDownloadError(Exception):
    def __init__(self, message: str = "Bad request, maybe your download token is deprecated.", status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code  # Bad Request

class PDFFetchForbiddenError(Exception):
    def __init__(self, message: str = "Access to the PDF is forbidden.", status_code: int = 403):
        super().__init__(message)
        self.status_code = status_code # Forbidden

class InvalidPDFError(Exception):
    def __init__(self, message: str = "Invalid PDF file. There is no PDF file behind your link.", status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code  # Unprocessable Entity

class SemanticScholarError(Exception):
    def __init__(self, message: str = "Connection to SemanticScholar failed.", status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

class OpenAIError(Exception):
    def __init__(self, message: str = "Connection to OpenAi failed.", status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

class PDFParseError(Exception):
    def __init__(self, message: str = "Failed to parse PDF"):
        super().__init__(message)

class DOIExtractionError(Exception):
    def __init__(self, message: str = "Failed to extract DOI"):
        super().__init__(message)
