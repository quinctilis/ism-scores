import unittest
from ism import ism
from ism import HTML_EXTENSION, TS_FORMAT
import pandas as pd
import os
from datetime import datetime
import requests
import concurrent.futures
import pathlib
import time

SERVICES_TAGS_NAME = "scoring-tables/servicestags.csv"
MANUFACTURING_TAGS_NAME = "scoring-tables/manufacturingtags.csv"
SERVICES_INDUSTRIES_NAME = "scoring-tables/servicesindustries.csv"
MANUFACTURING_INDUSTRIES_NAME = "scoring-tables/manufacturingindustries.csv"

GOLDEN_SMIWEB_NAME = "goldens/smi"+HTML_EXTENSION
GOLDEN_PMIWEB_NAME = "goldens/pmi"+HTML_EXTENSION
GOLDEN_SMIMATCH_NAME = "goldens/smi_match.gld"
GOLDEN_PMIMATCH_NAME = "goldens/pmi_match.gld"
GOLDEN_SMISCORE_NAME = "goldens/smi_scores.gld"
GOLDEN_PMISCORE_NAME = "goldens/pmi_scores.gld"

FIRST_REPORT_AVAILABLE = "2021-01-01"
WAYBACK_URL = "https://archive.org/wayback/available?url="
ISM_URL = "https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/"
GOLDEN_HISTORICAL_NAME = "goldens/historical_dates.csv.gld"

