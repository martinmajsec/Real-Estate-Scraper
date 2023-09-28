# import necessary libraries
from bs4 import BeautifulSoup
import requests
import re


  
# function to extract html document from given url
def getHTMLdocument(url):
    """Function to extract html document from given URL

    Paramters
    ---------
    url: str
        The URL to extract text from

    Returns
    -------
    str
        text in JSON format
    """
      
    # request for HTML document of given url
    response = requests.get(url)
      
    # response will be provided in JSON format
    return response.text

  
url_to_scrape = ""
# maximum array length
MAXN = 2000
# very big number
INF = 1e9
# holds no of pages where results are listed, on redfin it's always <= 9
pageNo = 1
# total price to calculate average
priceCnt = 0
# number of properties
propertyNo = 0
# beds[i] holds how many properties have i bedrooms
beds = [0] * MAXN
# baths[i] holds how many properties have i bathrooms
baths = [0] * MAXN
# total size to calculate average
sqftCnt = 0
# maximum amount of beds, used to display stats
maxBeds = 0
# maximum amount of baths, used to display stats
maxBaths = 0
minPrice = INF
minSize = INF
noSqft = 0
noBeds = 0
noBaths = 0
# keeps track of visited property addresses to avoid fetching the same results multiple times
visited = set()
# property object is modeled as a tuple (myPriceArr[i], myBedsMin[i], myBedsMax[i], myBathsMin[i], myBathsMax[i], mySizeMin[i], myLocation[i], links[i])
# in case the stat (no of baths, beds, or property size) is an interval, values in min and max are different; otherwise, they are the same
myBedsMin = [0] * MAXN
myBedsMax = [0] * MAXN
myBathsMin = [0] * MAXN
myBathsMax = [0] * MAXN
mySizeMin = [0] * MAXN
mySizeMax = [0] * MAXN
myPriceArr = [0] * MAXN
links = [""] * MAXN
# stores property address
myLocation = [""] * MAXN
# stores price string so output is formated as is originally on site
priceString = [""] * MAXN
# stores if property at [i] had an interval for any of the stats. if so, the property is skipped in getNextBest as the listing contains multiple offers. the stats are still included in general stats to give a better feel for the market
interval = [0] * MAXN
# keeps track of properties fetched by getNextBest()
visitedInNextBest = [0] * MAXN
# stores whether user wants to view properties for sale or for rental
buyrent = ""


# O(n) search, MAXN is small 
def getNextBest():
    """Gets index of next best offer (lowest price/sq.ft.)

    Returns
    -------
    int
        The index corresponding to the property
    """
    minOffer = INF + 0.0
    bestInd = -1
    for i in range(propertyNo):
        # skip if any of the stats is an interval or if this property was already chosen
        if (interval[i] == 1 or visitedInNextBest[i] == 1):
            continue
        # skip if the price is still at default value
        if (mySizeMin[i] == 0 or mySizeMax[i] == 0):
            continue
        assert(mySizeMin[i] == mySizeMax[i])
        curr =  myPriceArr[i] / mySizeMin[i]
        
        if (curr < minOffer):
#            print(curr, minOffer)
            minOffer = curr
            bestInd = i
#    print("best offer is", minOffer)
    visitedInNextBest[bestInd] = 1
    return bestInd

def is_link(tag):
    '''Returns True for tags that are links'''
    if (tag.find("tel") != -1): # phone number
        return False
    return True

# updates beds, baths and sqftCnt according to ind
def fill(ind, val):
    """Updates internal stat arrays

    Parameters
    ----------
    ind: int
        Index of the given stat. Modulo 3 is checked as each listing contains 3 stats.

    val: int
        Value of the stat - no of bedrooms/bathrooms or property size

    Returns
    -------
    None
        
    """
    try:
        global beds, baths, maxBeds, maxBaths, sqftCnt, minSize, noSqft, noBeds, noBaths
        # stats in order are no of bedrooms, no of bathrooms, property size
        if (ind % 3 == 0):
            beds[val] += 1
            noBeds += 1
            if (val > maxBeds):
                maxBeds = val
        if (ind % 3 == 1):
            baths[val] += 1
            noBaths += 1
            if (val > maxBaths):
                maxBaths = val
        if (ind % 3 == 2):
            sqftCnt += val / 2
            noSqft += 1
            if (val < minSize and val != 0):
                minSize = val / 2

    except:
        print("error with", ind, val)

def formatValues(x, y):
    """Takes two values, and only returns one if they are the same. Otherwise, returns the values separated by - sign. If any of the values can be cast to int, they are.

    Parameters
    ----------
    x: int or str
    y: int or str

    Returns
    -------
    str
        The formatted string

    """
    if (x == int(x)):
        x = int(x)
    if (y == int(y)):
        y = int(y)
    if (x == y):
        return x
    else:
        return str(x) + "-" + str(y)
        

