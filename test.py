import requests
import json

url = "https://www.jobsatamazon.co.uk/graphql"

query = """
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
      totalPayRateMin
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
      __typename
    }
    __typename
  }
}
"""

payload = {
    "query": query,
    "variables": {
        "searchJobRequest": {
            "locale": "en-GB",
            "country": "United Kingdom",
            "keyWords": "",
            "equalFilters": [],
            "containFilters": [
                {
                    "key": "isPrivateSchedule",
                    "val": ["true", "false"]
                }
            ],
            "rangeFilters": [],
            "orFilters": [],
            "dateFilters": [],
            "sorters": [
                {
                    "fieldName": "totalPayRateMax",
                    "ascending": "false"
                }
            ],
            "pageSize": 100,
            "consolidateSchedule": True
        }
    }
}

headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "Bearer Status|unauthenticated|Session|YOUR_SESSION_TOKEN",
    "content-type": "application/json",
    "country": "United Kingdom",
    "origin": "https://www.jobsatamazon.co.uk",
    "referer": "https://www.jobsatamazon.co.uk/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=30
)

print("Status:", response.status_code)

try:
    data = response.json()
    print(json.dumps(data, indent=2))
except requests.exceptions.JSONDecodeError:
    print(response.text)