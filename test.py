import requests
from fuzzywuzzy import fuzz, process
from tomlkit import loads, parse

response = requests.get(
    url="https://raw.githubusercontent.com/tgstation/tgstation/gbp-balances/.github/gbp-balances.toml",
)
content = response.text
document = parse(content)
gbptouser = {}
postouser = dict()
usertogbp = dict()
for githubid, gbp in document.items():
    user = gbp.trivia.comment.strip("# ")
    gbptouser[gbp] = user
    usertogbp[user] = gbp

# Sort by GBP count
gbptouser = dict(sorted(gbptouser.items(), reverse=True))
# index user to position
for index, item in enumerate(gbptouser.items()):
    index = index + 1
    gbp, user = item
    postouser[index] = user
print(postouser)
print(postouser["1"])
