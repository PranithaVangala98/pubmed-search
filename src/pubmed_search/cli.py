import requests
import click
import xmltodict
import json

def xml_to_dict(xml_string):
    xml_dict = xmltodict.parse(xml_string)
    json_data = json.dumps(xml_dict, indent=4)
    return json.loads(json_data)

def fetch_id_metadata(id_list):
   base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
   input_PMID_list = ','.join(map(str, id_list))
   print(input_PMID_list)
   params = {
        "db": "pubmed",
        "id": input_PMID_list,
        "sort": 'relevance'
    }
   r = requests.post(base_url,data=params)
   if r.status_code == 200:
      return xml_to_dict(r.text)['eSummaryResult']['DocSum'][:1]
   else:
      return None
   

@click.command()
@click.argument("input_text", required=True)
@click.option("--debug", "-d", default=False, type=bool, required=False, help="run in debug mode")
@click.option("--file", "-f", default=None, type=str, required=False, help="output file name")
def cli(input_text:str,debug: float, file: float) -> None:
  print('text searched for is',input_text)
  r = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=science[journal]+AND+breast+cancer+AND+2008[pdat]')
  if r.status_code == 200:
    id_list = xml_to_dict(r.text)['eSearchResult']['IdList']['Id']
    print(id_list)
    print(fetch_id_metadata(id_list))
  else:
    print("something went wrong, please try later!")

if __name__ == "__main__":
    cli()