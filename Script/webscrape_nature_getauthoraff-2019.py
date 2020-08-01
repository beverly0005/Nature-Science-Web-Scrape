##################################################################################################################
#                          Web Scrape information on author and affiliations for Nature
#
# Scrape the website: https://www.nature.com/nature/volumes
# Check first the website: https://www.nature.com/robots.txt to see if any restriction on web-scrape
# Need input data: "../Data/nature_volissue_table_.csv"
##################################################################################################################

# Import Library
import csv
import time
import pandas as pd
from nature_utils import *

# Input Variables
# website
url_base = 'https://www.nature.com/nature/volumes'
web_base = 'https://www.nature.com'
CHROMEDRIVER = 'chromedriver.exe'
# output file
datapath = '../Data/'
outputpath = '../Output/'
FILENAME_VOLISSUE = 'nature_volissue_table_'
FILENAME_AUTHOR = 'nature_author_table_'
FILENAME_AFFIL = 'nature_affil_table_'
# output column
FIELDS_VOLISSUE = ['year', 'volume', 'issue']
FIELDS_AUTHOR = ['year', 'volume', 'issue', 'article_id', 'section', 'title', 'author',
                 'author_sequence']
FIELDS_AFFIL = ['year', 'volume', 'issue', 'article_id', 'section', 'title', 'author_seq',
                'affiliation']


# Web-scrape the data from Nature website
# 1975-2015
years = range(1975, 2015)
for year in years:
    df = pd.read_csv(datapath + 'nature_volissue_table_.csv')

    """Webscraping may be interrupted by network connection. 
       We want to check if  webscraping of a specific year has be completed or not, 
       before move to next year. (Also see the part later)"""
    if os.path.isfile(outputpath + FILENAME_AFFIL + str(year) + '.csv') is True:
        oldfile_affil = pd.read_csv(outputpath + FILENAME_AFFIL + str(year) + '.csv', encoding='ISO-8859–1',
                                    error_bad_lines=False)
        lastvolume = oldfile_affil.tail(1).iloc[0]['volume']
        lastissue = oldfile_affil.tail(1).iloc[0]['issue']
        mode = 'a'
    else:
        lastvolume = 1000000
        lastissue = 1000000
        mode = 'w'

    # Write into author and affiliation tables
    with open(outputpath + FILENAME_AUTHOR + str(year) + '.csv', mode, newline='') as csv_author, \
            open(outputpath + FILENAME_AFFIL + str(year) + '.csv', mode, newline='') as csv_affil:  # create a csv file
        file_author = csv.DictWriter(csv_author, fieldnames=FIELDS_AUTHOR)
        file_affil = csv.DictWriter(csv_affil, fieldnames=FIELDS_AFFIL)
        file_author.writeheader()
        file_affil.writeheader()

        for index, row in df[df['year'] == year].iterrows():
            """Webscraping may be interrupted by network connection. 
               We want to check if  webscraping of a specific year has be completed or not, 
               before move to next year. """
            if row['volume'] > int(lastvolume) or (row['volume'] == int(lastvolume) and row['issue'] > int(lastissue)):
                continue
            else:
                Volume = str(row['volume'])
                Issue = str(row['issue'])
                link = url_base + '/' + Volume + '/issues/' + Issue

            for section in sections(link):
                ArticleSection = section.get('aria-labelledby')

                for article in section.find_all('article'):
                    try:
                        ArticleTitle = article.find('a').text
                    except AttributeError:
                        continue
                    ArticleTitle = remove_non_ascii_character(ArticleTitle).replace('\n', '').lstrip()
                    ArticleID = article.find('a').get('href')
                    ExistAuthor = article.find(lambda tag: tag.name == 'ul' and (tag.get('data-test') == 'author-list'
                                                                                 or tag.get('data-test') == [
                                                                                     'author-list']))

                    #   For the following issues, "Articles" and "Letters" have been put together under Section
                    #   "Research" with "News" etc.
                    if int(Issue) >= 7314:
                        try:
                            Add = article.find_parent('li').find_previous_sibling('h3').text
                        except:
                            Add = 'error'
                        ArticleSection = ArticleSection + Add

                    if ExistAuthor is None:  # No author part at all
                        print(str(year) + '/' + Volume + '/' + Issue + '/' + ArticleTitle)
                        file_author.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                              'article_id': ArticleID, 'section': ArticleSection,
                                              'title': ArticleTitle, 'author': '', 'author_sequence': ''})
                        file_affil.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                             'article_id': ArticleID, 'section': ArticleSection,
                                             'title': ArticleTitle, 'affiliation': ''})
                    else:
                        AuthorSeq = 0
                        time.sleep(10)
                        if (authoraffiliations(web_base, ArticleID) is None) or (
                                len(authoraffiliations(web_base, ArticleID)) == 0):  # No author information
                            file_author.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                                  'article_id': ArticleID, 'section': ArticleSection,
                                                  'title': ArticleTitle, 'author': '',
                                                  'author_sequence': ''})
                            file_affil.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                                 'article_id': ArticleID, 'section': ArticleSection,
                                                 'title': ArticleTitle, 'author_seq': '',
                                                 'affiliation': ''})
                            print(str(year) + '/' + Volume + '/' + Issue + '/' + ArticleTitle)
                        else:  # Have author information and loop over all authors
                            for authoraffiliation in authoraffiliations(web_base, ArticleID):
                                AuthorName = authoraffiliation.find('a').text
                                AuthorName = remove_non_ascii_character(AuthorName)
                                AuthorSeq += 1
                                file_author.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                                      'article_id': ArticleID, 'section': ArticleSection,
                                                      'title': ArticleTitle, 'author': AuthorName,
                                                      'author_sequence': AuthorSeq})

                            ExistAffil = affiliations(authoraffiliation)
                            if len(ExistAffil) == 0:  # No affiliation information
                                file_affil.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                                     'article_id': ArticleID, 'section': ArticleSection,
                                                     'title': ArticleTitle, 'author_seq': AuthorSeq,
                                                     'affiliation': ''})
                                print(str(year) + '/' + Volume + '/' + Issue + '/' + ArticleTitle + ':' + AuthorName)
                            else:
                                for affiliation in ExistAffil:  # Loop over all affiliation
                                    Affiliation = affiliation.find(lambda tag: tag.name == 'meta' and
                                                                               tag.get('itemprop') == 'address').get(
                                        'content')
                                    Affiliation = remove_non_ascii_character(Affiliation)
                                    file_affil.writerow({'year': year, 'volume': Volume, 'issue': Issue,
                                                         'article_id': ArticleID, 'section': ArticleSection,
                                                         'title': ArticleTitle, 'author_seq': AuthorSeq,
                                                         'affiliation': Affiliation})

                                    print(str(
                                        year) + '/' + Volume + '/' + Issue + '/' + ArticleTitle + ':' + AuthorName)