from .SealedScraper import SealedScraper

class ManaforceScraper(SealedScraper):
    """
    Manaforce doesn't carry sealed products as of March 2023
    """

    def __init__(self, setName):
        SealedScraper.__init__(self, setName)
        self.website = 'manaforce'
        self.url = ''