HTML_EXTENSION=".html.gld"
HISTORICAL_DIR="historical/"
HISTORICAL_DELIMITER="_"
BRAKING=5
class TestRegression(unittest.TestCase):
    def tearDown(self):
        pass
    def setUp(self):
        self.scrapper=ism()
    def test_match_smi(self):
        tags_df = self.scrapper.read_csv(SERVICES_TAGS_NAME)
        self.assertGreater(len(tags_df), 0, "error reading tags csv")
        tags_df.set_index(tags_df.columns.values[0], inplace=True)
        with open(GOLDEN_SMIWEB_NAME, "r", encoding='utf8') as f:
            web = f.read()
            self.assertGreater(len(web),0, "Web page is blank")
        d = self.scrapper.find_match(web, tags_df[tags_df.columns.values[0]].values, 
                        offset=tags_df[tags_df.columns.values[1]].values, 
                        categories = tags_df.index.values)
        self.assertGreater(len(d), 0,"error finding matches")
        df = pd.read_csv(GOLDEN_SMIMATCH_NAME, index_col=0).fillna("")
        golden = df.to_dict()['0']
        self.assertDictEqual(golden, d, "matches don't match")

    def test_score_smi(self):
        df = pd.read_csv(GOLDEN_SMIMATCH_NAME, index_col=0).fillna("")
        smi_match = df.to_dict()['0']
        industries_df = self.scrapper.read_csv(SERVICES_INDUSTRIES_NAME, separator=';')
        self.assertGreater(len(industries_df), 0, "error reading industries csv")
        tags_df = self.scrapper.read_csv(SERVICES_TAGS_NAME)
        self.assertGreater(len(tags_df), 0, "error reading tags csv")
        tags_df.set_index(tags_df.columns.values[0], inplace=True)
        mult={tags_df.index.values[i]:tags_df.iloc[i][tags_df.columns.values[2]]
               for i in range(len(tags_df))}
        scores = self.scrapper.score(smi_match, industries_df[industries_df.columns.values[0]].values, 
                              mult)
        self.assertGreater(len(scores), 0, "error generating scores")
        df = pd.read_csv(GOLDEN_SMISCORE_NAME, index_col=0).fillna("")
        golden = df.to_dict()
        self.assertDictEqual(golden, scores, "scores don't match")

    def test_match_pmi(self):
        tags_df = self.scrapper.read_csv(MANUFACTURING_TAGS_NAME)
        self.assertGreater(len(tags_df), 0, "error reading tags csv")
        tags_df.set_index(tags_df.columns.values[0], inplace=True)
        with open(GOLDEN_PMIWEB_NAME, "r", encoding='utf8') as f:
            web = f.read()
            self.assertGreater(len(web),0, "Web page is blank")
        d = self.scrapper.find_match(web, tags_df[tags_df.columns.values[0]].values, 
                        offset=tags_df[tags_df.columns.values[1]].values, 
                        categories = tags_df.index.values)
        self.assertGreater(len(d), 0,"error finding matches")
        df = pd.read_csv(GOLDEN_PMIMATCH_NAME, index_col=0).fillna("")
        golden = df.to_dict()['0']
        self.assertDictEqual(golden, d, "matches don't match")

    def test_score_pmi(self):
        df = pd.read_csv(GOLDEN_PMIMATCH_NAME, index_col=0).fillna("")
        pmi_match = df.to_dict()['0']
        industries_df = self.scrapper.read_csv(MANUFACTURING_INDUSTRIES_NAME, separator=';')
        self.assertGreater(len(industries_df), 0, "error reading industries csv")
        tags_df = self.scrapper.read_csv(MANUFACTURING_TAGS_NAME)
        self.assertGreater(len(tags_df), 0, "error reading tags csv")
        tags_df.set_index(tags_df.columns.values[0], inplace=True)
        mult={tags_df.index.values[i]:tags_df.iloc[i][tags_df.columns.values[2]]
               for i in range(len(tags_df))}
        scores = self.scrapper.score(pmi_match, industries_df[industries_df.columns.values[0]].values, 
                              mult)
        self.assertGreater(len(scores), 0, "error generating scores")
        df = pd.read_csv(GOLDEN_PMISCORE_NAME, index_col=0).fillna("")
        golden = df.to_dict()
        self.assertDictEqual(golden, scores, "scores don't match")

    def test_readFile(self):
        manufacturing_tags_df = self.scrapper.read_csv(MANUFACTURING_TAGS_NAME)
        self.assertGreater(len(manufacturing_tags_df), 0, "error reading tags csv")
        manufacturing_tags_df.set_index(manufacturing_tags_df.columns.values[0], inplace=True)
        manufacturing_industries_df = self.scrapper.read_csv(MANUFACTURING_INDUSTRIES_NAME, separator=';')
        self.assertGreater(len(manufacturing_industries_df), 0, "error reading industries csv")

        services_tags_df = self.scrapper.read_csv(SERVICES_TAGS_NAME)
        self.assertGreater(len(services_tags_df), 0, "error reading tags csv")
        services_tags_df.set_index(services_tags_df.columns.values[0], inplace=True)
        services_industries_df = self.scrapper.read_csv(SERVICES_INDUSTRIES_NAME, separator=';')
        self.assertGreater(len(services_industries_df), 0, "error reading industries csv")

        historical = pathlib.Path(HISTORICAL_DIR)
        df_services={}
        df_manufacturing={}
        services_count = 0
        manufacturing_count = 0
        for item in historical.rglob("*"+HTML_EXTENSION):
            if item.is_file():
                web = self.scrapper.read_file(str(item))
                self.assertGreater(len(web), 0, "error reading html from file")
                report = str(item).split("_")[0].split("/")[-1]
                if report == "services":
                    d = self.scrapper.find_match(web, services_tags_df[services_tags_df.columns.values[0]].values, 
                            offset=services_tags_df[services_tags_df.columns.values[1]].values, 
                            categories = services_tags_df.index.values)
                    self.assertGreater(len(d), 0,"error finding matches")
                    mult={services_tags_df.index.values[i]:services_tags_df.iloc[i][services_tags_df.columns.values[2]]
                            for i in range(len(services_tags_df))}
                    scores = self.scrapper.score(d, services_industries_df[services_industries_df.columns.values[0]].values, 
                              mult)
                    services_count+=1
                else:
                    d = self.scrapper.find_match(web, manufacturing_tags_df[manufacturing_tags_df.columns.values[0]].values, 
                            offset=manufacturing_tags_df[manufacturing_tags_df.columns.values[1]].values, 
                            categories = manufacturing_tags_df.index.values)
                    self.assertGreater(len(d), 0,"error finding matches")
                    mult={manufacturing_tags_df.index.values[i]:manufacturing_tags_df.iloc[i][manufacturing_tags_df.columns.values[2]]
                            for i in range(len(manufacturing_tags_df))}
                    scores = self.scrapper.score(d, manufacturing_industries_df[manufacturing_industries_df.columns.values[0]].values, 
                              mult)
                    manufacturing_count+=1
                self.assertGreater(len(scores), 0, "error generating scores")
                df = pd.DataFrame.from_dict(scores, orient='index')
                s = df.sum(axis=1).squeeze().sort_values()
                dates = datetime.strptime(str(str(item).split("_")[1].split(".")[0]), TS_FORMAT)
                df = pd.DataFrame(index=[dates],data=s.to_dict())
                if report == "services" and len(df_services) == 0:
                    df_services = df
                elif report == "services":
                    df_services = pd.concat([df_services,df])
                elif len(df_manufacturing) == 0:
                    df_manufacturing = df
                else:
                    df_manufacturing = pd.concat([df_manufacturing,df])
        df_manufacturing.sort_index(inplace=True)
        df_services.sort_index(inplace=True)
        self.assertEqual(services_count, len(df_services))
        self.assertEqual(manufacturing_count, len(df_manufacturing))


