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
    "Authorization": os.getenv(
        "AMAZON_AUTHORIZATION",
        "Bearer Status|unauthenticated|Session|YOUR_SESSION_TOKEN",
    ),
    "Content-Type": "application/json",
    "Origin": "https://www.jobsatamazon.co.uk",
    "Referer": "https://www.jobsatamazon.co.uk/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
}

SEARCH_PAYLOAD = {
    "variables": {
        "searchJobRequest": {
            "locale": "en-GB",
            "country": "United Kingdom",
            "keyWords": os.getenv("AMAZON_KEYWORDS", ""),
            "equalFilters": [],
            "containFilters": [
                {"key": "isPrivateSchedule", "val": ["true", "false"]}
            ],
            "rangeFilters": [],
            "orFilters": [],
            "dateFilters": [],
            "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
            "pageSize": 100,
            "consolidateSchedule": True,
        }
    },
    "query": """
    query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
      searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
                nextToken
        jobCards {
          jobId
                    language
                    dataSource
                    requisitionType
          jobTitle
                    jobType
                    employmentType
          city
          state
          postalCode
                    locationName
          totalPayRateMax
                    tagLine
                    bannerText
                    image
                    jobPreviewVideo
                    distance
                    featuredJob
                    bonusJob
                    bonusPay
                    scheduleCount
                    currencyCode
                    geoClusterDescription
                    surgePay
                    jobTypeL10N
                    employmentTypeL10N
                    bonusPayL10N
                    surgePayL10N
                    totalPayRateMinL10N
                    totalPayRateMaxL10N
                    distanceL10N
                    monthlyBasePayMin
                    monthlyBasePayMinL10N
                    monthlyBasePayMax
                    monthlyBasePayMaxL10N
                    jobContainerJobMetaL1
                    virtualLocation
                    poolingEnabled
                    payFrequency
        }
      }
    }
    """,
}