def getNeighborhood():
    """ Prompts the user to input a substring of a neighborhood's name. Searches Redfins's sitemaps to locate the listings in that neighborhood

    Returns
    -------
    None

    """
    global url_to_scrape
#    print("getting neighborhood")
    stateSitemap = "https://www.redfin.com/sitemap_com_neighborhoods.xml" # link to Redfin's sitemaps for neighborhoods
    stateLink = ""
    while(True):
        myState = input("Which state? Format is XX e.g. CA\n").strip().upper()
        if (len(myState) != 2):
            print("Wrong format. Enter the state's full name")
            continue
        #print(myState)
        sitemapXML = getHTMLdocument(stateSitemap)
        soup = BeautifulSoup(sitemapXML, 'xml')
        foundFlag = 0
        #print("soup is ", soup)
        for state in soup.find_all("loc"):
            #print("|", state.text, "|")
            ind = state.text.find(myState)
            if (ind != -1): # located substring in an existing sitemap
                foundFlag += 1
                stateLink = state.text
            
        if (foundFlag == 1):
#            print("found link", stateLink)
            break
        elif (foundFlag > 1):
            # this should be dead code
            print("Multiple candidates. This should be dead code")
            exit(0)
            
        else:
            print("Didn't find state ", myState, ". Try again", sep = '')
            continue
    
    assert stateLink != "" 
    # link was found

    nbXML = getHTMLdocument(stateLink)
    nbSoup = BeautifulSoup(nbXML, 'xml')
    nbLink = ""
    cnt = 0
   
    while(True):
        cnt += 1
        picked = 0
        myNb = input("Which neighborhood? space separated e.g. Santa Barbara\n")
        myNb = myNb.strip().lower().replace(" ", "-")
        for currNb in nbSoup.find_all("loc"):
            #print("|", currNb.text, "|")
            ind = currNb.text.lower().find(myNb)
            if (ind != -1): # located neihborhood in the corresponding state's sitemap that contains all neighborhoods
                #foundNbFlag += 1
                nbLink = currNb.text
                sp = nbLink.split("/")
                foundCity = sp[len(sp)-2].replace("-", " ")
                foundNb = sp[len(sp)-1].replace("-", " ")
                print("found", foundCity, foundNb)
                yesno = input("choose this? yes/no\n").lower().strip()
                if (yesno == "yes"):
                    picked = 1
                    break
                
                #print(currNb.text)
                #break

        if (picked == 1):
            break
        else:
            print("Didn't find neighborhood ", myNb.replace(" ", "-"), ". Try again", sep = '')
            continue   
    assert nbLink != ""
    url_to_scrape = nbLink

# main starts here

getNeighborhood()


print("buy/rent?")

# prompt the user until the input is correct
while(True):
    buyrent = input().strip().lower()

    if (buyrent == "rent"):
        buyrent = "/apartments-for-rent"
        url_to_scrape += buyrent
    elif (buyrent == "buy"):
        buyrent = ""
    else:
        print("wrong input, enter buy or rent")
        continue
    break


# print("scraping", url_to_scrape)
html_document = getHTMLdocument(url_to_scrape)
soup = BeautifulSoup(html_document, 'html.parser')

# print(url_to_scrape)

# gets number of pages
for pages in soup.find_all('a', {'class' : 'clickable goToPage'}):
#    print(pages.text)
    if (int(pages.text) > pageNo):
        pageNo = int(pages.text) 
print("found", pageNo, "pages")

pom = 0
bigIndex = 0

for i in range(1,pageNo+1):
    moreResults = url_to_scrape + "/page-" + str(i)
    html_document = getHTMLdocument(moreResults)
    print("reading", moreResults)
    soup = BeautifulSoup(html_document, 'html.parser')
    # checks whether site was visited, skips if it was
    continueFlag = 1

    myInd = bigIndex
    for name in soup.find_all('div', 
                      {'class' : 'link-and-anchor'}):
        #print(name.text)
        if ((name.text in visited) == False):
            continueFlag = 0
            visited.add(name.text)
#            print(name.text)
            myLocation[myInd] = name.text
#            print("already visited", name.text, "size of set is", len(visited))

        myInd += 1
    if (continueFlag == 1):
        print("cont'd")
        continue

    myInd = bigIndex - 1
    # gets prices
    for price in soup.find_all('span', 
                      {'class' : 'homecardV2Price'}):
        myInd += 1
        priceString[myInd] = price.text
        # parse the price
        try:
            pomStr = price.text.split("/mo")[0].strip()
            if (pomStr.lower() == "unknown"):
                continue
            pomStr = pomStr[1:len(pomStr)].replace(",","")
            pomStr = pomStr.replace("+","")

        except:
            print("exception skip", pomStr)
            # note: price is skipped but other stats from that property are still added to general stats
            continue
            
        myPrice = 0
        if (pomStr.strip() != ""): 
            myPrice = int(pomStr)
        priceCnt += myPrice
        if (myPrice < minPrice and myPrice != 0):
            minPrice = myPrice
        propertyNo+=1
        myPriceArr[myInd] = myPrice
