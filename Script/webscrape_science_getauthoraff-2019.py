##################################################################################################################
#                          Web Scrape information on author and affiliations for Science
#
# Scrape the website: 'https://science.sciencemag.org'
# Check first the website: https://science.sciencemag.org/robots.txt to see if any restriction on web-scrape
# Need input data: "../Data/science_volissue_table_.csv"
##################################################################################################################

# Import Library
import csv
import time
import pandas as pd
from science_utils import *

# Input Variables
# website
url_base = 'https://science.sciencemag.org/content/by/year/'
web_base = 'https://science.sciencemag.org'
CHROMEDRIVER = 'chromedriver.exe'
# Output file
datapath = '../Data/'
outputpath = '../Output/'
FILENAME_VOLISSUE = 'science_volissue_table_'
FILENAME_AUTHOR = 'science_author_table_'
FILENAME_AFFIL = 'science_affil_table_'
# Output column
FIELDS_AUTHOR = ['year', 'volume', 'issue', 'article_id', 'content', 'section', 'title', 'authors_list', 'author',
                 'author_sequence', 'symbol']
FIELDS_AFFIL = ['year', 'volume', 'issue', 'article_id', 'content', 'section', 'title', 'symbol', 'affiliation']


# Web-scrape the data from Nature website
# 1975-2015
years = range(1975, 2015)
for year in years:
    df = pd.read_csv(datapath + 'science_volissue_table_.csv')

    if os.path.isfile(outputpath + FILENAME_AFFIL + str(year) + '.csv') is True:
        oldfile_affil = pd.read_csv(outputpath + FILENAME_AFFIL + str(year) + '.csv', encoding='ISO-8859–1')
        lastvolume = oldfile_affil.tail(1).iloc[0]['volume']
        lastissue = oldfile_affil.tail(1).iloc[0]['issue']
        mode = 'a'
    else:
        lastvolume = 0
        lastissue = 0
        mode = 'w'

    with open(outputpath + FILENAME_AUTHOR + str(year) + '.csv', mode, newline='') as csv_author, \
            open(outputpath + FILENAME_AFFIL + str(year) + '.csv', mode, newline='') as csv_affil:  # create a csv file
        file_author = csv.DictWriter(csv_author, fieldnames=FIELDS_AUTHOR)
        file_affil = csv.DictWriter(csv_affil, fieldnames=FIELDS_AFFIL)
        file_author.writeheader()
        file_affil.writeheader()

        for index, row in df[df['year'] == year].iterrows():
            if row['volume'] < int(lastvolume) or (row['volume'] == int(lastvolume) and row['issue'] < int(lastissue)):
                continue
            else:
                Volume = str(row['volume'])
                Issue = str(row['issue'])
                link = web_base + '/content/' + Volume + '/' + Issue

            for article in article_level(link):
                ArticleTitle = article.text
                ArticleTitle = remove_non_ascii_character(ArticleTitle)
                ArticleID = generate_article_id(article)
                ArticleContent = content_level(article)
                ArticleAuthors = article_authors(article)
                ArticleAuthors = remove_non_ascii_character(ArticleAuthors) if not isinstance(
                    ArticleAuthors, str) else ArticleAuthors

                time.sleep(5)
                header = articlepage_level(web_base, ArticleID)
                ArticleSection = header.find(lambda tag: tag.name == 'div' and tag.get('class') == ['overline'])
                ArticleSection = remove_non_ascii_character(ArticleSection.text) if not (ArticleSection is None) else ''
                author_symbol_list, affil_symbol_list = author_affiliation(header)

                for AuthorName, AuthorSeq, AuthorSymbol in author_symbol_list:
                    try:
                        file_author.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                              'article_id': ArticleID, 'content': ArticleContent,
                                              'section': ArticleSection, 'title': ArticleTitle,
                                              'authors_list': ArticleAuthors, 'author': AuthorName,
                                              'author_sequence': AuthorSeq, 'symbol': AuthorSymbol})
                    except Exception as e:
                        print(e)
                        AuthorSymbol = AuthorSymbol.encode('utf-8')
                        file_author.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                              'article_id': ArticleID, 'content': '', 'section': ArticleSection,
                                              'title': ArticleTitle, 'authors_list': ArticleAuthors,
                                              'author': AuthorName, 'author_sequence': AuthorSeq,
                                              'symbol': AuthorSymbol})

                for SymbolName, Affil in affil_symbol_list:
                    try:
                        file_affil.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                             'article_id': ArticleID, 'content': '', 'section': ArticleSection,
                                             'title': ArticleTitle, 'symbol': SymbolName, 'affiliation': Affil})
                    except Exception as e:
                        print(e)
                        SymbolName = SymbolName.encode('utf-8')
                        file_affil.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                             'article_id': ArticleID, 'content': '', 'section': ArticleSection,
                                             'title': ArticleTitle, 'symbol': SymbolName, 'affiliation': Affil})
                    print(ArticleSection)
                    print(str(year) + '/' + Volume + '/' + Issue + '/' + ArticleTitle + '/' + Affil)