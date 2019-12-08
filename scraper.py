from requests import get
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
from geotext import GeoText

num_pages = input("How many pages would you like to scrape (up to 10)? ")

allJobs = []
all_dates = []
morelink = "jobs"

for i in range(int(num_pages)):
    page = get("https://news.ycombinator.com/" + morelink)
    soup = BeautifulSoup(page.content, 'html.parser')
    allJobs += soup.find_all('tr',class_='athing')
    all_dates += soup.find_all('td',class_='subtext')
    morelink = soup.find('a', class_='morelink')['href']
    sleep(1)

job_titles = []
company = []

posts = {}
i = 0
k = 0
full_job_title = zip(allJobs,all_dates)

for j in full_job_title:
  job_titles.append(j[0].find('a').get_text())
  title = j[0].find('a').get_text()
  company = title[:title.find("(Y")] if title.find("(Y") != -1 else ""
  date = j[1].find('a').get_text()
  lowerCaseTitle = title.lower()
  job = ''
  if lowerCaseTitle.find('is hiring'):
      job = title[lowerCaseTitle.find('is hiring')+10:]
  elif lowerCaseTitle.find('seeks'):
      job = title[lowerCaseTitle.find('seeks')+6]
  if company:
    posts.update({k:{"post_title":title,"company":company,"date_posted":date,"hiring":job}})

    k+=1
  i+=1

df = pd.DataFrame.from_dict(posts, orient='index')
print(df)

for i in range (0, len(job_titles)):
  places = GeoText(job_titles[i])  
  print(places.cities)
