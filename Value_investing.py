# Let's import some dependences
import pandas as pd
import concurrent.futures as cf
from yahoofinancials import YahooFinancials

import re
import ast
import time
import requests
import bs4 as bs
from bs4 import BeautifulSoup

# I use Wikipedia to see which companies are in the S&P500 index
sp500 = 'http://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

# I create an empty list fo fill in with data
tickers = []

for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text      
        tickers.append(ticker)
print(tickers)


# I create three dictionary to use for storing information

balanceSheet = {}
incomeStatement = {}
cashStatement = {}

# Let's iterate trough ticker in list of tickers

def retrieve_stock_data(ticker):
    try:
        print(ticker)
        start = time.time()
        yahoo_financials = YahooFinancials(ticker)
        balance_sheet_data = yahoo_financials.get_financial_stmts('annual', 'balance')
        income_statement_data = yahoo_financials.get_financial_stmts('annual', 'income') 
        cash_statement_data = yahoo_financials.get_financial_stmts('annual', 'cash')

        balanceSheet[ticker] = balance_sheet_data['balanceSheetHistory'][ticker] 
        incomeStatement[ticker] = income_statement_data['incomeStatementHistory'][ticker]
        cashStatement[ticker] = cash_statement_data['cashflowStatementHistory'][ticker]
    except:
        print('error with retrieving stock data')

        
# I created a function for ROE and EPS growth

roe_dict, epsg_dict = {}, {}
count_missing, count_cond, count_eps_0 = 0, 0, 0
for (keyB, valB), (keyI, valI) in zip(balanceSheet.items(), incomeStatement.items()):
    try:
        if keyB == keyI:
            yearsI = [k for year in valI for k, v in year.items()]
            yearsB = [k for year in valB for k, v in year.items()]
            if yearsI == yearsB:
                count_cond += 1
                equity = [v['totalStockholderEquity'] for year in valB for k, v in year.items()]
                commonStock = [v['commonStock'] for year in valB for k, v in year.items()]

                profit = [v['grossProfit'] for year in valI for k, v in year.items()]
                revenue = [v['totalRevenue'] for year in valI for k, v in year.items()]
                netIncome = [v['netIncome'] for year in valI for k, v in year.items()]

                roe = [round(netin/equity*100,2) for netin, equity in zip(netIncome, equity)]
                roe_dict[keyB] = (round(sum(roe)/len(roe),2), roe)

                eps = [round(earn/stono,2) for earn, stono in zip(profit, commonStock)]
                
                try:
                    epsg = []
                    for ep in range(len(eps)):
                        if ep == 0:
                            continue
                        elif ep == 1:
                            epsg.append(round(100*((eps[ep-1]/eps[ep])-1),2))
                        elif ep == 2:
                            epsg.append(round(100*((eps[ep-2]/eps[ep])**(1/2)-1),2))
                            epsg.append(round(100*((eps[ep-1]/eps[ep])-1),2))
                        elif ep == 3:
                            epsg.append(round(100*((eps[ep-3]/eps[ep])**(1/3)-1),2))
                            epsg.append(round(100*((eps[ep-1]/eps[ep])-1),2))
                        else:
                            print('More than 4 years of FY data')
                        
                    epsg_dict[keyB] = (round(sum(epsg)/len(epsg),2), epsg)
                except:
#                     print(keyB, 'eps contains 0')
                    count_eps_0 += 1
                    epsg_dict[keyB] = (0, eps)

    except:
#         print(keyB, 'data missing')
        count_missing += 1

print('Yearly data avail',count_cond, 'out of', len(balanceSheet))
print('Some key data missing', count_missing, 'out of', len(balanceSheet))
print('EPS Growth NaN', count_eps_0, 'out of', len(balanceSheet))


# Let's create the conditions on this 2 dictionary
ROE_req = 10 # ROE above 10% 
EPSG_req = 10 # EPS growth above 10%

print('-'*50, 'RETURN ON EQUITY','-'*50)
# Let's subsection the ROE by getting the first item  which is the requirement ROE 
roe_crit = {k:v for (k,v) in roe_dict.items() if v[0] >= ROE_req and sum(n < 0 for n in v[1])==0}
print(f'The number of companies have a ROE greater than 10% are: ' + str(len(roe_crit)))
#print(roe_crit)

print('-'*50, 'EARNINGS PER SHARE GROWTH','-'*50)
eps_crit = {k:v for (k,v) in epsg_dict.items() if v[0] >= EPSG_req and sum(n < 0 for n in v[1])==0}
print(f'The number of companies have a EPS growth greater than 10% are: ' + str(len(eps_crit)))
#print(eps_crit)

print('-'*50, 'ROE & EPS Growth Critera','-'*50)
both = [key1 for key1 in roe_crit.keys() for key2 in eps_crit.keys() if key2==key1]
print(f'The number of companies have both criteria are: ' + str(len(both)))
print(both)