class GetHistory(unittest.TestCase):
    def setUp(self):
        self.scrapper=ism()
    def _getArchivedWebDatesAndUrls(self, args):
        ts = args[0]
        report = args[1]
        time.sleep(args[2])
        date = ts.strftime("%Y%m%d")
        month =ts.strftime("%B")
        url = WAYBACK_URL+ISM_URL+report+"/"+month.lower()+"/&timestamp="+date
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200, "web ["+url+"] status code is "+str(resp.status_code))
        data = resp.json()
        self.assertGreater(len(data),0, "empty data")
        self.assertIn("archived_snapshots",data, "archived_snapshots not present in data")
        self.assertIn("closest",data["archived_snapshots"], "closest not present in data['archived_snapshots']")
        self.assertIn("available",data["archived_snapshots"]["closest"], "closest not present in data['archived_snapshots']['closest']")        
        historical_url =data["archived_snapshots"]["closest"]["url"]
        relase_dates = datetime.strptime(str(data["archived_snapshots"]["closest"]["timestamp"]), TS_FORMAT)
        return (relase_dates, historical_url)
    
    def _URL2HTML(self, args):
        url = args[0]
        output=args[1]
        text = self.scrapper.read_web(url, False)
        if text == "":
            self.scrapper.read_web(url, True)
        if text != "":
            with open(output, "w", encoding='utf8') as f:
                f.write(text)

    def test_updateISMReports(self):
        timestaps=pd.date_range(start=FIRST_REPORT_AVAILABLE, end=datetime.now(), freq='M')
        series = []
        for report in ["services","pmi"]:
            args=[(ts,report, 0 if BRAKING <= 0 else BRAKING)  for ts in timestaps]
            with concurrent.futures.ThreadPoolExecutor(max_workers=10 if BRAKING <= 0 else 1) as executor:
                res = executor.map(self._getArchivedWebDatesAndUrls, args)
            res_l = list(res)
            urls = [res[1] for res in res_l if res is not None]
            release_dates = [res[0] for res in res_l if res is not None]
            series += [pd.Series(index=release_dates, data=urls, name=report)]
            os.makedirs(HISTORICAL_DIR, exist_ok = True)
            args=[(urls[i],HISTORICAL_DIR+report+HISTORICAL_DELIMITER+release_dates[i].strftime(TS_FORMAT)+HTML_EXTENSION)  for i in range(len(urls))]
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(self._URL2HTML, args)
        df = pd.concat(series, axis=1)
        df.to_csv(GOLDEN_HISTORICAL_NAME)


