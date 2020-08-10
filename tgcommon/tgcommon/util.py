import re

def normalise_to_ckey(key):
	return re.sub('[^A-Za-z0-9]+', '', key)
