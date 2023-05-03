#!/usr/bin/env python

import requests
import pandas as pd
from os import path 
from datetime import datetime
import sys
import getopt
import pathlib
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

HTML_EXTENSION=".html.gld"
TS_FORMAT = "%Y%m%d%H%M%S" #20220107050337

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
   print("-d, --directory D:       Read all files in the directory as ism reports")
   print("    --pmi M:             Month (Jan-Dec) to apply the default pmi on")
   print("    --smi M:             Month (Jan-Dec) to apply the default smi on")
   print("-h, --help:              Shows help and exit")
   
class ism():
    def __init__(self):
        pass

    def read_csv(self, file: str='fields.csv', separator: str =',') -> pd.DataFrame:
       if not path.isfile(file):
          return pd.DataFrame()

       return pd.read_csv(file, sep=separator)

    def read_file(self, file: str) -> str:
       """Extracts text from a local HTLM-like file. Not plain text. 

       Args:
           file (str): The file we want to extract text from.

       Returns:
           str: The string containing all the text in the HTML-like file.
       """
       if not path.isfile(file):
          return ""
       with open(file, "r", encoding='utf8') as f:
            web = f.read()
            return web
       
    def read_web(self, url: str, selenium: bool = False) -> str:
       """Extracts text from a webpage. 

       Args:
           url (str): The webpage we want to extract text from.
           selenium (bool, optional): If true, using selenium to 
           move the cursor and agree the TOS. If false, then use
           fast web scrapping to extract text from web. Defaults to False.

       Returns:
           str: The string containing all the text in the web.
       """
       try:
          if not selenium:
            r = requests.get(url)
            if r.status_code != 200:
              print('response error: '+str(r.status_code))
              return ""
            else:
               return r.text
          else:
            service = ChromeService(executable_path=ChromeDriverManager().install())
            options = Options()
            options.add_argument('user-agent=fake-useragent')
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            driver.execute_script("arguments[0].click();", WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Agree']"))))
            html = driver.find_element(by=By.TAG_NAME, value= "body").get_attribute('innerHTML')
            driver.quit()
            return html
       except Exception as e:
          print(str(e))
          return ""
   
    def find_match(self, text, tags, offset, categories) -> dict:
       """Given a set of tags and offsets, this function finds
       relevant text enclosed within those tags. 

       Args:
           text (string): Text to find matches in.
           tags ([string]): Tags delimiting each relevant field.
           offset ([int]): Offset to apply to tags to delimit relevant fields.
           categories ([string]): List of categories of the report.

       Returns:
           {string:string}: For each category, the relevant text containing ism sentiment.
       """
       d = {}
       if categories is not None and len(categories)!=len(tags):
         print('indexes provided differ from tags length')
         return {}

       t = [(tags[i],categories[i],offset[i]) if categories[i] != None else 
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
         if len(p)>1:
            d[tag[1]] = p[1].get_text()
         else:
            d[tag[1]] = soup.get_text()
       return d
         
    def score(self, categorized_text:dict, industries: list, multiplicator: dict, from_mark: str=':', to_mark: str='.') -> dict:
       """Given a categorized text, this function gives a sentiment 
       score per industry and per category. 

       Args:
           categorized_text (dict): For each category (key), the value is a string with an industry breakdown. 
           industries (list): List of industries to be found in the breakdown of categorized_text.
           multiplicator (dict): For each category (key), the value is a weight to apply. Can be negative.
           from_mark (str, optional): Character from where industry breakdown starts within a categorized text. Defaults to ':'.
           to_mark (str, optional): Character where industry breakdown ends within a categorized text. Defaults to '.'.

       Returns:
           dict: For each industry (key), another dictionary as a value where keys are categories and values the score.
       """
       d = {inds:{} for inds in industries}
       for k,v in categorized_text.items():
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
      opts, _ = getopt.getopt(argv, "u:i:t:o:svhyd:",
                              ["url=",  "industries=", "tags=", 
                               "output=", "sum", "version", "help", 
                               "accept-disclaimer","smi=", "pmi=",
                               "directory="])
    except getopt.GetoptError:
      print("Error when parsing arguments")
      print_help()
      sys.exit(2)
    sum_ = False    
    accept = False
    directory = ""
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
      elif opt in ("-d", "--directory"):
         sum_ = True
         directory = str(arg)
         if directory[-1]!='/':
            directory +='/'
         output = ".csv"
         tags_services = 'scoring-tables/servicestags.csv'
         tags_manufacturing = 'scoring-tables/manufacturingtags.csv'
         industries_services = 'scoring-tables/servicesindustries.csv'
         industries_manufacturing = 'scoring-tables/manufacturingindustries.csv'
      elif opt in ("--pmi"):
         url = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/'+str(arg).lower()
         tags = 'scoring-tables/manufacturingtags.csv'
         industries = 'scoring-tables/manufacturingindustries.csv'
         output = str(arg)+"_pmi.csv"
         sum_ = True
      elif opt in ("--smi"):
         url = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/'+str(arg).lower()
         tags = 'scoring-tables/servicestags.csv'
         industries = 'scoring-tables/servicesindustries.csv'
         output = str(arg)+"_smi.csv"
         sum_ = True
      else:
         print("Some argument was misspelled")
         print_help()
         sys.exit(2)
    if output == '':
       output = 'ism.csv'
    MyIsm = ism()
    if directory == "":
       tags_df = MyIsm.read_csv(tags)
       if len(tags_df) == 0:
         print("Could not get tags from "+tags)
         sys.exit(2)
      
       tags_df.set_index(tags_df.columns.values[0], inplace=True)
       industries_df = MyIsm.read_csv(industries, separator=';')
       if len(industries_df) == 0:
         print("Could not get industries from "+industries)
         sys.exit(2)
       webs = [(MyIsm.read_web(url, accept),url)]
    else:
       tags_services_df = MyIsm.read_csv(tags_services)
       tags_manufacturing_df = MyIsm.read_csv(tags_manufacturing)
       industries_services_df = MyIsm.read_csv(industries_services, separator=';')
       industries_manufacturing_df = MyIsm.read_csv(industries_manufacturing, separator=';')
       if len(tags_services_df) == 0 or len(tags_manufacturing_df) == 0 or len(industries_services_df) == 0 or len(industries_manufacturing_df) == 0:
         print("Problem reading tags/industries csvs")
         sys.exit(2)
       tags_services_df.set_index(tags_services_df.columns.values[0], inplace=True)
       tags_manufacturing_df.set_index(tags_manufacturing_df.columns.values[0], inplace=True)
       
       historical = pathlib.Path(directory)
       webs=[]
       for item in historical.rglob("*"+HTML_EXTENSION):
            if item.is_file():
                webs += [(MyIsm.read_file(str(item)),str(item).split('.')[0]+".csv")]
    df_services={}
    df_manufacturing={}
    for text, url in webs:   
      if text == "":
         print("Could not read url "+url)
         sys.exit(2)
      if directory=="":
         d = MyIsm.find_match(text, tags_df[tags_df.columns.values[0]].values, 
                           offset=tags_df[tags_df.columns.values[1]].values, 
                           categories = tags_df.index.values)
         mult={tags_df.index.values[i]:tags_df.iloc[i][tags_df.columns.values[2]]
                  for i in range(len(tags_df))}
         scores = MyIsm.score(d, industries_df[industries_df.columns.values[0]].values, 
                                 mult)
      else:
         if "/" in url:
            report = url.split("_")[0].split("/")[-1]
         else:
            report = url.split("_")[0].split("\\")[-1]
         if report == "services":
            d = MyIsm.find_match(text, tags_services_df[tags_services_df.columns.values[0]].values, 
                           offset=tags_services_df[tags_services_df.columns.values[1]].values, 
                           categories = tags_services_df.index.values)
            mult={tags_services_df.index.values[i]:tags_services_df.iloc[i][tags_services_df.columns.values[2]]
                  for i in range(len(tags_services_df))}
            scores = MyIsm.score(d, industries_services_df[industries_services_df.columns.values[0]].values, 
                                 mult)
         else:
            d = MyIsm.find_match(text, tags_manufacturing_df[tags_manufacturing_df.columns.values[0]].values, 
                           offset=tags_manufacturing_df[tags_manufacturing_df.columns.values[1]].values, 
                           categories = tags_manufacturing_df.index.values)
            mult={tags_manufacturing_df.index.values[i]:tags_manufacturing_df.iloc[i][tags_manufacturing_df.columns.values[2]]
                  for i in range(len(tags_manufacturing_df))}
            scores = MyIsm.score(d, industries_manufacturing_df[industries_manufacturing_df.columns.values[0]].values, 
                                 mult)
      if len(d) == 0:
         print("Did not find any match in url text "+url)
         sys.exit(2)

      
      df = pd.DataFrame.from_dict(scores, orient='index')
      if sum_:
         df = df.sum(axis=1).squeeze().sort_values()
         if directory != "":
            
            dates = datetime.strptime(str(url.split("_")[1].split(".")[0]), TS_FORMAT)
            df = pd.DataFrame(index=[dates],data=df.to_dict())
            if report == "services" and len(df_services) == 0:
               df_services = df
            elif report == "services":
               df_services = pd.concat([df_services,df])
               df_services.sort_index(inplace=True)
            elif len(df_manufacturing) == 0:
               df_manufacturing = df
            else:
               df_manufacturing = pd.concat([df_manufacturing,df])
               df_manufacturing.sort_index(inplace=True)
    if directory != "":
      if len(df_manufacturing)>0:
         df_manufacturing.name='manufacturing_scores'
         df_manufacturing.index.name = 'release_date'
         df_manufacturing.to_csv("manufacturing"+output, sep=';')
         df.cumsum().plot()
      if len(df_services)>0:
         df_services.name='services_scores'
         df_services.index.name = 'release_date'
         df_services.to_csv("services"+output, sep=';')
    else:
      df.name = 'score'
      df.index.name='industry'
      df.to_csv(output, sep=';')
if __name__ == "__main__":
    main(sys.argv[1:])
