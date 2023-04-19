import unittest
from ism import ism
import os

GOLDEN_WEB_NAME = "goldens/web.html.gld"

class TestRegression(unittest.TestCase):
    def tearDown(self):
        pass
    def setUp(self):
        self.scrapper=ism()
    def test_match(self):
        tags_df = self.scrapper.read_csv("scoring-tables/servicestags.csv")
        self.assertIsNotNone(tags_df, "error reading tags csv")
        tags_df.set_index(tags_df.columns.values[0], inplace=True)
        industries_df = self.scrapper.read_csv("scoring-tables/servicesindustries.csv", separator=';')
        self.assertIsNotNone(industries_df, "error reading industries csv")
        with open(GOLDEN_WEB_NAME, "r") as f:
            web = f.read()
            self.assertGreater(len(web),0, "Web page is blank")
        d = self.scrapper.find_match(web, tags_df[tags_df.columns.values[0]].values, 
                        offset=tags_df[tags_df.columns.values[1]].values, 
                        indexes = tags_df.index.values)
        self.assertIsNotNone(d,"error finding matches")

class GenerateGoldens(unittest.TestCase):
    def setUp(self):
        self.scrapper=ism()
    def test_goldens(self):
        os.makedirs(os.path.dirname(GOLDEN_WEB_NAME), exist_ok=True)
        web = self.scrapper.read_web('https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/march', True)
        self.assertIsNotNone(web, "Error downloading ism page")
        with open(GOLDEN_WEB_NAME, "w") as f:
            n = f.write(web)
            self.assertGreater(n,0, "Web page is blank")
if __name__ == '__main__':
    unittest.main()