class GenerateGoldens(unittest.TestCase):
    def setUp(self):
        self.scrapper=ism()
    def test_smiGolden(self):
        smi_tags_df = self.scrapper.read_csv(SERVICES_TAGS_NAME)
        self.assertGreater(len(smi_tags_df), 0, "error reading tags csv")
        smi_tags_df.set_index(smi_tags_df.columns.values[0], inplace=True)
        os.makedirs(os.path.dirname(GOLDEN_SMIWEB_NAME), exist_ok=True)
        smi_text = self.scrapper.read_web('https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/march', True)
        self.assertGreater(len(smi_text), 0, "Error downloading ism page")
        with open(GOLDEN_SMIWEB_NAME, "w", encoding='utf8') as f:
            n = f.write(smi_text)
            self.assertGreater(n,0, "Web page is blank")
        d = self.scrapper.find_match(smi_text, smi_tags_df[smi_tags_df.columns.values[0]].values, 
                        offset=smi_tags_df[smi_tags_df.columns.values[1]].values, 
                        categories = smi_tags_df.index.values)
        self.assertGreater(len(d),0,"error finding matches")
        df_smi = pd.DataFrame.from_dict(d, orient="index")
        df_smi.to_csv(GOLDEN_SMIMATCH_NAME)

        smi_industries_df = self.scrapper.read_csv(SERVICES_INDUSTRIES_NAME, separator=";")
        self.assertGreater(len(smi_industries_df),0, "error reading industries csv")
        mult={smi_tags_df.index.values[i]:smi_tags_df.iloc[i][smi_tags_df.columns.values[2]]
               for i in range(len(smi_tags_df))}
        smi_scores = self.scrapper.score(d, smi_industries_df[smi_industries_df.columns.values[0]].values, mult)
        df_smi_scores = pd.DataFrame.from_dict(smi_scores)
        df_smi_scores.to_csv(GOLDEN_SMISCORE_NAME)

    def test_pmiGolden(self):
        pmi_tags_df = self.scrapper.read_csv(MANUFACTURING_TAGS_NAME)
        self.assertGreater(len(pmi_tags_df), 0, "error reading tags csv")
        pmi_tags_df.set_index(pmi_tags_df.columns.values[0], inplace=True)
        os.makedirs(os.path.dirname(GOLDEN_PMIWEB_NAME), exist_ok=True)
        pmi_text = self.scrapper.read_web('https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/march', True)
        self.assertGreater(len(pmi_text), 0, "Error downloading ism page")
        with open(GOLDEN_PMIWEB_NAME, "w", encoding='utf8') as f:
            n = f.write(pmi_text)
            self.assertGreater(n,0, "Web page is blank")
        d = self.scrapper.find_match(pmi_text, pmi_tags_df[pmi_tags_df.columns.values[0]].values, 
                        offset=pmi_tags_df[pmi_tags_df.columns.values[1]].values, 
                        categories = pmi_tags_df.index.values)
        self.assertGreater(len(d), 0, "error finding matches")
        df_pmi = pd.DataFrame.from_dict(d, orient="index")
        df_pmi.to_csv(GOLDEN_PMIMATCH_NAME)

        pmi_industries_df = self.scrapper.read_csv(MANUFACTURING_INDUSTRIES_NAME, separator=";")
        self.assertGreater(len(pmi_industries_df), 0, "error reading industries csv")
        mult={pmi_tags_df.index.values[i]:pmi_tags_df.iloc[i][pmi_tags_df.columns.values[2]]
               for i in range(len(pmi_tags_df))}
        pmi_scores = self.scrapper.score(d, pmi_industries_df[pmi_industries_df.columns.values[0]].values, mult)
        df_pmi_scores = pd.DataFrame.from_dict(pmi_scores)
        df_pmi_scores.to_csv(GOLDEN_PMISCORE_NAME)
if __name__ == '__main__':
    unittest.main()