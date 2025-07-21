class PDFDownloadError(Exception):
    def __init__(self, message: str = "Bad request, maybe your download token is deprecated."):
        super().__init__(message)
        self.status_code = 400  # Bad Request

class PDFFetchForbiddenError(PDFDownloadError):
    def __init__(self, message: str = "Access to the PDF is forbidden."):
        super().__init__(message)
        self.status_code = 403 # Forbidden

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
