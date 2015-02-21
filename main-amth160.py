# -*- coding: utf-8 -*-
import re
import requests
import json
import urllib
from pymongo import MongoClient
from secrets import CRUNCHBASE_API_KEY
from colors import bcolors
from decimal import *

# NOTES
# obj = json.loads(json_string) 
# print bcolors.HEADER + "Warning: No active frommets remain. Continue?" + bcolors.ENDC

# List of top VC firms
vc_firms = ["Angel Academe",
            "Accel",
            "KPCB",
            "Sequoia",
            "NEA",
            "Andreessen Horowitz",
            "Lightspeed",
            "Benchmark",
            "Bessemer",
            "IVP",
            "DFJ",
            "Bain Capital Ventures",
            "Union Square",
            "Greylock",
            "Khosla",
            "Shasta",
            "General Catalyst",
            "Intel capital",
            "Foundry Group",
            "First Round",
            "SV Angel",
            "Google Ventures",
            "SoftTech"]

# For CrunchBase API access, add onto HTTP request as parameter
payload = {'api_key' : CRUNCHBASE_API_KEY}
good_count = 0
bad_count = 0
bad = []

# Establish connections
client = MongoClient('mongodb://localhost:27017/')
db = client.amth160
vcs = db.vcs
companies = db.companies

def get_entity(namespace, permalink ):
    req = requests.get("http://api.crunchbase.com/v/1/%s/%s.js" \
            % (namespace, permalink), params=payload)

    if req.status_code == 200:
        print "\t\t[-] Got http://api.crunchbase.com/v/1/%s/%s.js" \
                % (namespace, permalink)
        try:
            return json.loads(req.text)
        except:
            return None
    else:
        print "\t\t[-] %s: http://api.crunchbase.com/v/1/%s/%s.js" \
                % (req.status_code, namespace, permalink)
        return None

def search(query, model):
    safe_query = urllib.quote(query)  # Make query url-safe

    print "\t\t[-] Calling http://api.crunchbase.com/v/1/search.js?query=%s" \
            % safe_query

    req = requests.get("http://api.crunchbase.com/v/1/search.js?query=%s" \
            % safe_query, params=payload)

    if req.status_code == 200:
        print "\t\t[-] Got http://api.crunchbase.com/v/1/search.js?query=%s" \
                % safe_query

        try:
            res = json.loads(req.text)  # Convert string response into Python dictionary
        except:
            print req.text
            return None


        # Find the best match from result
        permalink = None
        namespace = None
        for result in res['results']:
            if result['namespace'] == model:
                # Get permalink and namespace of top result
                permalink = result['permalink']
                namespace = result['namespace']
                break

        # No result found
        if permalink is None:
            print "\t\t[-] No results found."
            return None

        return get_entity(namespace, permalink)

    else: 
        print "\t\t[-] %s: http://api.crunchbase.com/v/1/search.js?query=%s" \
                % (req.status_code, safe_query)
        return None

def scrape_vcs():
    global vcs

    print bcolors.PINK + "[>] Running MineBase scraper with %s firms..." \
            % len(vc_firms) + bcolors.ENDC

    for vc_firm in vc_firms:    # Iterate through VC firms
        continue
        if vcs.find_one({'name':re.compile(vc_firm)}):
            print bcolors.YELLOW+ "\t[>] Skipping duplicate: %s" % vc_firm + bcolors.ENDC
            continue

        print bcolors.BLUE+ "\t[>] Attempting %s" % vc_firm + bcolors.ENDC

        data = search(vc_firm, 'financial-organization')
        if data is None:
            print bcolors.RED + "\t\t[-] Failed to get %s" % vc_firm + bcolors.ENDC
            bad_count += 1
            bad.append(vc_firm)
            continue
        else:
            if vcs.find_one({'name':data['name']}):
                print bcolors.YELLOW+ "\t[>] Skipping duplicate: %s" % vc_firm + bcolors.ENDC
                continue
            good_count += 1
            print "\t\t[+] Successfully got %s" % vc_firm 
            vcs.insert(data)
            print bcolors.GREEN + "\t\t[+] Successfully Inserted %s" \
                    % vc_firm + bcolors.ENDC

    if len(bad) > 0:
        print bcolors.RED + "[>] Needs work..." + bcolors.ENDC
        print bad

