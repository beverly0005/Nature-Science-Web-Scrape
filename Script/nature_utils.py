########################################################################################################################
#   Create Functions for WebScrape in Nature
########################################################################################################################

import os
import urllib.request

from urllib.error import HTTPError
from urllib.request import urlopen as request
from bs4 import BeautifulSoup as Soup
from user_agent import generate_user_agent

# Set up proxies
os.environ['http_proxy'] = ''
proxies = {'http://91.185.222.11', 'http://3.17.154.4', 'http://178.128.116.248', 'http://1.10.188.103'}
proxy_support = urllib.request.ProxyHandler({'http': proxies})
opener = urllib.request.build_opener(proxy_support)
urllib.request.install_opener(opener)


# Functions
def sections(link, timeout=100, headers={'User-Agent': generate_user_agent(device_type="desktop")}):
    req = urllib.request.Request(link, None, headers)
    issue_page = request(req, timeout=timeout)
    issue_html = issue_page.read()
    issue_page.close()
    issue_soup = Soup(issue_html, 'html.parser')
    # Find the right table
    main = issue_soup.find(lambda tag: tag.name == 'div' and tag.get('data-container-type') == 'issue-section-list')
    sections = main.find_all('section')
    return sections


def remove_non_ascii_character(word):
    return word.encode('utf-8', errors='ignore').decode('unicode_escape', errors='ignore') \
        .encode('utf-8', errors='ignore').decode('ascii', 'ignore')


def articlepage_level(web_base, ArticleID, headers={'User-Agent': generate_user_agent(device_type="desktop")},
                      timeout=500):
    # find specific article page
    try:
        req = urllib.request.Request(web_base + ArticleID, None, headers)
        article_page = request(req, timeout=timeout)

        # Triple attempts
        tmp = 1
        while tmp <= 3:
            try:
                article_html = article_page.read()
                tmp = 5
            except http_client.IncompleteRead as e:
                tmp = tmp + 1
                if tmp == 3:
                    article_html = e.partial
            except:
                tmp = tmp + 1

        article_page.close()
        article_soup = Soup(article_html, "html.parser")
        main = article_soup.find('header')
        if main is None:
            main = article_soup.find(lambda tag: tag.name == 'div' and tag.get('id') == 'content')
            if main is None:
                print('Error: No Header for Article')
    except HTTPError:
        main = None
    except TypeError:
        main = None

    return main


def authoraffiliations(web_base, ArticleID, ntry=1):
    try:
        main = articlepage_level(web_base, ArticleID)
        authoraffil = main.find_all(lambda tag: tag.name == 'li' and tag.get('itemprop') == 'author')
    except AttributeError:
        authoraffil = None
    except:
        if ntry <= 3:
            ntry += 1
            authoraffiliations(web_base, ArticleID, ntry)

    return authoraffil


def affiliations(authoraffiliation, ntry=1):
    try:
        allaffil = authoraffiliation.find_all(lambda tag: tag.name == 'span' and tag.get('itemprop') == 'affiliation')
    except HTTPError:
        print('HTTPError')
        print('Refreshing the Page'
              'Number of Try:{}'.format(ntry))
        if ntry <= 3:
            affiliations(authoraffiliation, ntry + 1)
    return allaffil
