from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from fpdf import FPDF
import re

#for browser run
import subprocess 
import webbrowser
import sys
import urllib # for url encoding

# Needed:
# BeautifulSoup
# pip install urlopen
# pip install lxml
# pip install fpdf
# DejaVuSansCondensed.ttf font file in program directory

# Working 29.09.2019
# The program may need modifications if the page changes

#to do
# fix bug if only one category page
# maybe a table view?

# add proxy
# multithreading (not necessary becouse it can look like flood)


#Settings
# products per page 15/30/45/60 (recommended 60 for best performance)
sett_productsPerPage = 60
# start page number (recommended start from 0),
sett_startPageNumber = 0
# category eg. Muzyka = 33,  Kolekcje własne = 46, Gry planszowe = 376301, 0 = no category
sett_category = 376301
# use to limit results
limitResults = 500


#data containier
dataList = []

#prepare PDF
pdf = FPDF()
pdf.add_page()

#DejaVu Unicode font (uses UTF-8)
pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
pdf.set_font('DejaVu', '', 10)


#open top products in browser function
def openBest(data, number):
    for i in range(0, number):
        url = "https://www.empik.com/szukaj/produkt?q="
        url += data[i][0]
        url += "&qtype=basicForm&ac=true"
        print(url)
        
        if sys.platform == 'darwin':    # in case of OS X
            subprocess.Popen(['open', url])
        else:
            webbrowser.open_new_tab(url)


#search url constructor
def searchUrl(data):
        url = "https://www.empik.com/szukaj/produkt?q="
        url += urllib.parse.quote_plus(data, safe='', encoding='utf-8', errors=None)
        url += "&qtype=basicForm&ac=true"
        return url
        
            
#url constructor
def urlBuilder( productPerPage, pageNumber, Category ):
    url = "https://www.empik.com/promocje?"

    if Category != 0:
        url += "searchCategory=" + str(Category)

    url += "&hideUnavailable=true"
    url += "&start=" + str((pageNumber*productPerPage)+1)
    url += "&resultsPP=" + str(productPerPage)
    url += "&qtype=facetForm"
    return url

# url
sett_url = urlBuilder(sett_productsPerPage, sett_startPageNumber, sett_category)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
reg_url = sett_url
req = Request(url=reg_url, headers=headers) 
html = urlopen(req)
bsObj = BeautifulSoup(html.read(), "lxml");

#counting pages
pageNumbers = bsObj.find("div", "pagination").findAll("a")
aTagNumber = len(pageNumbers)-2

priceList = bsObj.findAll("div", "price ta-price-tile")
#titleList = bsObj.findAll("strong", "ta-product-title")

extractedPagesAmount = int(pageNumbers[aTagNumber].get_text())
productsOnPage = len(priceList)
print("First link: ", sett_url)
print("Category number: ", sett_category)
print("Number of pages: ", extractedPagesAmount)
print("Number of products of each page: ", productsOnPage)
print("Approximate number of expected products: ~", extractedPagesAmount*productsOnPage)

#---------------------
print("Fetching ", extractedPagesAmount, " pages of data")

count = 0
for j in range(0, extractedPagesAmount):
    
    reg_url = urlBuilder(sett_productsPerPage, j, sett_category)
    req = Request(url=reg_url, headers=headers) 
    html = urlopen(req)
    bsObj = BeautifulSoup(html.read(), "lxml");

    priceList = bsObj.findAll("div", "price ta-price-tile")
    titleList = bsObj.findAll("strong", "ta-product-title")

    productsOnPage = len(priceList)
    
    #  singe item in loop
    for i in range(0, productsOnPage):
        extractedPrice = priceList[i].get_text()
        extractedTitle = (titleList[i].get_text()).strip()
        count += 1

        prices =  re.findall("\d+\,\d+", extractedPrice)
        
        prices[0] = float(prices[0].replace(',','.'))

        if len(prices) == 2:
            prices[1] = float(prices[1].replace(',','.'))
            percentdiff = round(((prices[1]*100)/prices[0])-100,2)
            data = [extractedTitle, percentdiff, prices[0], prices[1]]
        else:
            # when no second price
            percentdiff = 0
            data = [extractedTitle, percentdiff, prices[0], prices[0]]

        dataList.append(data)

        #to Debug
        #print("-", percentdiff, end="% ")
        #print(prices, end=" ")
        #print(extractedTitle)
    #---------------------

    print("[",j+1,"/",extractedPagesAmount, "] - page done")


#display collected data

# function to return the second element 
def returnSecondElement(val): 
    return val[1]  

limitCount = 0
dataList.sort(key = returnSecondElement, reverse = True) #sort

print("Listing")
print("Order: price diff [%], old price [PLN], new price [PLN], product")

pdf.cell(0, 10, txt="Results", ln=1, align="C")
pdf.cell(0, 10, txt="Order: price diff [%], old price [PLN], new price [PLN], product", ln=1, align="L")

for i in dataList:
    limitCount += 1

    text = str(i[1]) + "%\t" + str(i[2]) + "\t" + str(i[3]) + "\t" + str(i[0])
    print(text)
    
    # can't use "\t" in PDF
    pdfText = str(i[1]) + "%    " + str(i[2]) + "    " + str(i[3]) + "    " + i[0]

    
    pdf.cell(0, 10, txt=pdfText, ln=1, align="L", fill=False, link=searchUrl(i[0]))

    
    if limitCount >= limitResults:
        break;

print("Total scanned products: ", count)
print("Listed only: ", limitResults, " best of % difference.")
print("Please generate PDF file to see whole list.")

print("Do you want to generate PDF file? [yes/no]")
choice = input()

if choice == "yes":
    pdf.output("output.pdf")
else:
    print("Thanks for using")

print("Do you want to see best products in browser? [yes/no]")
choice = input()

if choice == "yes":
    howManyOpen = input("How many? (number): ")
    howManyOpen = int(howManyOpen)
    openBest(dataList, howManyOpen)
else:
    print("Thanks for using")


