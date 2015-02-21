# -*- coding: utf-8 -*-
import json
import logging
import pdb
from bson import json_util
from datetime import datetime
from pycrunchbase import CrunchBase
from pymongo import MongoClient
from secrets import CRUNCHBASE_API_KEY

# Establish connections with database for writing.
client = MongoClient('mongodb://localhost:27017/')
db = client.mgt535
investors = db.investors
cb = CrunchBase(CRUNCHBASE_API_KEY)

# Get investors in this company along with investment round they invested in.
def get_funding_rounds(company_permalink):
    company = cb.organization(company_permalink)
    total_raised = company.total_funding_usd
    total_funding_rounds = company.data['relationships']['funding_rounds']['paging']['total_items']
    funding_rounds = company.funding_rounds
    if len(funding_rounds) < total_funding_rounds:
        funding_rounds = cb.more(funding_rounds)

    if not total_raised:
        logging.warning('Couldn\'t get info on ' + company_permalink)

    all_funding_rounds = []

    # Iterate through funding rounds
    for funding_round in funding_rounds:
        funding_round = cb.funding_round(funding_round.uuid)
        round_label = funding_round.series
        if round_label:
            round_label = 'Series ' + round_label
        else:
            round_label = funding_round.funding_type.capitalize()

        # Special case: Funding round has no named investors
        # if 'investments' not in round_data['relationships']:
        #     for _round in all_funding_rounds:
        #         if _round['series'] == round_series:
        #             _round['amount_raised'] = _round['amount_raised'] + \
        #                     round_properties['money_raised_usd']
        #     continue
        # else:
        #    round_investment = round_data['relationships']['investments']['items']

        if not funding_round.investments:
            logging.warning('No investments found in this round: ' + funding_round.permalink)

        # Get date of investment round announcement
        round_date = funding_round.announced_on
        # round_date_code = funding_round.announced_on_trust_code
        # round_date = get_date(round_date_code, round_date_raw)

        if round_date is None:
            logging.warning('Couldn\'t get info on ' + funding_round.permalink + \
                    ' ' + round_label)
            continue

        payload = {
            'date' : round_date,
            'amount_raised' : funding_round.money_raised_usd,
            'label' : round_label,
            'investors' : []
        }

        # Iterate through individual investments in round, which constitute
        # money invested by a single investor.
        for investment in funding_round.investments:
            # investor = investment['investor']
            #
            # if 'first_name' in investor and 'last_name' in investor:
            #     investor_name = investor['first_name'] + ' ' + investor['last_name']
            # elif 'name' in investor:
            #     investor_name = investor['name']
            # else:
            #     pdb.set_trace()
            #     investor_name = 'N/A'
            #
            # investor_permalink = investment['investor']['path']
            payload['investors'].append(str(investment.investor))

        # Update a round with more funding if the round already exists
        did_update = False
        for _round in all_funding_rounds:
            if _round['label'] == payload['label']:
                _round['amount_raised'] = _round['amount_raised'] + \
                        payload['amount_raised']
                _round['investors'].extend(payload['investors'])
                if payload['date'] > _round['date']:
                    _round['date'] = payload['date']
                did_update = True

        # Otherwise, add the new round
        if not did_update:
            all_funding_rounds.append(payload)

    return all_funding_rounds

def get_date(trust_code, date_raw):
    if trust_code < 7:
        return None
    # elif trust_code == 6:
    #     return datetime.strptime(date_raw, '%Y-%m-%d')
    elif trust_code == 7:
        return datetime.strptime(date_raw, '%Y-%m-%d')

def main():
    funding_rounds = None
    for company_permalink in ['uber']:
        funding_rounds = get_funding_rounds(company_permalink)

    print json.dumps(funding_rounds, default=json_util.default)

    pdb.set_trace()


    return

if __name__ == "__main__":
    main()

# Permalink names for billion-dollar startups as of February 2015
billion_dollar_club = ['xiaomi',
                        'uber',
                        'palantir-technologies',
                        'space-exploration-technologies',
                        'flipkart',
                        'airbnb',
                        'dropbox',
                        'snapchat',
                        'theranos',
                        'meituan-com',
                        'square',
                        'pinterest',
                        'wework',
                        'cloudera',
                        'spotify',
                        'stripe',
                        'jawbone',
                        'fanatics',
                        'vancl',
                        'legendary-entertainment',
                        'pure-storage',
                        'bloom-energy',
                        'powa-technologies',
                        'inmobi',
                        'houzz',
                        'dianping',
                        'nutanix',
                        'magic-leap',
                        'snapdeal',
                        'coupang',
                        'instacart',
                        'delivery-hero',
                        'intarcia-therapeutics',
                        'mongodb-inc',
                        'docusign',
                        'adyen',
                        'koudai',
                        'jasper-wireless',
                        'deem',
                        'social-finance',
                        'sunrun',
                        'appnexus',
                        'automattic',
                        'fab',
                        'gilt-groupe',
                        'tiny-speck',
                        'actifio',
                        'proteus-biomedical',
                        'appdynamics',
                        'ironsource',
                        'home24-france',
                        'yello-mobile',
                        'cloudfare',
                        'evernote',
                        'good-technology',
                        'eventbrite',
                        'tango',
                        'insidesales-com',
                        'mogujie',
                        'kabam',
                        'lookout',
                        'justfabulous',
                        'the-honest-co',
                        'credit-karma',
                        'qualtrics',
                        'razer',
                        'shopify',
                        'ani-technologies',
                        'shazam-entertainment',
                        'beibei',
                        'grabtaxi',
                        'moderna-therapeutics',
                        'beats-by-dr-dre',
                        'box',
                        'coupons-com',
                        'fisker',
                        'gopro',
                        'hortonworks',
                        'jd-com',
                        'lashou-com',
                        'lending-club',
                        'mobileye-vision-technologies',
                        'nest-labs',
                        'new-relic',
                        'rocket-internet',
                        'wayfair',
                        'zalando'
                        ]


################################################################################


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