def scrape_companies():
    global vcs, companies 

    # Get list of all companies from VC firms
    print bcolors.PINK + "[>] Getting list of companies in firms..." 
    for vc_firm in vcs.find({}):
        continue
        startups = []
        investments = vc_firm['investments']
        for investment in investments:
            company = investment['funding_round']['company'] 
            if (company['name'], company['permalink']) not in startups:
                startups.append(company)
                companies.update({'permalink': company['permalink']}, {'$set': company}, upsert=True)

        vcs.update({"_id": vc_firm["_id"]}, {"$set": {"startups": startups}})

    print bcolors.PINK + "[>] Getting info about companies..." 
    # Get info about each company
    bad_companies = []
    for company in companies.find({}):

        if 'crunchbase_url' in company or 'funding_rounds' in company:
            # print bcolors.YELLOW+ "\t[>] Skipping duplicate: %s" % company['name'] + bcolors.ENDC
            zero_raised = re.compile(r'\$0')
            currency_regex = re.compile(r'C?([$€£]{1})(\d*\.*\d*)([MBKmbk])')
            pound = "£"
            euro = "€"

            # if company['total_raised'] is not None:
            # continue

            if zero_raised.search(company['total_money_raised']):
                companies.update({'name': company['name'], 'permalink': company['permalink']}, {'$set': {'total_raised' : None}})
            else:
                parts = currency_regex.search(company['total_money_raised'])
                parts = parts.groups() if parts is not None else None

                # TODO: FIX THIS. WE SHOULDNT NEED. BREAKS ON $0
                if parts == None:
                    print bcolors.YELLOW+ "\t[>] Parts == None: %s %s" % (company['name'], company['total_money_raised']) + bcolors.ENDC
                    companies.update({'name': company['name'], 'permalink': company['permalink']}, {'$set': {'total_raised' : None}})
                    bad_companies.append(company['permalink'])
                else:
                    conversion = float(1)
                    if parts[0] == pound:
                        conversion = float(1.65)
                    elif parts[0] == euro:
                        conversion = float(1.38)

                    multiplier = float(1)
                    if parts[2] == 'M' or parts[2] == 'm':
                        multiplier = float(1000000)
                    elif parts[2] == 'K' or parts[2] == 'k':
                        multiplier = float(1000)
                    elif parts[2] == 'B' or parts[2] == 'b':
                        multiplier = float(1000000000)

                    try:
                        """
                        print company['name']
                        print parts
                        print "parts 0"
                        print parts[0]
                        print "parts 1"
                        print parts[1]
                        print "parts 2"
                        print parts[2]
                        print conversion
                        print multiplier
                        print parts[1]
                        """
                        total_raised = multiplier * conversion * float(parts[1])
                    except:
                        print bcolors.YELLOW+ "\t[>] Can't convert: %s %s" % (company['name'], company['total_money_raised']) + bcolors.ENDC
                        bad_companies.append(company['permalink'])
                        total_raised = None

                    companies.update({'name': company['name'], 'permalink': company['permalink']}, {'$set': {'total_raised' : total_raised }})

            """
            total_raised = 0
            for funding_round in company['funding_rounds']:
                if funding_round['raised_currency_code'] != 'USD':
                if funding_round['raised_amount'] is not None:
                    total_raised += funding_round['raised_amount']
                    companies.update({'name': company['name'], 'permalink': company['permalink']}, {'$set': {'total_raised' : total_raised }})
                else:
                    print bcolors.RED + "\t[>] Unknown funding value for %s. Deleting total_raised..." % company['name'] + bcolors.ENDC
                    companies.update({'name': company['name'], 'permalink': company['permalink']}, {'$set': {'total_raised' : None}})
            """
            continue

        print bcolors.BLUE+ "\t[>] Attempting %s" % company['name'] + bcolors.ENDC

        try:
            data = get_entity('company', company['permalink'])
            data.pop('name')
            data.pop('permalink')
            companies.update({'name': company['name'], 'permalink': company['permalink']}, {'$set': data})
            print bcolors.GREEN + "\t\t[+] Successfully Updated %s" % company['name']
        except:
            print bcolors.RED + "\t\t[-] Failed to update %s" % company['name'] + bcolors.ENDC
            bad_companies.append(company['permalink'])
            pass

    if len(bad_companies) > 0:
        print bcolors.RED + "[>] Needs work..." + bcolors.ENDC
        print bad_companies
        print len(bad_companies)

