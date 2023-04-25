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