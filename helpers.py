import pandas as pd
import scrapy

class individualFeatures:
    '''def __init__(self, percentSocial, percentAds):
        self.percentSocial = percentSocial
        self.percentAds = percentAds'''
    
    def percentPaidSearch(self, percentSearch, percentPaid):
        return percentSearch * (percentPaid/100)
    
    def adSpend(self, visits, percentSocial, percentAds, percentPaidSearch):
        social = (visits * (percentSocial/100)) * 7
        display = (visits * (percentAds/100)) * 7
        paidSearch = (visits * (percentPaidSearch/100)) * 0.95
        return round(social + display + paidSearch)
    
    def percentAdTraffic(self, percentSocial, percentAds, percentPaidSearch):
        return round(percentSocial+percentAds+percentPaidSearch, 2)
    
class aggregateFeatures:
    triggerWords = ['book', 'call', 'today', 'get', 'my', 'free', 'copy', 'checklist', 
                'pdf', 'report', 'ebook', 'join', 'session', 'now', 'set', 'email',
                'free', 'list', 'attend', 'start', 'access', 'training', 'speak', 
                'expert', 'here']
    '''trigger words are words that are associated with a call to action. We are creating a list of them so that we can cout the number of trigger words a business has in their landing page. A lot of trigger words indicate multiple CTA's, this is a sign of spending too much on ads.'''
    
    def adRevenue(self, revenue, percentAdTraffic):
        return revenue * (percentAdTraffic/100)
    
    def roas(self, adRevenue, adSpend):
        return adRevenue - adSpend
    
    def cac(self, newCustomers, adSpend):
        return newCustomers / adSpend
    
    def profit(self, revenue, adSpend, hardcosts):
        return revenue - adSpend - hardcosts
    
    def landingPageComplexity(self, links, words):
        tw = 0
        for w in words:
            if w in self.triggerWords:
                tw += 1
        return tw * len(links) * len(words)
    
    def profitMargin(self, revenue, adSpend, hardcosts):
        af = aggregateFeatures()
        return af.profit(revenue, adSpend, hardcosts) / revenue