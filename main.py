import re
import requests
import json
from secrets import CRUNCHBASE_API_KEY
from colors import bcolors

# NOTES
# obj = json.loads(json_string) 
# print bcolors.HEADER + "Warning: No active frommets remain. Continue?" + bcolors.ENDC

# List of top VC firms
vc_firms = ["accel-partners", "kpcb-holdings-inc", "Sequoia", "new-enterprise-associates", "Andressen Horowitz", "Lightspeed", "Benchmark", "Bessemer", "IVP", "DFJ", "Bain Capital Ventures", "Union Square", "Greylock", "Khosala", "Shasta", "General Catalyst", "Intel capital", "Foundry", "First Round", "SV Angel", "Google Ventures", "Softech"]

# For CrunchBase API access, add onto HTTP request as parameter
payload = {'api_key' : CRUNCHBASE_API_KEY}
good_count = 0
bad_count = 0
bad = []

if __name__ == '__main__':

    print bcolors.PINK + "[>] Running MineBase scraper with %s firms..." % len(vc_firms) + bcolors.ENDC

    for vc_firm in vc_firms:

        if re.search(' ', vc_firm):
            print bcolors.YELLOW + "\t[-] Skipping %s" % vc_firm + bcolors.ENDC
            bad_count += 1
            bad.append(vc_firm)
            continue
        else:
            print bcolors.BLUE+ "\t[>] Attempting %s" % vc_firm + bcolors.ENDC

        req_url = "http://api.crunchbase.com/v/1/financial-organization/%s.js" % vc_firm
        req = requests.get(req_url, params=payload)
        if req.status_code == 200:
            good_count += 1
            print bcolors.GREEN + "\t\t[+] Successfully got %s" % vc_firm + bcolors.ENDC
        else:
            bad_count += 1
            bad.append(vc_firm)
            print bcolors.RED + "\t\t[-] Failed to get %s" % vc_firm + bcolors.ENDC

    print bcolors.RED + "[>] Needs work..." + bcolors.ENDC
    print bad
