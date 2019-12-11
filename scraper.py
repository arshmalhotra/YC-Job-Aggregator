from requests import get, post
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
from geotext import GeoText
from fuzzywuzzy import process
import certifi
import ssl
import geopy.geocoders
from geopy.geocoders import Nominatim
import urllib.request, json

massiveCSV = pd.read_csv('./organizations.csv')
FC_API_KEY = 'PloT13uDXv2S0M7MU3p3ztb3WGJxiYEb'
MQ_API_KEY = 'ALxx74m6uGxA41aH7H93qxufXNYdglxD'

ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx
geolocator = Nominatim(user_agent="YC-Job-Mapper", timeout=5)

def getData(pages):
    allJobs = []
    allDates = []
    moreLink = "jobs"

    for i in range(int(numPages)):
        page = get("https://news.ycombinator.com/" + moreLink)
        # print(page)
        soup = BeautifulSoup(page.content, 'html.parser')
        allJobs += soup.find_all('tr',class_='athing')
        allDates += soup.find_all('td',class_='subtext')
        print(f"going to {i} page")
        moreLink = soup.find('a', class_='morelink')['href']
        sleep(10)

    return allJobs, allDates

def getText(fromData):
    return fromData.find('a').get_text()

def getCompany(fromTitle):
    idx = fromTitle.find('(Y')
    if idx > -1:
        return fromTitle[:idx].strip()
    return ''

def getCity(fromTitle):
    formatedTitle = ' '.join([s.capitalize() for s in fromTitle.split()])
    places = GeoText(formatedTitle, country='US')
    if list(places.cities):
        return places.cities
    elif 'SF' in fromTitle:
        return ['San Francisco']
    elif 'NYC' in fromTitle:
        return ['New York City']
    elif 'LA' in fromTitle:
        return ['Los Angeles']
    else:
        return None

def getJobs(fromTitle):
    jobCategories = {
        'Engineer': ['engineer', 'eng', 'developer', 'dev'],
        'Director': ['director'],
        'Head/Lead': ['head', 'lead'],
        'Sales': ['sales'],
        'Manager': ['manager', 'pm']
    }
    priorityCategories = ['Director', 'Head/Lead', 'Manager']
    jobs = []
    lowerCaseTitle = fromTitle.lower()

    for position, keywords in jobCategories.items():
        bestMatch = process.extractOne(lowerCaseTitle, keywords)
        if bestMatch[1] >= 60:
            jobs.append(position)

    if not any(op in lowerCaseTitle for op in ['and', 'or']):
        temp = jobs
        jobs = [cat for cat in priorityCategories if cat in jobs]
        jobs = jobs if jobs else temp

    return jobs

def getFunding(fromHTML):
    categories = fromHTML.find_all('h6', class_='text-secondary')
    values = fromHTML.find_all('div', class_='badge badge-secondary ml-auto')
    pairs = zip(categories, values)

    for pair in pairs:
        cat = pair[0].get_text().strip()
        val = pair[1].get_text().strip()
        if 'Funding' in cat:
            return val

    return None

def getLocation(fromHTML):
    details = fromHTML.find_all('p', class_='lighter')
    for detail in details:
        cat = detail.get_text().strip()
        if 'Location' in cat and 'United States' in cat:
            return cat[10:cat.index(',', 10)]

    return None

def getCompanyInfo(ofCompany):
    co = ofCompany.lower()
    coURL = co.replace(' ', '-')
    url = 'https://www.ycdb.co/company/' + coURL

    ycdb = get(url)
    soup = BeautifulSoup(ycdb.content, 'html.parser')
    sleep(1)

    funding = getFunding(soup)
    location = getLocation(soup)



    return location, funding

cityToLatLong = {}

def getLatLong(location):
    url = 'http://www.mapquestapi.com/geocoding/v1/address?key=' + MQ_API_KEY
    data = json.dumps({
        "location": location,
        "options": {
            "thumbMaps": False
        }
    })
    response = post(url, data=data)
    jsonResp = response.json()
    # print(jsonResp)
    if jsonResp['info']['statuscode'] == 0:
        latLong = jsonResp['results'][0]['locations'][0]['displayLatLng']
        # print(latLong)
        return latLong['lat'], latLong['lng']
        # return 0,1
    # if location in cityToLatLong:
    #     return cityToLatLong[location]
    # loc = geolocator.geocode(location)
    # cityToLatLong[location] = (loc.latitude, loc.longitude)
    # return loc.latitude, loc.longitude

def getAddress(ofCompany, withCity):
    domain = massiveCSV.loc[massiveCSV['name']==ofCompany, 'homepage_domain']
    if any(domain.values):
        data = json.dumps({
            "domain": domain.values[0]
        })
        url = 'https://api.fullcontact.com/v3/company.enrich'
        header = {'Authorization': 'Bearer '+FC_API_KEY}
        response = post(url, data=data, headers=header)
        jsonResp = response.json()
        if jsonResp['location']:
            locations = jsonResp['details']['locations']
            if withCity:
                for loc in locations[:-1]:
                    if withCity[:-4] == loc.get('city'):
                        return loc['formatted'].strip()
            else:
                return locations[0]['formatted'].strip()
    return withCity

def createDataDict(allJobs, allDates, length):
    posts = {}
    j = 0
    # f = open("data.csv", "w+")
    # f.write("title,company,date,jobs,address,city,funding,lat,long\r\n")
    for i in range(length):
        title = getText(allJobs[i])
        print(f"working on: {title}")
        date = getText(allDates[i])
        date = date[3:] if 'on ' in date else date
        company = getCompany(title)
        jobs = getJobs(title)
        city, funding = getCompanyInfo(company)
        listingCity = getCity(title)
        if listingCity:
            city = listingCity[0]

        has_addy = False
        if company and jobs and city and funding:
            city += ', US'
            address = getAddress(company, city)
            if(address != city):
                has_addy = True
            lat,long = getLatLong(address)
            posts[j+1] = {
                'post_title': title,
                'company': company,
                'date_posted': date,
                'hiring': jobs,
                'location': address,
                'city': city,
                'funding': funding,
                'lat':lat,
                'long':long,
                'has_addy':has_addy
            }
            # f.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\r\n", title, company,
            #         date, jobs, address, city, funding, lat, long)
            j+=1
    # f.close()
    return posts

numPages = input("How many pages would you like to scrape (up to 10)? ")
allJobs, allDates = getData(numPages)
posts = createDataDict(allJobs, allDates, len(allJobs))

df = pd.DataFrame.from_dict(posts, orient='index')
df.to_csv('output-100.csv')
print(df)


# print(getAddress("Iris Automation", "San Francisco, US"))
