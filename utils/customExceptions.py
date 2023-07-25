class TooManyRequestsError(Exception):
    """Raised when there are too many requests"""
    pass

class ScrapingError(Exception):
    """Raised when there is an error while scraping"""
    pass