import os.path  # db managing libraries
import sqlite3

import requests  # api call libraries
import json
import datetime
import time

import traceback  # catching errors

import aiohttp
import asyncio

class dbManage():  # yes I know reusing my own code ;)
    def __init__(self):
        self.checkFile = os.path.exists(
            "activity.db")  # create start menu to give user option to create new db or import existing
        self.conn = sqlite3.connect("activity.db")
        if self.checkFile == True:
            print("Opened database successfully")
        else:
            self.conn.execute('''CREATE TABLE COLLECTIONS
                             (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                             COLLECTIONNAME           TEXT    NOT NULL,
                             COLLECTIONNO           TEXT    NOT NULL,
                             TOKENMINTADDRESS            TEXT     NOT NULL,
                             PRICE           REAL    NOT NULL,
                             IMAGEURL           TEXT    NOT NULL,
                             DATE           TEXT    NOT NULL,
                             SIGNATURE           TEXT    NOT NULL
                             );''')
            print("Table created successfully")

    def insertValue(self, collection, collectionNo, tokenMintAddress, price, imageUrl, date, signature):
        self.conn.execute(
            'INSERT INTO COLLECTIONS(COLLECTIONNAME, COLLECTIONNO, TOKENMINTADDRESS, PRICE, IMAGEURL, DATE, SIGNATURE) VALUES (?,?,?,?,?,?,?)',
            (collection, collectionNo, tokenMintAddress, price, imageUrl, date, signature))
        # print("Success")
        self.conn.commit()

    def insertListingValue(self, collection, fp, listingNumber, low1, low2, low3, low4, low5, avgOfLow5, avgOfLow10, avgOfLow20):
        currentDateTime = datetime.datetime.now()
        self.conn.execute(
            'INSERT INTO ' + collection + '_LISTINGS(FLOORPRICE,LISTINGSNO,LOW1,LOW2,LOW3,LOW4,LOW5,AVGOFLOW5,AVGOFLOW10,AVGOFLOW20,DATE) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (fp,listingNumber, low1, low2, low3, low4, low5, avgOfLow5, avgOfLow10, avgOfLow20,currentDateTime)
        )  # need to work out what to do if there is no low5 for the first 10 secs of me launch
        self.conn.commit()
        print("Success")

    def createNewDB(self, collection):
        self.conn.execute("CREATE TABLE " + collection + """_LISTINGS
                                     (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                     FLOORPRICE           REAL    NOT NULL,
                                     LISTINGSNO           INT    NOT NULL,
                                     LOW1          REAL,
                                     LOW2          REAL,
                                     LOW3          REAL,
                                     LOW4          REAL,
                                     LOW5          REAL,
                                     AVGOFLOW5           REAL    NOT NULL,
                                     AVGOFLOW10           REAL    NOT NULL,
                                     AVGOFLOW20           REAL    NOT NULL,
                                     DATE           TEXT    NOT NULL
                                     );""")
        print("Table created successfully")

    def checkDuplicates(self, signature):  # to not duplicate activity posts
        isDuplicate = False
        cursor = self.conn.cursor()
        cursor.execute("SELECT SIGNATURE FROM COLLECTIONS")  # REMOVED UNKNOWN DATE KEYWORD FROM STATEMENT
        rows = cursor.fetchall()
        for row in rows:
            if row[0] == signature:
                isDuplicate = True
        return isDuplicate

    def checkIfTableExists(self,collectionName):
        cursor = self.conn.cursor()
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='" + collectionName + "_LISTINGS'")
        if cursor.fetchone()[0] != 1:
            self.createNewDB(collectionName)


