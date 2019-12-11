import pandas as pd
import random
import numpy as np
import string
import statistics
s = pd.read_csv('./output-abbr.csv')
# cities = s["location"].tolist()
fd = pd.DataFrame(s)
uniqueCities = fd["abbr"].unique()
d = {}
med = []
print(uniqueCities)
for city in uniqueCities:
  rows = fd.loc[fd["abbr"] == city]
  avg = 0
  num = 1
  abbr = ""
  for i in range(len(rows["total_funding"])):
    x = fd.loc[fd["post_title"] == list(rows["post_title"])[i], "total_funding"].values[0]
    # print(x)
    abbr = fd.loc[fd["post_title"] == list(rows["post_title"])[i], "abbr"].values[0]
    if(abbr == "IA"):
      print(x,abbr)
    avg += x
    num += 1
    med.append(x)
  # print(f"on {abbr}")
  v = statistics.median(med)
  avg = avg/num
  d.update({abbr:{"avg":avg,"med":v}})
#   if(abbr == 'IA'):
#   else:
#     d.update({abbr:{"avg":avg,"med":v}})
  avg = []
  median = []
  for row in fd[abbr]:
    avg.append(d.get(abbr).get("avg"))
    median.append(d.get(abbr).get("med"))

# print(avg, median)

  #
  #     print(city, len(rows))
  #     latstdev = .01*(max(rows["lat"])-min(rows["lat"]))
  #     longstdev = .01*(max(rows["long"])-min(rows["long"]))
  #     latjitter = rows["lat"] + np.random.randn(len(rows["lat"])) * latstdev
  #     longjitter = rows["long"] + np.random.randn(len(rows["long"])) * longstdev
  #     for i in range(len(rows["lat"])):
  #         b = fd.loc[fd["post_title"] == list(rows["post_title"])[i], "has_addy"].values
  # #         print(b[0])
  #         if not b[0]:
  #             fd.loc[fd["post_title"] == list(rows["post_title"])[i], "lat"] = list(latjitter)[i]
  #             fd.loc[fd["post_title"] == list(rows["post_title"])[i], "long"] = list(longjitter)[i]
