########################################################################################################################
#   Create Functions for WebScrape in Science
########################################################################################################################

import os
import re
import requests

from urllib.error import HTTPError
from bs4 import BeautifulSoup as Soup
from user_agent import generate_user_agent

# Proxies
os.environ['http_proxy'] = ''


# Functions
def article_level(link, timeout=100, headers={'User-Agent': generate_user_agent(device_type="desktop")}):
    # find all articles
    issue_page = requests.get(link, timeout=timeout, headers=headers)
    issue_soup = Soup(issue_page.content, "html.parser")

    if link != 'https://science.sciencemag.org/content/349/6254':
        # This issue is very special, we cannot scrape its articles information via "main"
        main = issue_soup.find_all(lambda tag: tag.name == 'div' and tag.get('role') == 'main')
        if len(main) == 1:
            articles = main[0].find_all(lambda tag: tag.name == 'div' and tag.get('class') == [
                'highwire-cite-title', 'media__headline__title'])
            print('1-Level Main')
        else:
            articles = 'Error: len(main) != 1'
            print('Error: Not 1-Level Main')
    else:
        articles = issue_soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['highwire-cite-title',
                                                                                       'media__headline__title'])
    return articles


def content_level(article):
    # find the topmost content level: special issue, content, etc.
    list0 = article.find_parent(lambda tag: tag.name == 'ul' and tag.get('class') == ['toc-section', 'item-list'])
    section = list0.find_parent('li')
    content = section.find_parent('li')
    if content == None:
        content_name = ''
    else:
        content_name = ' '.join(content['class'])
    return content_name


def article_authors(article):
    # find all authors of an article:
    parent = article.find_parent('h3')
    authors = parent.find_next_sibling(lambda tag: tag.name == 'p' and tag.get('class') == ['highwire-cite-authors',
                                                                                             'byline'])
    if authors == None:
        author_names = ''
    else:
        author_names = authors.text
        author_names = remove_non_ascii_character(author_names)
    return author_names


def articlepage_level(web_base, ArticleID, timeout=100, headers={'User-Agent': generate_user_agent(device_type="desktop")}):
    # find specific article page
    article_page = requests.get(web_base + ArticleID, timeout=timeout, headers=headers)
    article_soup = Soup(article_page.content, "html.parser")
    main = article_soup.find_all(lambda tag: tag.name == 'header' and tag.get('class') == ['article__header'])
    if len(main) == 1:
        header = main[0]
        print('1-Level Main')
    else:
        header = 'Error: len(main) != 1'
        print('Error: No Header for Article')
    return header


def author_affiliation(header, ntry=1):
    # find author affiliation of an article
    author_symbol_list = []
    affiliation_symbol_list = []

    try:
        contributors = header.find_all(lambda tag: tag.name == 'ol' and tag.get('class') == ['contributor-list'])
        affiliations = header.find_all(lambda tag: tag.name == 'ol' and tag.get('class') == ['affiliation-list'])

        # Getting author_symbol_list
        if len(contributors) > 0:
            for contributor in contributors:
                contributor_list = contributor.find_all(lambda tag: tag.name == 'li')
                author_symbol_list += parse_contributor_list(contributor_list)
        else:
            try:
                contributor = header.find(lambda tag: tag.name == 'span' and tag.get('class') == [
                    'highwire-citation-authors'])
                author = remove_non_ascii_character(contributor.text)
                author_symbol_list = [[author, '', '']]
            except:
                author_symbol_list = [['', '', '']]

        # Getting affiliation_symbol_list
        if len(affiliations) > 0:
            for affiliation in affiliations:
                affiliation_list = affiliation.find_all(lambda tag: tag.name == 'li')
                affiliation_symbol_list += parse_affiliation_symbol(affiliation_list)
        else:
            affiliation_symbol_list = [['', '']]

    except HTTPError:
        print('HTTPError')
        print('Refreshing the Page'
              'Number of Try:{}'.format(ntry))
        if ntry <= 3:
            author_affiliation(header, ntry + 1)
    except IndexError:
        author_symbol_list = ['', '', '']
        affiliation_symbol_list = ['', '']
        print('IndexError')
    except Exception as e:
        author_symbol_list = ['', '', '']
        affiliation_symbol_list = ['', '']
        print(e)
    return author_symbol_list, affiliation_symbol_list


def parse_contributor_list(contributor_list):
    # parse contributor list to return author_symbol_list
    author_symbol_list = []
    author_seq = 1
    for contributor in contributor_list:
        author_name = contributor.find(lambda tag: tag.name == 'span').text
        author_name = remove_non_ascii_character(author_name)
        author_symbol = parse_author_symbol(contributor)
        author_symbol_list += [[author_name, author_seq, author_symbol]]
        author_seq += 1
    return author_symbol_list


def parse_author_symbol(contributor):
    # parse all the symbols relevant to an author of an article
    author_symbol_list = contributor.find_all(lambda tag: tag.name == 'sup')
    author_symbol_affil = ''
    if len(author_symbol_list) > 0:
        author_symbol_affil = ','.join([author_symbol.text for author_symbol in author_symbol_list])
    else:
        author_symbol_list = contributor.find_all(lambda tag: tag.name == 'a')
        author_symbol_affil = ','.join([author_symbol.text for author_symbol in author_symbol_list])
    return author_symbol_affil


def parse_affiliation_symbol(affiliation_list):
    affil_symbol_list = []
    for affiliation in affiliation_list:
        symbol_name = affiliation.find(lambda tag: tag.name == 'sup')
        if symbol_name is not None:
            symbol_name = symbol_name.text
        else :
            symbol_name = ''

        affil = affiliation.find(lambda tag: tag.name == 'address').text.strip()

        if symbol_name != '':
            try:  # If symbol_name is an integer
                symbol_name = int(symbol_name)
                affil = re.sub(r'^' + str(symbol_name), '', affil)
            except ValueError:  # If symbol_name is a special character
                affil = re.sub('['+ symbol_name + ']', '', affil)

        affil = remove_non_ascii_character(affil)
        affil_symbol_list += [[symbol_name, affil]]
    return affil_symbol_list


def generate_article_id(article):
    # find article id in the form of link to the article
    list0 = article.find_parent('a')
    section_link = list0['href']
    return section_link


def remove_non_ascii_character(word):
    return word.encode('utf-8', errors='ignore').decode('unicode_escape', errors='ignore')\
        .encode('utf-8', errors='ignore').decode('ascii', 'ignore')