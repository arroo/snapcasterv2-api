from scrapers.base.AetherVaultScraper import AetherVaultScraper

scraper = AetherVaultScraper("elspeth, sun's champion")

print(f'Scraping {scraper.website} for {scraper.cardName}')

scraper.scrape()

print("Scrape complete")
print("Results: ")
results = scraper.getResults()


