# %%
import json
from pathlib import Path

import requests

from pyjstat import pyjstat


# %%
def hent_fornavn():
    """
    Hent alle fornavn fra ssb for begge kjønn
    """
    url = "https://data.ssb.no/api/v0/no/table/10501"
    data = {
        "query": [
            {"code": "Fornavn", "selection": {"filter": "all", "values": ["*"]}},
            {
                "code": "ContentsCode",
                "selection": {"filter": "item", "values": ["Personer"]},
            },
            {
                "code": "Tid",
                "selection": {
                    "filter": "item",
                    "values": ["2013", "2014", "2015", "2020", "2021"],
                },
            },
        ],
        "response": {"format": "json-stat2"},
    }
    d = requests.post(url, json=data)
    return d


# %%
def hent_etternavn():
    """
    Hent alle etternavn fra ssb for begge kjønn
    """
    url = "https://data.ssb.no/api/v0/no/table/12891"
    data = {
        "query": [
            {"code": "Etternavn", "selection": {"filter": "all", "values": ["*"]}},
            {
                "code": "ContentsCode",
                "selection": {"filter": "item", "values": ["Personer"]},
            },
            {
                "code": "Tid",
                "selection": {
                    "filter": "item",
                    "values": ["2018", "2019", "2020", "2021"],
                },
            },
        ],
        "response": {"format": "json-stat2"},
    }
    r = requests.post(url, json=data)
    return r


# %%
def pyjstat_to_df(filsti: Path):
    """
    Last inn json-stat data fra JSON-fil og konvertér til dataframe
    """
    with open(filsti, "r") as f:
        j = json.load(f)
        s = json.dumps(j)
        dataset = pyjstat.Dataset.read(s)
        df = dataset.write("dataframe")
    return df
