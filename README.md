# Description
This script scrapes the ism web page to get both smi and pmi quantitative information out 
of their respective text based reports. 

## ⚠️Disclaimer
Read carefully the code before you run it to make 
sure you understand the implications of doing so. In the case of ismworld, this may be 
against its [Terms of service](https://www.ismworld.org/footer/terms-of-use/), more precisely, against:
> exploit the Service or collect any data incorporated in the Service in any automated manner through the use of bots, metaspiders, crawlers or any other automated means;

This code is intended for educational purposed only and the creator is not held liable for any 
consequences resulting from its use

## Dependencies
There should be no dependencies (external programs) to be installed. Just having python3.7+ 
and internet connection should be enough to install the program and run it.

## Installing
You can install the necessary python packages by running 
```shell
pip install -r requirements.txt
```
To make sure everything is installed properly, run
```shell
python ism.py --version
```

## Running program
Once required packages have been installed, one can safely run the script by typing:
```shell
python ism.py -y --pmi march
```
The above command should have generated a txt file named `march_pmi.txt`. Keep in mind that 
reports are released next month, so march report will be available in mid april. Ism webpage 
usually stores the two most recent reports, so in the example above, if the march report 
is available, then the february report will be available too, but the january one will not.

The output `<month>_<report>.csv` will contain a summary of the report broken down by industry.
Each industry will have a score based on the report analyzed. The more positive (negative) the 
score, the more bullish (bearish) the industry.

### How scores are generated
There are some `.csv` files in the `scoring-tables` folder accompanying the main script. 
* **servicesindustries.csv:** The list of industries that the ism uses to generate the 
smi report. A change on this list will result in failing to match what the report says about 
an specific industry and the rate assigned to it.

* **manufacturingindustries.csv:** The list of industries that ism uses to generate the pmi 
report. A change on this list will result in failing to match what the report says about 
an specific industry and the rate assigned to it.

* **servicestags.csv:** Here we define the categories in smi report. In order to find which 
category the text is referring to, we need a tag in the html defined here and an offset.
The column multiplier is the score we assign to that category, being a positive number 
positive sentiment and negative number negative. Usually in reports they express sentiments 
as _backlog of orders have increased for the manufacturing industry_. So we need to know 
if an increase in backlog of orders is positive (+1.5 multiplier for example) or negative
(a -1.5 multiplier). All the categories for any given industry are averaged up taking into 
consideration the weight on this `multiplier` column.

* **manufacturingtags.csv:** Same as `servicestags.csv` but for the pmi report.
