from requests import get
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
from geotext import GeoText
from fuzzywuzzy import process
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="YC-Job-Search")

def getData(pages):
    allJobs = []
    allDates = []
    moreLink = "jobs"

    for i in range(int(numPages)):
        page = get("https://news.ycombinator.com/" + moreLink)
        soup = BeautifulSoup(page.content, 'html.parser')
        allJobs += soup.find_all('tr',class_='athing')
        allDates += soup.find_all('td',class_='subtext')
        moreLink = soup.find('a', class_='morelink')['href']
        sleep(3)

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

def getLatLong(city):
    loc = geolocator.geocode(city)
    return loc.latitude, loc.longitude


def createDataDict(allJobs, allDates, length):
    posts = {}
    j = 0
    for i in range(length):
        title = getText(allJobs[i])
        date = getText(allDates[i])
        company = getCompany(title)
        jobs = getJobs(title)
        city, funding = getCompanyInfo(company)
        listingCity = getCity(title)

        if listingCity:
            city = listingCity[0]

        if company and jobs and city and funding:
            city += ', US'
            lat,long = getLatLong(city)
            posts[j+1] = {
                'post_title': title,
                'company': company,
                'date_posted': date,
                'hiring': jobs,
                'city': city,
                'funding': funding,
                'lat':lat,
                'long':long
            }
        j+=1
    return posts


numPages = input("How many pages would you like to scrape (up to 10)? ")
allJobs, allDates = getData(numPages)
posts = createDataDict(allJobs, allDates, len(allJobs))

df = pd.DataFrame.from_dict(posts, orient='index')
df.to_csv('output.csv')
print(df)
