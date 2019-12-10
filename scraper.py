from requests import get
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
from geotext import GeoText

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
    places = GeoText(fromTitle)
    if list(places.cities):
        return places.cities
    elif 'SF' in fromTitle:
        return ['San Francisco']
    elif 'NYC' in fromTitle:
        return ['New York City']
    else:
        return None

def getJobTitle(fromTitle):
    jobTitle = ''
    lowerCaseTitle = fromTitle.lower()
    identifiers = ['hiring', 'seeks']
    ids = [(id, lowerCaseTitle.find(id)) for id in identifiers if id in lowerCaseTitle]
    if ids:
        idx = ids[-1][1] + len(ids[-1][0]) + 1
        jobTitle = fromTitle[idx:]
    return jobTitle

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
        if 'Location' in cat:
            return cat[10:]

    return None

def getCompanyInfo(ofCompany):
    co = ofCompany.lower()
    coURL = co.replace(' ', '-')
    url = 'https://www.ycdb.co/company/' + coURL

    ycdb = get(url)
    soup = BeautifulSoup(ycdb.content, 'html.parser')
    sleep(3)

    funding = getFunding(soup)
    location = getLocation(soup)

    

    return location, funding

def createDataDict(allJobs, allDates, length):
    posts = {}

    for i in range(length):
        title = getText(allJobs[i])
        date = getText(allDates[i])
        company = getCompany(title)
        jobTitle = getJobTitle(title)
        city, funding = getCompanyInfo(company)
        listingCity = getCity(title)
        if listingCity:
            city = listingCity[0]

        if company:
            posts[i+1] = {
                'post_title': title,
                'company': company,
                'date_posted': date,
                'hiring': jobTitle,
                'city': city,
                'funding': funding
            }
    return posts


numPages = input("How many pages would you like to scrape (up to 10)? ")
allJobs, allDates = getData(numPages)
posts = createDataDict(allJobs, allDates, len(allJobs))

df = pd.DataFrame.from_dict(posts, orient='index')
df.to_csv('output.csv')
print(df)