def export_companies_and_vcs():
    company_details = "company, total_raised, ipo, exists\n"

    for company in companies.find({'total_raised' : {'$ne' : None}}):
        company_details += "%s, %s, %s, %s\n" % \
                (company['name'].replace(',',''), company['total_raised'], 1 if company['ipo'] else 0, 0 if company['deadpooled_day'] else 1)

    f = open('company_details.csv', 'w+')
    f.write(company_details.encode('utf-8'))

    vcs_list = [
            "Angel Academe",
            "KPCB Holdings",
            "Accel Partners",
            "Sequoia Capital",
            "New Enterprise Associates",
            "Andreessen Horowitz",
            "Lightspeed Venture Partners",
            "Institutional Venture Partners",
            "Bain Capital Ventures",
            "Union Square Ventures",
            "Greylock Partners",
            "Khosla Ventures",
            "Shasta Ventures",
            "Foundry Group",
            "First Round Capital",
            "Google Ventures",
            "SoftTech VC",
            "Benchmark",
            "Bessemer Venture Partners",
            "Draper Fisher Jurvetson (DFJ)",
            "General Catalyst Partners",
            "Intel Capital",
            "SV Angel"
            ]

    vc_details = "vc, failed_count, ipo_count, ipo_percentage, average_total_raised"

    for vc in vcs_list:
        vc_details += "\n%s, " % vc
        failed = 0
        ipoed = 0
        total_raised = 0
        startups = vcs.find_one({'name' : vc})['startups']
        for startup in startups:
            company = companies.find_one({'permalink' : startup['permalink']})
            try:
                total_raised += company['total_raised'] if company['total_raised'] else 0
            except:
                continue
            if company['ipo']:
                ipoed += 1
            if company['deadpooled_year']:
                failed += 1
        vc_details += "%s, %s, %s, %s" \
                % (failed, ipoed, float(ipoed) / (ipoed + failed) if (ipoed + failed) > 0 else 1, float(total_raised) / len(startups))


    f = open('vc_details.csv', 'w+')
    f.write(vc_details.encode('utf-8'))


def export_matching():

    vcs_list = [
            "Angel Academe",
            "KPCB Holdings",
            "Accel Partners",
            "Sequoia Capital",
            "New Enterprise Associates",
            "Andreessen Horowitz",
            "Lightspeed Venture Partners",
            "Institutional Venture Partners",
            "Bain Capital Ventures",
            "Union Square Ventures",
            "Greylock Partners",
            "Khosla Ventures",
            "Shasta Ventures",
            "Foundry Group",
            "First Round Capital",
            "Google Ventures",
            "SoftTech VC",
            "Benchmark",
            "Bessemer Venture Partners",
            "Draper Fisher Jurvetson (DFJ)",
            "General Catalyst Partners",
            "Intel Capital",
            "SV Angel"
            ]
    vc_startups = {}

    vcs_to_companies = "source, target"
    for vc in vcs_list:
        startups = vcs.find_one({'name': vc})['startups']
        for startup in startups:
            vcs_to_companies += "\n%s, %s" % (vc, startup['name'].replace(',',''))

    """
    for vc in vcs_list:
        vc_startups[vc] = [startup['name'] for startup in vcs.find_one({'name': vc})['startups']]

    vcs_to_companies = "company, "
    doOnce = True

    for company in companies.find({'total_raised' : {'$ne': None}}):
        line = company['name'] + ', '
        for vc, startups in vc_startups.iteritems():
            if doOnce:
                vcs_to_companies += vc + ', ' 

            if company['name'] in startups:
                line += '1, '
            else:
                line += '0, '

        if doOnce:
            vcs_to_companies = vcs_to_companies[:-2] + '\n'

        vcs_to_companies += (line[:-2] + '\n')
        doOnce = False
    """
        
    f = open('vcs_to_companies.csv', 'w+')
    f.write(vcs_to_companies.encode('utf-8'))
    


if __name__ == '__main__':

    # scrape_vcs()
    # scrape_companies()
    export_companies_and_vcs()
    export_matching()

