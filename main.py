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

# Permalink names for billion-dollar startups as of February 2015
billion_dollar_club = ['xiaomi', 'uber', 'palantir-technologies', 'space-exploration-technologies', 'flipkart', 'airbnb', 'dropbox', 'snapchat', 'theranos', 'meituan-com', 'square', 'pinterest', 'wework', 'cloudera', 'spotify', 'stripe', 'jawbone', 'fanatics', 'vancl', 'legendary-entertainment', 'pure-storage', 'bloom-energy', 'powa-technologies', 'inmobi', 'houzz', 'dianping', 'nutanix', 'magic-leap', 'snapdeal', 'coupang', 'instacart', 'delivery-hero', 'intarcia-therapeutics', 'mongodb-inc', 'docusign', 'adyen', 'koudai', 'jasper-wireless', 'deem', 'social-finance', 'sunrun', 'appnexus', 'automattic', 'fab', 'gilt-groupe', 'tiny-speck', 'actifio', 'proteus-biomedical', 'appdynamics', 'ironsource', 'home24-france', 'yello-mobile', 'cloudfare', 'evernote', 'good-technology', 'eventbrite', 'tango', 'insidesales-com', 'mogujie', 'kabam', 'lookout', 'justfabulous', 'the-honest-co', 'credit-karma', 'qualtrics', 'razer', 'shopify', 'ani-technologies', 'shazam-entertainment', 'beibei', 'grabtaxi', 'moderna-therapeutics', 'beats-by-dr-dre', 'box', 'coupons-com', 'fisker', 'gopro', 'hortonworks', 'jd-com', 'lashou-com', 'lending-club', 'mobileye-vision-technologies', 'nest-labs', 'new-relic', 'rocket-internet', 'wayfair', 'zalando' ]

# Get investors in this company along with investment round they invested in.
def get_funding_rounds(company_permalink):
    try:
        company = cb.organization(company_permalink)
    except:
        logging.warning('Failed to get organization/' + company_permalink)
        return
    total_raised = company.total_funding_usd if company.total_funding_usd else 0
    total_funding_rounds = company.data['relationships']['funding_rounds']['paging']['total_items']
    funding_rounds = company.funding_rounds
    if len(funding_rounds) < total_funding_rounds:
        funding_rounds = cb.more(funding_rounds)

    all_funding_rounds = []

    # Iterate through funding rounds
    for funding_round in funding_rounds:
        try:
            funding_round = cb.funding_round(funding_round.uuid)
        except:
            logging.warning('Failed to get funding_round/' + funding_round.uuid)
            continue

        round_label = funding_round.series
        if round_label:
            round_label = 'Series ' + round_label.capitalize()
        else:
            round_label = funding_round.funding_type.capitalize()

        # Get date of investment round announcement
        round_date = funding_round.announced_on

        if round_date is None or not funding_round.money_raised_usd:
            logging.warning('Failed to get ' + round_label + ' funding_round/' + funding_round.permalink)
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

def main():
    funding_rounds = []
    for company_permalink in billion_dollar_club:
        more_funding_rounds = get_funding_rounds(company_permalink)
        if more_funding_rounds:
            funding_rounds.extend(more_funding_rounds)

    print json.dumps(funding_rounds, default=json_util.default)

    return

if __name__ == "__main__":
    main()
