import os


GRAPHQL_URL = os.getenv(
    "AMAZON_GRAPHQL_URL",
    "https://www.jobsatamazon.co.uk/graphql",
)
JOB_PAGE_URL = (
    "https://www.jobsatamazon.co.uk/app#/jobSearch"
    "?query=Warehouse%20Operative&locale=en-GB"
)

HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": "https://www.jobsatamazon.co.uk",
    "Referer": "https://www.jobsatamazon.co.uk/app",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
}

SEARCH_PAYLOAD = {
    "operationName": "searchJobCardsByLocation",
    "variables": {
        "searchJobRequest": {
            "locale": "en-GB",
            "country": "United Kingdom",
            "keyWords": os.getenv("AMAZON_KEYWORDS", "Warehouse Operative"),
            "equalFilters": [],
            "containFilters": [
                {"key": "isPrivateSchedule", "val": ["true", "false"]}
            ],
            "rangeFilters": [],
            "orFilters": [],
            "dateFilters": [],
            "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
            "pageSize": 20,
            "consolidateSchedule": True,
        }
    },
    "query": """
    query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
      searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
        jobCards {
          jobId
          jobTitle
          city
          state
          postalCode
          jobType
          employmentType
          totalPayRateMax
        }
      }
    }
    """,
}
