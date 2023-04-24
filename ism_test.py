import unittest
from ism import ism
import pandas as pd
import os

SERVICES_TAGS_NAME = "scoring-tables/servicestags.csv"
MANUFACTURING_TAGS_NAME = "scoring-tables/manufacturingtags.csv"
SERVICES_INDUSTRIES_NAME = "scoring-tables/servicesindustries.csv"
MANUFACTURING_INDUSTRIES_NAME = "scoring-tables/manufacturingindustries.csv"

GOLDEN_SMIWEB_NAME = "goldens/smi.html.gld"
GOLDEN_PMIWEB_NAME = "goldens/pmi.html.gld"
GOLDEN_SMIMATCH_NAME = "goldens/smi_match.gld"
GOLDEN_PMIMATCH_NAME = "goldens/pmi_match.gld"
GOLDEN_SMISCORE_NAME = "goldens/smi_scores.gld"
GOLDEN_PMISCORE_NAME = "goldens/pmi_scores.gld"

class TestRegression(unittest.TestCase):
    def tearDown(self):
        pass
    def setUp(self):
        self.scrapper=ism()
    def test_match_smi(self):
        tags_df = self.scrapper.read_csv(SERVICES_TAGS_NAME)
        self.assertIsNotNone(tags_df, "error reading tags csv")
        tags_df.set_index(tags_df.columns.values[0], inplace=True)
        industries_df = self.scrapper.read_csv(SERVICES_INDUSTRIES_NAME, separator=';')
        self.assertIsNotNone(industries_df, "error reading industries csv")
        with open(GOLDEN_SMIWEB_NAME, "r", encoding='utf8') as f:
            web = f.read()
            self.assertGreater(len(web),0, "Web page is blank")
        d = self.scrapper.find_match(web, tags_df[tags_df.columns.values[0]].values, 
                        offset=tags_df[tags_df.columns.values[1]].values, 
                        categories = tags_df.index.values)
        self.assertIsNotNone(d,"error finding matches")
        df = pd.read_csv(GOLDEN_SMIMATCH_NAME, index_col=0).fillna("")
        golden = df.to_dict()['0']
        self.assertDictEqual(golden, d, "matches don't match")

    def test_match_pmi(self):
        tags_df = self.scrapper.read_csv(MANUFACTURING_TAGS_NAME)
        self.assertIsNotNone(tags_df, "error reading tags csv")
        tags_df.set_index(tags_df.columns.values[0], inplace=True)
        industries_df = self.scrapper.read_csv(MANUFACTURING_INDUSTRIES_NAME, separator=';')
        self.assertIsNotNone(industries_df, "error reading industries csv")
        with open(GOLDEN_PMIWEB_NAME, "r", encoding='utf8') as f:
            web = f.read()
            self.assertGreater(len(web),0, "Web page is blank")
        d = self.scrapper.find_match(web, tags_df[tags_df.columns.values[0]].values, 
                        offset=tags_df[tags_df.columns.values[1]].values, 
                        categories = tags_df.index.values)
        self.assertIsNotNone(d,"error finding matches")
        df = pd.read_csv(GOLDEN_PMIMATCH_NAME, index_col=0).fillna("")
        golden = df.to_dict()['0']
        self.assertDictEqual(golden, d, "matches don't match")

class GenerateGoldens(unittest.TestCase):
    def setUp(self):
        self.scrapper=ism()
    def test_webGolden(self):
        smi_tags_df = self.scrapper.read_csv(SERVICES_TAGS_NAME)
        self.assertIsNotNone(smi_tags_df, "error reading tags csv")
        smi_tags_df.set_index(smi_tags_df.columns.values[0], inplace=True)
        os.makedirs(os.path.dirname(GOLDEN_SMIWEB_NAME), exist_ok=True)
        smi_text = self.scrapper.read_web('https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/march', True)
        self.assertIsNotNone(smi_text, "Error downloading ism page")
        with open(GOLDEN_SMIWEB_NAME, "w", encoding='utf8') as f:
            n = f.write(smi_text)
            self.assertGreater(n,0, "Web page is blank")
        d = self.scrapper.find_match(smi_text, smi_tags_df[smi_tags_df.columns.values[0]].values, 
                        offset=smi_tags_df[smi_tags_df.columns.values[1]].values, 
                        categories = smi_tags_df.index.values)
        self.assertIsNotNone(d,"error finding matches")
        df_smi = pd.DataFrame.from_dict(d, orient="index")
        df_smi.to_csv(GOLDEN_SMIMATCH_NAME)

        pmi_tags_df = self.scrapper.read_csv(MANUFACTURING_TAGS_NAME)
        self.assertIsNotNone(pmi_tags_df, "error reading tags csv")
        pmi_tags_df.set_index(pmi_tags_df.columns.values[0], inplace=True)
        os.makedirs(os.path.dirname(GOLDEN_PMIWEB_NAME), exist_ok=True)
        pmi_text = self.scrapper.read_web('https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/march', True)
        self.assertIsNotNone(smi_text, "Error downloading ism page")
        with open(GOLDEN_PMIWEB_NAME, "w", encoding='utf8') as f:
            n = f.write(pmi_text)
            self.assertGreater(n,0, "Web page is blank")
        d = self.scrapper.find_match(pmi_text, pmi_tags_df[pmi_tags_df.columns.values[0]].values, 
                        offset=pmi_tags_df[pmi_tags_df.columns.values[1]].values, 
                        categories = pmi_tags_df.index.values)
        self.assertIsNotNone(d,"error finding matches")
        df_pmi = pd.DataFrame.from_dict(d, orient="index")
        df_pmi.to_csv(GOLDEN_PMIMATCH_NAME)

if __name__ == '__main__':
    unittest.main()