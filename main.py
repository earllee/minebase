# -*- coding: utf-8 -*-
import json
import logging
import pdb
import pymongo
from bson import json_util
from datetime import datetime
from pycrunchbase import CrunchBase
from secrets import CRUNCHBASE_API_KEY

# Establish connections with database for writing.
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client.mgt535
connections = db.connections
saved_funding_rounds = db.funding_rounds

# Establish CrunchBase API interface
cb = CrunchBase(CRUNCHBASE_API_KEY)

# Permalink names for billion-dollar startups as of February 2015
billion_dollar_club = ['xiaomi', 'uber', 'palantir-technologies', 'space-exploration-technologies', 'flipkart', 'airbnb', 'dropbox', 'snapchat', 'theranos', 'meituan-com', 'square', 'pinterest', 'wework', 'cloudera', 'spotify', 'stripe', 'jawbone', 'fanatics', 'vancl', 'legendary-entertainment', 'pure-storage', 'bloom-energy', 'powa-technologies', 'inmobi', 'houzz', 'dianping', 'nutanix', 'magic-leap', 'snapdeal', 'coupang', 'instacart', 'delivery-hero', 'intarcia-therapeutics', 'mongodb-inc', 'docusign', 'adyen', 'koudai', 'jasper-wireless', 'deem', 'social-finance', 'sunrun', 'appnexus', 'automattic', 'fab-com', 'gilt-groupe', 'tiny-speck', 'actifio', 'proteus-biomedical', 'appdynamics', 'ironsource', 'home24', 'yello-mobile', 'cloudflare', 'evernote', 'good-technology', 'eventbrite', 'tango-2', 'insidesales-com', 'mogujie', 'kabam', 'lookout', 'justfabulous', 'the-honest-company', 'credit-karma', 'qualtrics', 'razer', 'shopify', 'ani-technologies', 'shazam-entertainment', 'beibei', 'grabtaxi', 'moderna-therapeutics', 'beats-by-dr-dre', 'box', 'coupons-com', 'fisker', 'gopro', 'hortonworks', 'jd-com', 'lashou-com', 'lending-club', 'mobileye-vision-technologies', 'nest-labs', 'new-relic', 'rocket-internet', 'wayfair', 'zalando' ]

def get_funding_round(funding_round_uuid):
    # Skip if we already got this round
    if saved_funding_rounds.find_one({'permalink' : funding_round_uuid}):
        return None

    try:
        funding_round = cb.funding_round(funding_round_uuid)
    except:
        logging.warning('(3) Failed to get funding_round/' + funding_round_uuid)
        return None

    if not bool(funding_round.investments):
        return None

    round_label = funding_round.series
    if round_label:
        round_label = 'Series ' + round_label.capitalize()
    else:
        round_label = funding_round.funding_type.capitalize()

    # Get date of investment round announcement
    round_date = funding_round.announced_on

    if round_date is None:
        logging.warning('(4) Failed to get funding_round/' + funding_round.permalink)
        pdb.set_trace()
        return None

    company = funding_round.funded_organization[0]

    payload = {
        'org_name' : company.name,
        'org_permalink' : company.permalink,
        'announce_date' : round_date,
        'amount_raised' : funding_round.money_raised_usd,
        'label' : round_label,
        'investors' : [],
        'permalink' : funding_round.permalink
    }

    # Iterate through individual investments in round, which constitute
    # money invested by a single investor.
    for investment in funding_round.investments:
        try:
            payload['investors'].append(str(investment.investor))
        except:
            logging.warning('(1) Failed to add investor.')
            pdb.set_trace()

    return payload

# Get investors in this company along with investment round they invested in.
def get_funding_rounds(company_permalink):
    global saved_funding_rounds

    try:
        company = cb.organization(company_permalink)
    except:
        logging.warning('(1) Failed to get organization/' + company_permalink)
        return

    try:
        total_funding_rounds = company.data['relationships']['funding_rounds']['paging']['total_items']
    except:
        logging.warning('(2) Failed to get organization/' + company_permalink)
        return

    funding_rounds = company.funding_rounds
    if len(funding_rounds) < total_funding_rounds:
        funding_rounds = cb.more(funding_rounds)

    all_funding_rounds = []

    # Iterate through funding rounds
    for funding_round in funding_rounds:

        payload = get_funding_round(funding_round.uuid)
        if payload is None:
            continue

        # Iterate through individual investments in round, which constitute
        # money invested by a single investor.
        for investment in funding_round.investments:
            try:
                payload['investors'].append(str(investment.investor))
            except:
                logging.warning('(1) Failed to add investor.')
                pdb.set_trace()

        # Update a round with more funding if the round already exists
        did_update = False
        for _round in all_funding_rounds:
            if _round['label'] == payload['label']:
                _round['amount_raised'] = _round['amount_raised'] + \
                        payload['amount_raised']
                _round['investors'].extend(payload['investors'])
                if payload['announce_date'] > _round['announce_date']:
                    _round['announce_date'] = payload['announce_date']
                did_update = True

        # Otherwise, add the new round
        if not did_update:
            all_funding_rounds.append(payload)

    return all_funding_rounds

def main():
    global saved_funding_rounds

    # Code to scrape just missing funding rounds
    """
    for funding_round_uuid in missing_funding_rounds_uuids:
        funding_round = get_funding_round(funding_round_uuid)

        # On success, add funding rounds to all funding rounds
        if funding_round and not saved_funding_rounds.find_one(\
                        {'permalink' : funding_round['permalink']}):
            saved_funding_rounds.insert(funding_round)
    """

    # Code to scrape funding rounds for all companies in billion dollar club
    """
    funding_rounds = []
    for company_permalink in billion_dollar_club:
        # Skip if we already tried scraping this company
        if saved_funding_rounds.find_one(\
                {'org_permalink' : company_permalink}):
            continue

        # Get funding rounds for this company
        more_funding_rounds = get_funding_rounds(company_permalink)

        # On success, add funding rounds to all funding rounds
        if more_funding_rounds:
            funding_rounds.extend(more_funding_rounds)

            # Save each funding round in Mongo
            for funding_round in more_funding_rounds:
                if not saved_funding_rounds.find_one(\
                        {'permalink' : funding_round['permalink']}):
                    saved_funding_rounds.insert(funding_round)
    """

    # Code to export CSV of connections between investors
    f = open('pairs.txt', 'w')
    # pairs = []
    count = 0
    for company_permalink in billion_dollar_club:
        investors_so_far = []
        funding_rounds = saved_funding_rounds.find({'org_permalink' : \
            company_permalink}).sort('announce_date', pymongo.DESCENDING)
        for funding_round in funding_rounds:
            current_investors = funding_round['investors']

            for investor in investors_so_far:
                for current_investor in current_investors:
                    if current_investor != investor:
                        try:
                            # count += 1
                            f.write(investor + ',' + current_investor + '\n')
                            # pairs.append((investor, current_investor))
                        except:
                            count += 1

            # Add new set of investors
            investors_so_far.extend(current_investors)

    f.close()
    print count
    return

# This triggers the main function on run.
if __name__ == "__main__":
    main()
