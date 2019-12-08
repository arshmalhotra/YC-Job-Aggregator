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
        sleep(5)

    return allJobs, allDates

def getText(fromData):
    return fromData.find('a').get_text()

def getCompany(fromTitle):
    idx = fromTitle.find('(Y')
    if idx:
        return fromTitle[:idx]
    return ''

def getCity(fromTitle):
    places = GeoText(fromTitle)
    return places.cities

def getJobTitle(fromTitle):
    jobTitle = ''
    lowerCaseTitle = fromTitle.lower()
    identifiers = ['is hiring', 'seeks']
    ids = [(id, lowerCaseTitle.find(id)) for id in identifiers if id in lowerCaseTitle]
    if ids:
        idx = ids[-1][1] + len(ids[-1][0]) + 1
        jobTitle = fromTitle[idx:]
    return jobTitle

def createDataDict(allJobs, allDates, length):
    posts = {}

    for i in range(length):
        title = getText(allJobs[i])
        date = getText(allDates[i])
        company = getCompany(title)
        city = getCity(title)
        jobTitle = getJobTitle(title)

        if company:
            posts[i] = {
                'post_title': title,
                'company': company,
                'date_posted': date,
                'hiring': jobTitle,
                'city': city
            }
    return posts

numPages = input("How many pages would you like to scrape (up to 10)? ")
allJobs, allDates = getData(numPages)
posts = createDataDict(allJobs, allDates, len(allJobs))

df = pd.DataFrame.from_dict(posts, orient='index')
df.to_csv('output.csv')
print(df.values)
