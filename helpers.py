import pandas as pd
from fullcontact import FullContactClient
from imblearn.over_sampling import SMOTENC
from urllib.request import urlopen, Request
import numpy as np
import mysql.connector
from getpass import getpass
from mysql.connector import connect
from bs4 import BeautifulSoup
import requests
import re

class individualFeatures:
    '''trigger words are words that are associated with a call to action. We are creating a list of them so that we can cout the number of trigger words a business has in their landing page. A lot of trigger words indicate multiple CTA's, this is a sign of spending too much on ads.'''
    
    def percentPaidSearch(self, percentSearch, percentPaid):
        return percentSearch * (percentPaid/100)
    
    def adSpend(self, visits, percentSocial, percentAds, percentPaidSearch):
        social = (visits * (percentSocial/100)) * 7
        display = (visits * (percentAds/100)) * 7
        paidSearch = (visits * (percentPaidSearch/100)) * 0.95
        return round(social + display + paidSearch)
    
    def percentAdTraffic(self, percentSocial, percentAds, percentPaidSearch):
        return round(percentSocial+percentAds+percentPaidSearch, 2)
    
    def nWords(self, landingPage):
        words = 0
        for lp in landingPage.split(' '):
            if lp.startswith('http') == False:
                words += 1
        return words
    
    def triggerWords(self, landingPage):
        triggerWords = ['book', 'call', 'today', 'get', 'my', 'free', 'copy', 'checklist', 
                'pdf', 'report', 'ebook', 'join', 'session', 'now', 'set', 'email',
                'free', 'list', 'attend', 'start', 'access', 'training', 'speak', 
                'expert', 'here', 'send', 'strategy', 'course', 'quote', 'newsletter']
        tw = 0
        for lp in landingPage.split(' '):
            if lp in triggerWords:
                tw += 1
        return tw
    
    def nLinks(self, landingPage):
        links = 0
        for lp in landingPage.split(' '):
            if lp.startswith('http') == True:
                links += 1
        return links
    
    
class aggregateFeatures:
    
    def estimateRevenue(self, df, key):
        fcc = FullContactClient(key)
        revenue = []
        for i in range(len(df)):
            row = df.iloc[i]
            lead = fcc.company.enrich(domain=row['lead']).json()
            try:
                if row['business model'] == 'consulting':
                    revenue.append(lead['employees'] * 15873)
                if row['business model'] == 'ecommerce':
                    revenue.append(lead['employees'] * 66666)
                if row['business model'] == 'info':
                    revenue.append(lead['employees'] * 16666)
                if row['business model'] == 'media':
                    revenue.append(lead['employees'] * 50000)
                if row['business model'] == 'restaurant':
                    revenue.append(lead['employees'] * 35714)
                if row['business model'] == 'software':
                    revenue.append(lead['employees'] * 379722)
            except:
                revenue.append(False)
        return revenue
    
    def adRevenue(self, revenue, percentAdTraffic):
        return revenue * (percentAdTraffic/100)
    
    def roas(self, adRevenue, adSpend):
        return adRevenue / adSpend
    
    def cac(self, newCustomers, adSpend):
        return adSpend / newCustomers
    
    def profit(self, revenue, adSpend, hardcosts):
        return revenue - adSpend - hardcosts
    
    def landingPageComplexity(self, links, words, triggerWords):
        return links+1 * words+1 * triggerWords+1
    
    def profitMargin(self, revenue, adSpend, hardcosts):
        af = aggregateFeatures()
        return af.profit(revenue, adSpend, hardcosts) / revenue
    
    def lpc(database='leads', table='landingpage'):
        password = input('Enter password: ')
        connection = connect(host='localhost', user='root', password=password, database=database)
        cursor = connection.cursor()
        q = 'select words, triggers, links from {};'.format(table)
        cursor.execute(q)
        results = cursor.fetchall()
        complexities = []
        for r in results:
            complexities.append(r[0]*r[1]*r[2])
        return complexities

    
