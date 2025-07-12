class PDFDownloadError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code

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
