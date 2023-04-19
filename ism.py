#!/usr/bin/env python

import requests
import pandas as pd
from os import path 
import sys
import getopt
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def print_version():
   print ("version 0.1")

def print_help():
   print("ism.py usage")
   print("-u, --url U:             base url")
   print("-i, --industries I:      file path to read industries from")
   print("-t, --tags T:            file path to read tags from")
   print("-o, --output F:          output file to write")
   print("-s, --sum:               sum partial results and rank totals")
   print("-v, --version:           Shows version and exit")
   print("-y, --accept-disclaimer: Accept the disclaimer notice prompt")
   print("    --pmi M:             Month (Jan-Dec) to apply the default pmi on")
   print("    --smi M:             Month (Jan-Dec) to apply the default smi on")
   print("-h, --help:              Shows help and exit")
   
class ism():
    def __init__(self):
        pass

    def read_csv(self, file='fields.csv', separator=','):
       if not path.isfile(file):
          return None

       return pd.read_csv(file, sep=separator)

      
    def read_web(self, url, selenium = False):
       try:
          if not selenium:
            r = requests.get(url)
            if r.status_code != 200:
              print('response error: '+str(r.status_code))
              return None
            else:
               return r.text
          else:
            service = ChromeService(executable_path=ChromeDriverManager().install())
            options = Options()
            options.add_argument('user-agent=fake-useragent')
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            driver.execute_script("arguments[0].click();", WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Agree']"))))
            html = driver.find_element(by=By.TAG_NAME, value= "body").get_attribute('innerHTML')
            driver.quit()
            return html
       except Exception as e:
          print(str(e))
          return None
   
    def find_match(self, text, tags, offset, indexes = None):
       """Given a set of tags and offsets, this function finds
       relevant text enclosed within those tags. 

       Args:
           text (string): Text to find matches in.
           tags ([string]): Tags delimiting each relevant field.
           offset ([int]): Offset to apply to tags to delimit relevant fields.
           indexes ([int], optional): _description_. Defaults to None.

       Returns:
           [string]: List of relevant fields containing information of given parameters.
       """
       d = {}
       if indexes is not None and len(indexes)!=len(tags):
         print('indexes provided differ from tags length')
         return None

       t = [(tags[i],indexes[i],offset[i]) if indexes[i] != None else 
            (tags[i],tags[i],offset[i]) for i in range(len(tags))]
       for tag in t:
         where = text.find(tag[0])
         if where == -1:
            d[tag[1]]=''
            continue
         if tag[2]>0:
            lines = ''.join(text[where:].splitlines()[1:tag[2]+1])
         else:
            lines = ''.join(text[:where+1].splitlines()[tag[2]-1:])
         soup = BeautifulSoup(lines, 'html.parser')
         p = soup.find_all(class_='mb-3')
         if len(p)>0:
            d[tag[1]] = p[1].get_text()
         else:
            d[tag[1]] = soup.get_text()
       return d
         
    def score(self, text, industries, multiplicator, from_mark=':', to_mark='.'):
       d = {inds:{} for inds in industries}
       for k,v in text.items():
          mult = multiplicator[k]
          for industry in industries:
             from_ = v.find(from_mark)
             if from_ < 0:
                d[industry][k] = 0
                
             else:
                to_ = v.find(to_mark,from_)
                if to_ > 0:
                   relevant = v[from_:to_]
                   if industry in relevant:
                      d[industry][k] = mult
                      continue
                   to2_ = v.find(to_mark, to_+1)
                   if to2_ < 0:
                      d[industry][k] = 0
                      continue
                   relevant = v[to_:to2_]
                   if industry in relevant:
                      to3_ = v.find(to_mark, to2_+1)
                      if to3_ < 0:
                         d[industry][k] = -mult
                         continue
                      relevant = v[to2_:to3_]
                      if industry in relevant:
                         score = -mult
                      else:
                         score = 0
                      d[industry][k] = score
                      continue
                   d[industry][k] = 0
                   continue
       return d

def main(argv):
    try:
      opts, _ = getopt.getopt(argv, "u:i:t:o:svhy",
                              ["url=",  "industries=", "tags=", 
                               "output=", "sum", "version", "help", 
                               "accept-disclaimer","smi=", "pmi="])
    except getopt.GetoptError:
      print("Error when parsing arguments")
      print_help()
      sys.exit(2)
    sum_ = False    
    accept = False
    url = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/april'
    tags = 'scoring-tables/manufacturingtags.csv'
    industries = 'scoring-tables/manufacturingindustries.csv'
    output = ''
    for opt, arg in opts:
      if opt in ("-h","--help"):
         print_help()
         sys.exit()
      elif opt in ("-v", "--version"):
         print_version()
         sys.exit()
      elif opt in ("-u", "--url"):
         url = str(arg) 
      elif opt in ("-i", "--industries"):
         industries =str(arg)
      elif opt in ("-t", "--tags"):
         tags =str(arg)
      elif opt in ("-o", "--output"):
         output = str(arg)
      elif opt in ("-s", "--sum"):
         sum_ = True
      elif opt in ("-y", "--accept-disclaimer"):
         accept = True
      elif opt in ("--pmi"):
         url = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/'+str(arg).lower()
         tags = 'scoring-tables/manufacturingtags.csv'
         industries = 'scoring-tables/manufacturingindustries.csv'
         output = str(arg)+"_pmi.txt"
         sum_ = True
      elif opt in ("--smi"):
         url = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/'+str(arg).lower()
         tags = 'scoring-tables/servicestags.csv'
         industries = 'scoring-tables/servicesindustries.csv'
         output = str(arg)+"_smi.txt"
         sum_ = True
      else:
         print("Some argument was misspelled")
         print_help()
         sys.exit(2)
    if output == '':
       output = 'ism.csv'
    Myism = ism()
    tags_df = Myism.read_csv(tags)
    if tags_df is None:
       print("Could not get tags from "+tags)
       sys.exit(2)
    tags_df.set_index(tags_df.columns.values[0], inplace=True)

    industries_df = Myism.read_csv(industries, separator=';')
    if industries_df is None:
       print("Could not get industries from "+industries)
       sys.exit(2)

    web = Myism.read_web(url, accept)
    if web is None:
       print("Could not read url "+url)
       sys.exit(2)
    
    d = Myism.find_match(web, tags_df[tags_df.columns.values[0]].values, 
                        offset=tags_df[tags_df.columns.values[1]].values, 
                        indexes = tags_df.index.values)
    if d is None:
       sys.exit(2)

    mult={tags_df.index.values[i]:tags_df.iloc[i][tags_df.columns.values[2]]
               for i in range(len(tags_df))}
    scores = Myism.score(d, industries_df[industries_df.columns.values[0]].values, 
                              mult)
    df = pd.DataFrame.from_dict(scores, orient='index')
    if sum_:
       df = df.sum(axis=1).squeeze().sort_values()
       df.name = 'score'
    df.to_csv(output, sep=';')
if __name__ == "__main__":
    main(sys.argv[1:])
