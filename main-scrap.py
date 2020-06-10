#!/bin/bash/python3
import scrapy
from scrapy.crawler import CrawlerProcess
import re
import sys
from os import path
from process_csv import process_file

# Constants
DESC_REG = re.compile("^.*(locaux|logements).*(\d{4})(\d{2}).*$")
PROCESSED_DIR="data/processed"
PENDING_DIR="data/pending"

OUTFILE = lambda dir, type, year, month : path.join(dir, f"{type}-{year}-{month}.csv")

class Scrapper(scrapy.Spider):

    name = "scrapper"
    start_urls= ["https://www.data.gouv.fr/fr/datasets/base-des-permis-de-construire-sitadel/"]

    def parse(self, response):

        for article in response.css("article.card") :
            desc = article.css("h4::text").extract_first()
            match = DESC_REG.match(desc)
            if match :
                type = match.group(1)
                year = match.group(2)
                month = match.group(3)
                checkfile = OUTFILE(PROCESSED_DIR, type, year, month)
                outfile = OUTFILE(PENDING_DIR, type, year, month)

                if path.exists(checkfile) :
                    print(f"File {checkfile} already exists : skipping")
                else:
                    print(f"Downloading {checkfile}")
                    href = article.css("a::attr('href')").extract_first()
                    yield scrapy.Request(href, self.download_csv, meta = dict(outfile=outfile))

    def download_csv(self, response) :

        # Download new CSV
        csvfile = response.meta['outfile']
        base, _ = path.splitext(csvfile)
        jsonfile = base + '.json'
        errfile = base + '.err'
        with open(csvfile, 'wb') as f:
            f.write(response.body)

        # Process it (to CSV)
        with open(jsonfile, "w") as jsonout, open(errfile, "w") as errfile :
            process_file(csvfile, jsonout, errfile)

process = CrawlerProcess()
process.crawl(Scrapper)
process.start()