#        print(myPrice)

    # store links to property listings
    myInd = bigIndex - 1
    for x in soup.find_all('div', {'class' : 'bottomV2'}):
        myInd += 1
        for y in x.find_all("a"):
            curr = y.get('href')
            if (is_link(curr)):
#                print(curr)
                links[myInd] = "redfin.com" + curr

    
    myInd = bigIndex - 1
    # gets stats
    for stat in soup.find_all('div', {'class' : 'stats'}):   
        myInd += 1
        # print(stat.text)
        try:
            splStr = stat.text.split(" ")[0].replace(",","")
        except:
#            print("except skip")
#            input()
            continue
        if (splStr.replace("—","0 ") != splStr):
#            print("skip")
#            input()
            continue
#        print(splStr)
        pomInd = (myInd - bigIndex) # 3 in each listing
        # no of bedrooms and bathrooms can have .5. All values are doubled so they could be stored as ints
        if (len(splStr.split("-")) == 2): # interval
            interval[bigIndex + pomInd // 3] = 1
#            print("splitting", splStr, "ind is", myInd)
#            input()
            x = int(float(splStr.split("-")[0]) * 2)
            y = int(float(splStr.split("-")[1]) * 2)
            for j in range(x, y+1):
                fill(pomInd, j)
        else: # single value
            try:
                x = int(float(splStr)*2)
                y = x # if value is not an interval, min and max are the same
                fill(pomInd, x)
            except: # encountered "local rules", must be signed in to view info
                continue
        
##        print(ind // 3, ": ", x, y)
##        input()     
##        if (i != 1):
##        print("splStr", splStr, "pomInd", pomInd)
##        print("x", x, "|y", y)
##        print("writing at index", bigIndex + pomInd // 3)
##        input()
        if (pomInd % 3 == 0):
            myBedsMin[bigIndex + pomInd // 3] = x
            myBedsMax[bigIndex + pomInd // 3] = y
        if (pomInd % 3 == 1):
            myBathsMin[bigIndex + pomInd // 3] = x
            myBathsMax[bigIndex + pomInd // 3] = y
        if (pomInd % 3 == 2):
            mySizeMin[bigIndex + pomInd // 3] = x // 2
            mySizeMax[bigIndex + pomInd // 3] = y // 2
        
        
    ## uncomment to see raw data
##    for i in range(bigIndex, propertyNo):
##        print(myPriceArr[i], myBedsMin[i] / 2, myBedsMax[i] / 2, myBathsMin[i] / 2, myBathsMax[i] / 2, mySizeMin[i], mySizeMax[i], myLocation[i], links[i])
##        if (i == bigIndex - 1):
##            print("---")
##    print("positions ", bigIndex, "-", propertyNo, " are taken", sep = "")
##    input()
    bigIndex = propertyNo


print("Total", propertyNo, "properties")
print("Average property price is", priceCnt // propertyNo, "$")
print("Lowest property price is", minPrice, "$")
print("Average property size is", sqftCnt // noSqft, "sq.ft")
print("Lowest property size is", minSize, "sq.ft")

print("No of properties with n bedrooms")
for i in range(2,maxBeds+1):
    if (beds[i] == 0):
        continue
    if (i % 2 == 0):
        print(i//2, ": ", beds[i], sep = '') # to avoid printing .0
    else:
        print(i/2, ": ", beds[i], sep = '')

print("No of properties with n bathrooms")
for i in range(2,maxBaths+1):
    if (baths[i] == 0):
        continue
    if (i % 2 == 0):
        print(i//2, ": ", baths[i], sep = '') # to avoid printing .0
    else:
        print(i/2, ": ", baths[i], sep = '')

while (True):
    print("How much offers would you like? 1", propertyNo, sep = '-')
    offerNo = 0
    try:
        offerNo = int(input())
        if (offerNo > propertyNo):
            print("Requested no of offers is larger than total no of properties.")
            offerNo = propertyNo
        
    except:
        print("Please enter a number")
        continue
    print("Fetching", offerNo, "properties sorted by price per sq.ft.")
    print()
    for i in range(offerNo):
        bestInd = getNextBest()
        if (bestInd == -1):
            print("remaining properties were not shown as they have interval stats")
            break
        print("Price ", priceString[bestInd], end = ' | ', sep = '')
        print("Beds ", formatValues(myBedsMin[bestInd] / 2,myBedsMax[bestInd] / 2), end = ' | ', sep = '')
        print("Baths ", formatValues(myBathsMin[bestInd] / 2, myBathsMax[bestInd] / 2), end = ' | ', sep = '')
        print("Size ", formatValues(mySizeMin[bestInd], mySizeMax[bestInd]), end = ' | ', sep = '')
        print("Address ", myLocation[bestInd], end = ' |\n', sep = '')
        print("Link:", links[bestInd])
        print()
        
#        print("score", myPriceArr[bestInd]/mySizeMin[bestInd])
    break
    