class Data:
    
    def doubleUp(self, df, class_size, target_col, sm):
        yes = df.loc[df[target_col] == 1]
        no = df.loc[df[target_col] == 0]
        df = pd.concat([yes, no])
        inv = len(df) - class_size - 6
        positives = df.iloc[:class_size+6]
        negatives = df.iloc[inv:]
        posX = positives.drop([target_col], axis='columns')
        posY = positives[target_col]
        posX2, posY2 = sm.fit_resample(posX, posY)
        pos2 = posX2
        pos2[target_col] = posY2
        negX = negatives.drop([target_col], axis='columns')
        negY = negatives[target_col]
        negX2, negY2 = sm.fit_resample(negX, negY)
        neg2 = negX2
        neg2[target_col] = negY2
        return pd.concat([pos2, neg2])
    
    def getCol(self, host, user, password, database, cols):
        connection = connect(host='localhost', user='root', password='Raptor//Kona9', database='leads')
        cursor = connection.cursor()
        cursor.execute('select {} from survey;'.format(cols))
        return cursor.fetchall()

    # I need to inspect the holdup at results[54]
    def lpContent(self, headers):
        results = Data().getCol('localhost', 'root', 'Raptor//Kona9', 'leads', 'name, landingPage')
        connection = connect(host='localhost', user='root', password='Raptor//Kona9', database='leads')
        cursor = connection.cursor()
        queries = []
        for i in range(len(results)):
            print(i)
            lead = results[i][0]
            url = results[i][1]
            try:
                lp = lpCopy(url, headers) + ' ' + ctaButton(url, headers)
                lc = countLinks(url, headers)
            except:
                lp = ''
                lc = 0
            nwords, ntriggers = lpMetadata(lp)
            q = 'INSERT INTO landingpage (name, landingPage, words, triggers, links) VALUES ({}, {}, {}, {}, {});'.format(lead, url, nwords, ntriggers, lc)
            queries.append(q)
        for query in queries:
            cursor.execute(query)
        connection.commit()
        pass
 

class Scraping:
    
    def lpCopy(self, url, headers):
        req = Request(url=url, headers=headers) 
        html = urlopen(req).read()
        soup = BeautifulSoup(html, 'lxml')
        div = soup.findAll('div')
        p = soup.findAll('p')
        try:
            text = div[0].text + p[0].text
        except: 
            text = div[0].text
        text2 = text.replace('\n', '').replace('\'', '').replace(')', '').replace('(', '').lower()
        text3 = re.sub("([\(\[]).*?([\)\]])", '', text2)
        text4 = re.sub(r'\[(^)*\]', '', text3)
        text5 = text4.replace('-', '').replace('"', '').replace('!', ' ').replace('*', '').replace(':', ' ').replace('.', ' ')
        text6 = text5.replace('?', ' ')
        text7 = text6.replace('|', '').replace('/', '').replace(',', '').replace('...', '')
        text8 = text7.replace('\xa0', '').replace('“', '').replace('”', '').replace('…', '')
        return text8
    
    def ctaButton(self, url, headers):
        req = Request(url=url, headers=headers) 
        html = urlopen(req).read()
        soup = BeautifulSoup(html, 'lxml')
        span = soup.findAll('span')
        return span[2].text.lower()

    def lpMetadata(self, text):
        words = text.split(' ')
        n_trigger_words = individualFeatures().triggerWords(text)
        n_words = len(words)
        return n_words , n_trigger_words

    def countLinks(self, url, headers):
        req = Request(url=url, headers=headers) 
        html = urlopen(req).read()
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for link in soup.findAll('a', attrs={'href': re.compile("^https://")}):
            links.append(link.get('href'))
        return len(links)
    
class Math:
    
    def cubicRoot(self, x):
        return x ** (1. / 3)

connection = connect(host='localhost', user='root', password='Raptor//Kona9', database='leads')
cursor = connection.cursor()
cursor.execute('''INSERT INTO test (col1, col2) VALUES ('Cardinal', 'Stavanger');''')
print('ok')