class APICall():
    def __init__(self):
        print("API Call Loop Active")
        self.database = dbManage()

    async def activityCall(self,collectionNames):
        print("Running Activity Call", datetime.datetime.now())
        global collectionNo
        count = 0
        activity = []
        try:
            for collection in collectionNames:
                async with aiohttp.ClientSession() as session:
                    #print(collectionNames)
                    #print(collection)
                    requestLink = f'http://api-mainnet.magiceden.dev/v2/collections/{collection}/activities?offset=0&limit=30'
                    async with session.get(requestLink) as resp:
                        parsejson = await resp.json()
                        #print(data)
                        for i in range(0, 29):
                            test = parsejson[i]["type"]
                            if test == "buyNow":
                                buyprice = parsejson[i]["price"]  # round this up
                                timeOfTransaction = datetime.datetime.fromtimestamp(parsejson[i]["blockTime"])
                                tokenMintAddress = parsejson[i]["tokenMint"]
                                signature = parsejson[i]["signature"]  # used for identifying duplicates
                                isDuplicate = self.database.checkDuplicates(signature)
                                if isDuplicate == False:
                                    try:
                                        lookupAPIAddress = "http://api-mainnet.magiceden.dev/v2/tokens/" + tokenMintAddress
                                        #print(lookupAPIAddress)
                                        lookupResponse = requests.get(lookupAPIAddress)
                                        lookupData = lookupResponse.text
                                        parseLookupData = json.loads(lookupData)
                                        collectionName = parseLookupData["name"]
                                        #print(collectionName)
                                        if collectionName[-4] == "#":  # calculate whether it is #xxx or #xxxx
                                            collectionNo = collectionName[-4:]
                                        elif collectionName[-5] == "#":
                                            collectionNo = collectionName[-5:]
                                        else:
                                            collectionNameError = True
                                            for i in range(len(collectionName)):
                                                if collectionName[i] == "#":
                                                    collectionNameError = False
                                                    break
                                            if collectionNameError == True:
                                                for i in range(len(collectionName)):
                                                    if collectionName[i] == " ":
                                                        collectionName = collectionName[:(i+1)] + "#" + collectionName[(i+1):]
                                                        break
                                                if collectionName[-2] == "#":  # calculate whether it is #xxx or #xxxx
                                                    collectionNo = collectionName[-2:]
                                                elif collectionName[-3] == "#":
                                                    collectionNo = collectionName[-3:]
                                                elif collectionName[-4] == "#":
                                                    collectionNo = collectionName[-4:]
                                                elif collectionName[-5] == "#":
                                                    collectionNo = collectionName[-5:]
                                                else:
                                                    print("Collection Name Error")
                                                    print(collectionName)
                                        #print(collectionName)
                                        image = parseLookupData["image"]
                                        #print(collection,collectionNo,buyprice)
                                        isDuplicate = self.database.checkDuplicates(signature)
                                        if isDuplicate == False:
                                            print("Inserting",collectionNo,"from",collection)
                                            self.database.insertValue(collection, collectionNo, tokenMintAddress, buyprice, image,
                                                                      timeOfTransaction, signature)
                                            activity.append(
                                                [collection, collectionNo, tokenMintAddress, buyprice, image, timeOfTransaction])
                                        else:
                                            print("2nd loop Dupe")

                                        await asyncio.sleep(5)  # to avoid timeouts
                                    except:
                                        print("API Error - Continuing in 5...")
                                        traceback.print_exc()
                                        await asyncio.sleep(5)
                                else:
                                    # print("1st loop dupe")
                                    count += 1  # prevent API errors
                                    if count == 30:
                                        print("Stalling for 1 second to prevent errors")
                                        await asyncio.sleep(1)
                                        count = 0
            print("Finished Activity Call Loop", datetime.datetime.now())
            return activity
        except Exception as e:
            print(e)
            print("Call Loop Error - Continuing in 5...")
            await asyncio.sleep(5)


    async def listingsCall(self,collectionNames):
        print("Started Listings Call Loop", datetime.datetime.now())
        messageToSend = []

        for collection in collectionNames:
            async with aiohttp.ClientSession() as session:
                offset = 0
                timerLoop = 0
                prices = []
                url = f'http://api-mainnet.magiceden.dev/v2/collections/{collection[0]}/stats'
                print(url)
                async with session.get(url) as resp:
                    response = await resp.json()
                    print(response)
                    floorPrice = response['floorPrice']
                    listedCount = response['listedCount']
                    requestNumber = listedCount // 20  # doing it this way for efficiency
                    extraRequestNumber = listedCount % 20

                if floorPrice > 1000:
                    floorPrice = floorPrice / 1000000000

                for i in range(requestNumber):
                    url = f'http://api-mainnet.magiceden.dev/v2/collections/{collection[0]}/listings?offset={offset}&limit=20'
                    async with session.get(url) as resp:
                        response = await resp.json()
                        for listing in response:
                            price = listing["price"]
                            tokenAddress = listing["tokenAddress"]
                            prices.append([price, tokenAddress])
                        offset += 20
                        timerLoop += 1
                        if timerLoop == 3:
                            # print("Stalling...")
                            await asyncio.sleep(0.2)
                            timerLoop = 0

                if extraRequestNumber != 0:
                    url = f'http://api-mainnet.magiceden.dev/v2/collections/{collection[0]}/listings?offset={offset}&limit={extraRequestNumber}'
                    async with session.get(url) as resp:
                        response = await resp.json()
                    for listing in response:
                        price = listing["price"]
                        tokenAddress = listing["tokenAddress"]
                        prices.append([price, tokenAddress])

                def takeSecond(elem):
                    return elem[0]

                #print(floorPrice, listed)
                prices.sort(key=takeSecond)
                #for i in prices:
                    #print(i[0])

            total = 0
            for i in range(0,5):
                total += prices[i][0]
            avgOfLow5 = total / 5

            total = 0
            for i in range(0, 10):
                total += prices[i][0]
            avgOfLow10 = total / 10

            total = 0
            for i in range(0, 20):
                total += prices[i][0]
            avgOfLow20 = total / 20

            self.database.checkIfTableExists(collection[0])
            self.database.insertListingValue(collection[0],floorPrice,listedCount,prices[0][0],prices[1][0],prices[2][0],prices[3][0],prices[4][0],avgOfLow5,avgOfLow10,avgOfLow20)

            if collection[1] == 0:

                # analyse data here
                # EXAMPLE ANALYSIS ALGORITHM
                cursor = self.database.conn.cursor()
                cursor.execute("SELECT FLOORPRICE,LISTINGSNO,DATE FROM " + collection[0] + "_LISTINGS;")
                rows = cursor.fetchall()

                print(len(rows))
                while True:
                    if len(rows) > 12:
                        percDifferenceOfFP = ((floorPrice / rows[-11][0]) - 1)  # 1 hr change
                        if floorPrice > 3:
                            if percDifferenceOfFP > 0.1:
                                print("Rising", (percDifferenceOfFP * 100), "% since", rows[-11][2])
                                messageToSend.append([1, percDifferenceOfFP * 100, rows[-11][2],collection[0],floorPrice,listedCount])
                                collection[1] += 1
                                break
                            elif percDifferenceOfFP < -0.1:
                                print("Dropping", (percDifferenceOfFP * 100), "% since", rows[-11][2])
                                messageToSend.append([1, percDifferenceOfFP * 100, rows[-11][2],collection[0],floorPrice,listedCount])
                                collection[1] += 1
                                break
                        else:
                            if percDifferenceOfFP > 0.3:
                                print("Rising", (percDifferenceOfFP * 100), "% since", rows[-11][2])
                                messageToSend.append([1, percDifferenceOfFP * 100, rows[-11][2],collection[0],floorPrice,listedCount])
                                collection[1] += 1
                                break
                            elif percDifferenceOfFP < -0.3:
                                print("Dropping", (percDifferenceOfFP * 100), "% since", rows[-11][2])
                                messageToSend.append([1, percDifferenceOfFP * 100, rows[-11][2],collection[0],floorPrice,listedCount])
                                collection[1] += 1
                                break

                    if collection[2] == 0:
                        if len(rows) > 285:
                            percDifferenceOfFP = ((floorPrice / rows[-284][0]) - 1)  # 1 hr change
                            if floorPrice > 3:
                                if percDifferenceOfFP > 0.1:
                                    print("Rising", (percDifferenceOfFP * 100), "% since", rows[-284][2])
                                    messageToSend.append([2, percDifferenceOfFP * 100, rows[-284][2], collection[0],floorPrice,listedCount])
                                    collection[2] += 1
                                    break
                                elif percDifferenceOfFP < -0.1:
                                    print("Dropping", (percDifferenceOfFP * 100), "% since", rows[-284][2])
                                    messageToSend.append([2, percDifferenceOfFP * 100, rows[-284][2], collection[0],floorPrice,listedCount])
                                    collection[2] += 1
                                    break
                            else:
                                if percDifferenceOfFP > 0.3:
                                    print("Rising", (percDifferenceOfFP * 100), "% since", rows[-284][2])
                                    messageToSend.append([2, percDifferenceOfFP * 100, rows[-284][2],collection[0],floorPrice,listedCount])
                                    collection[2] += 1
                                    break
                                elif percDifferenceOfFP < -0.3:
                                    print("Dropping", (percDifferenceOfFP * 100), "% since", rows[-284][2])
                                    messageToSend.append([2, percDifferenceOfFP * 100, rows[-284][2],collection[0],floorPrice,listedCount])
                                    collection[2] += 1
                                    break
                    break
        # return any notifications
        # not necessary to return any data if not required

        print("Ended Listings Call Loop", datetime.datetime.now())
        return messageToSend,collectionNames

    def verifyCollection(self,collection):
        statsLink = 'http://api-mainnet.magiceden.dev/v2/collections/' + collection + '/stats'
        request = requests.get(statsLink)
        response = request.json()
        try:
            fp = response["floorPrice"]
            return True
        except:
            return False


#call = APICall()

#collection = ["zombiecets"]

#listing = call.listingsCall(collection)