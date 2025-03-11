import requests
import json
import xmltodict
import re
import csv
import click


def filterValidAuthors(authorsInfo):
    keywords = ['department', 'school', 'university', 'institute', 'college']
    validAuthors = []
    for author in authorsInfo:
        for aff in author['affiliations']:
            contians = any(keyword in aff.lower() for keyword in keywords)
            if not contians:
                validAuthors.append(author)

    return validAuthors


def getAuthorName(author):
    return (author['ForeName'] if isinstance(author, dict) and 'ForeName' in author else '')+" "+(author['LastName'] if isinstance(author, dict) and 'LastName' in author else '')

def extractAuthorListInfo(authorList):
    authorsInfo = []
    for author in authorList:
        if not 'AffiliationInfo' in author:
            continue
        fullName = getAuthorName(author=author)
        affiliationInfo = author['AffiliationInfo']
        affiliations = []
        if isinstance(affiliationInfo, dict):
            affiliations.append(affiliationInfo['Affiliation'])
        elif isinstance(affiliationInfo, list):
            for item in affiliationInfo:
                affiliations.append(item['Affiliation'])
        emails = []
        for aff in affiliations:
            email = re.findall(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", aff)
            emails.extend(email)
        authorsInfo.append({
            "name": fullName,
            "affiliations": affiliations,
            "emails": emails
        })
    return authorsInfo


def getPublicationType(item):
    if isinstance(item, dict):
        return item['#text']
    elif isinstance(item, list):
        return ",".join(list(map(lambda x: x['#text'], item)))
    return None


def getAuthorList(item):
    if isinstance(item, dict):
        return [item]
    elif isinstance(item, list):
        return item


def get_pubmed_artice_info(pubmed_article):
    pubMedId = pubmed_article['MedlineCitation']['PMID']['#text']
    articleTitle = pubmed_article['MedlineCitation']['Article']['ArticleTitle']

    publicationType = getPublicationType(pubmed_article['MedlineCitation']
                                         ['Article']['PublicationTypeList']['PublicationType'])

    if 'AuthorList' not in pubmed_article['MedlineCitation']['Article']:
        return None
    authorList = getAuthorList(
        pubmed_article['MedlineCitation']['Article']['AuthorList']['Author'])
    # print('pubmedid', pubMedId)
    authorsInfo = extractAuthorListInfo(authorList)
    validAuthors = filterValidAuthors(authorsInfo)
    if len(validAuthors) > 0:
        return {
            "pubMedId": pubMedId,
            "articleTitle": articleTitle,
            "publicationType": publicationType,
            "authors": list(map(lambda x: x['name'], validAuthors)),
            "affiliations": list(map(lambda x: x['affiliations'], validAuthors)),
            "emails": list(map(lambda x: x['emails'], validAuthors))
        }
    return None


def fetch_id_info(idList: list):
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    id_list_string = ",".join(map(str, idList))
    req_body = {
        'db': 'pubmed',
        'id': id_list_string,
    }
    r = requests.post(base_url, data=req_body)
    if r.status_code == 200:
        parsed = xmltodict.parse(r.text)
        data = []
        if isinstance(parsed['PubmedArticleSet']['PubmedArticle'], list):
            for pubmed_article in parsed['PubmedArticleSet']['PubmedArticle']:
                data.append(get_pubmed_artice_info(pubmed_article))

        elif isinstance(parsed['PubmedArticleSet'], dict):
            data.append(get_pubmed_artice_info(parsed['PubmedArticleSet']))

        data = list(filter(lambda x: x, data))
        return data
    else:
        print("Something went wrong, please try later")


def e_search(searchTerm='cancer',file='pubmed-articles.csv'):
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    params = {
        'db': 'pubmed',
        "term": searchTerm,
        "retmode": 'json',
        "retmax": 200
    }
    r = requests.get(base_url, params=params)
    if r.status_code == 200:
        parsed = json.loads(r.text)
        parsed = parsed['esearchresult'] if 'esearchresult' in parsed else {}
        idlist = parsed['idlist'] if 'idlist' in parsed else []
        data = fetch_id_info(idlist)
        with open(file, 'w', newline='') as csvfile:
            fieldnames = ['pubMedId', 'articleTitle',
                          'publicationType', 'authors', 'affiliations', 'emails']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    else:
        print("Something went wrong, please try later")

   

@click.command()
@click.argument("input_text", required=True)
@click.option("--debug", "-d", default=False, type=bool, required=False, help="run in debug mode")
@click.option("--file", "-f", default=None, type=str, required=False, help="output file name")
def cli(input_text:str,debug: float, file: str) -> None:
  
  if file and (not file.endswith('.csv')):
      print('Please give a vailid file name ending with .csv')
      return
  e_search(input_text,file)

if __name__ == "__main__":
    cli()