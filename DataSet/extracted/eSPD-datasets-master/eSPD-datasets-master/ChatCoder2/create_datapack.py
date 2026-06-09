import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
# to be able to import modules from parent directory
import xml.etree.ElementTree as ET
from util import getUNIXTimestamp
from datetime import datetime, timezone
from DynamicArray import DynamicArray
import re
import numpy as np
import regex
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description='Creates ChatCoder2 datapacks')
parser.add_argument(
	"--datapackID",
	dest='datapackID',
	help="the unique identifier that the datapack is going to have",
	default="ChatCoder2"
)
parser.add_argument(
	"--description",
	dest='description',
	help="description of the datapack",
	default=None
)
args = parser.parse_args()

print("\n---           Arguments           ---")
for key, val in args.__dict__.items(): print("%20s: %s" % (key, val))
print()

print("parsing logs…")


with open("ChatCoder2/raw_dataset/AllChatLogs.xml", "r") as file:
	file.readline() # ignore first empty line
	logs = ET.parse(file)
logsRoot = logs.getroot()

print("parsing labels…")
labels = ET.parse("ChatCoder2/raw_dataset/AllCodingsExport2.xml")
labelsRoot = labels.getroot()

# example datapacks and documentation can be found in the chat-visualizer repo
datapack = {
	"datapackID": args.datapackID,
	"description": args.description,
	"generatedAtTime": getUNIXTimestamp(), # unix timestamp
	"chats": {}
}
chats = datapack["chats"] # shorthand

print("parsing done!")
print("saving chatlogs and finding errors…")

# finding errors
noChatName = 0
noLineNum = 0
noUserID = 0
badDateTime = 0
noDateTime = 0
noBody = 0
errorMessages = 0


##
## roughly parses dates from the corpus
##
## :param      dateString:  The date string
## :type       dateString:  { String }
##
## :returns:   { Null if not properly formatted or datetime }
## :rtype:     { Null or datetime }
##
def parseDate(dateString):
	text = dateString.upper()
	text = re.sub(r"A\.M\.?", "AM", text)
	text = re.sub(r"P\.M\.?", "PM", text)
	# print(text)

	# we ignore seconds and dates because the corpus is not properly formatted
	# and it"s unlikely that someone starts messaging someone else the next day
	# and the time is less than 25 minutes after
	timePattern = r"(\d{1,2})\s*:\s*(\d{1,2})(?:\s*:\s*\d{1,2})?\s*((?:PM|AM)?)"
	match = re.search(timePattern, text)
	if match == None: return None
	hours = match.group(1)
	minutes = match.group(2)
	AMPM = match.group(3)
	dateString = "1/1/1970 " + hours + ":" + minutes + " " + AMPM if AMPM else \
	             "1/1/1970 " + hours + ":" + minutes

	# "Jun 28 2018 at 7:40AM" -> "%b %d %Y at %I:%M%p"
	# "September 18, 2017, 22:19:55" -> "%B %d, %Y, %H:%M:%S"
	# "Sun,05/12/99,12:30PM" -> "%a,%d/%m/%y,%I:%M%p"
	# "Mon, 21 March, 2015" -> "%a, %d %B, %Y"
	# "2018-03-12T10:12:45Z" -> "%Y-%m-%dT%H:%M:%SZ"
	date_time_str = "%d/%m/%Y %I:%M %p" if AMPM else "%d/%m/%Y %H:%M"
	try: return datetime.strptime(dateString, date_time_str)
	except: return None


def bodyPreprocessing(body):
	# fix some scraping errors in data related to dates
	datePattern = r"\d{1,2}\/\d{1,2}\/?(?:\d\d\d\d|\d\d|\d)?"
	timePattern = r"\d{1,2}:\d{1,2}(?::\d{1,2})?\s*(?:pm|am)?"
	datePattern = r"(\s*\S+\s*[\(\[](?:%s)?\s*(?:%s)[\)\]]:?\s*)" % (datePattern, timePattern)
	otherDatePattern = r"\w{2,3} \w{2,3} (?:%s) (?:\d\d\d\d|\d\d|\d)" % timePattern
	# body = re.sub(datePattern, "| [[date: \g<1>]]", body)
	# body = re.sub(datePattern, MESSAGE_DELIMITER, body) # this. is. so. awesome!!!!
	body = re.sub(datePattern, " ", body)
	body = re.sub(otherDatePattern, " ", body) # exists only a few times
	# if body != None and re.search(datePattern, body):
	# 	# body = "[[date bug: %s]]" % body
	# 	body = "[[date bug]]"

	# there's a weird bug in the dataset where messages by these users are
	# prepended with a colon
	if userID in ["fishman1192002", "westwoodkush"]:
		body = re.sub(r"^:", "", body)

	body = re.sub(r"\r", "", body) # remove carriage returns
	body = re.sub(r"\n+", "\\n", body)
	body = re.sub(r"\s+", " ", body) # the one time to replace tabs with spaces
	body = body.strip()
	return body


#
# Populate chats object
#

for message in logsRoot:
	chatName = message.find("name")
	lineNum = message.find("lineNum")
	userID = message.find("userID")
	dateTime = message.find("dateTime")
	body = message.find("body")
	comment = message.find("comment")
	hasErrors = False

	# if dateTime == None : hasErrors = True; noDateTime += 1
	if dateTime == None: noDateTime += 1
	if     body == None: noBody += 1
	if   userID == None: noUserID += 1; hasErrors = True; continue
	if  lineNum == None: noLineNum += 1; hasErrors = True; continue
	if chatName == None: noChatName += 1; hasErrors = True; continue

	chatName = chatName.text    if chatName != None else "[[no chatName]]"
	lineNum = int(lineNum.text) if lineNum != None else "[[no lineNum]]"
	userID = userID.text        if userID != None else "[[no userID]]"
	body = body.text            if body != None else None
	if dateTime is not None:
		dateTime = parseDate(dateTime.text)
		if dateTime is None: badDateTime += 1

	body = bodyPreprocessing(body) if body is not None else None

	# initialize chat
	if chatName not in chats:
		chats[chatName] = {
			# "description": "Some comments about the chat",
			"hasErrors": False,
			"className": "predator",
			"authorOnRightSide": None, # appears on the right side in visualizations
			# "predictedClassName": "negative",
			"isLabelled": False,
			"numOfNonemptyMessages": 0,
			"numOfPredatorMessages": 0,
			"numOfNonPredatorMessages": 0,

			# This array stores different content types of the chat.
			# Currently there are
			# - messages (regular text messages) and
			# - separators (displayed as horizontal rules, e.g. to indicate
			#   time has passed between messages)
			# In the future, we might add other types of content like images
			# and voice messages.
			"content": DynamicArray()
		}
	chat = chats[chatName]
	chat["hasErrors"] = chat["hasErrors"] or hasErrors

	isFromPredator = userID == chatName or \
	                 userID == "{%s}" % chatName or \
	                 bool(regex.search('(%s){e<=3}' % chatName, userID))

	if isFromPredator: chat["numOfPredatorMessages"] += 1
	else: chat["numOfNonPredatorMessages"] += 1
	if body: chat["numOfNonemptyMessages"] += 1

	# victim is on the right
	if not isFromPredator: chat["authorOnRightSide"] = userID

	content = {
		"type": "message",
		"author": userID,
		"body": body,
		"time": int(dateTime.replace(tzinfo=timezone.utc).timestamp()*1000) if dateTime else None,  # unix timestamp
		"dateTime": dateTime,
		"isFromPredator": isFromPredator,
		"labels": set(),

		# "prediction": 0.3256,
		# "labels": ["bar"],
		# "HTMLclassNames": ["warning"]

		"type": "message",
		"lineNum": lineNum,
	}
	if isFromPredator: content["HTMLclassNames"] = ["isFromPredator"]

	chat["content"][lineNum-1] = content

for chat in chats.values():
	# when we insert segments later, this won't be true anymore
	chat["numberOfMessages"] = len(chat["content"])

######################## Some stats


print("Number of messages with \n    noChatName %s, noLineNum %s, noUserID %s, noDateTime %s, badDateTime %s, noBody %s" % (noChatName, noLineNum, noUserID, noDateTime, badDateTime, noBody))

numberOfChats = len(chats)
numberOfMessages = 0
numberOfPredatorMessages = 0
noneMessages = 0
for chatName in chats:
	numberOfMessages += chats[chatName]["numberOfMessages"]
	# print("%s: %s" % (chatName, chats[chatName]["content"].size()))
	for messageI, message in enumerate(chats[chatName]["content"], start=0):
		if message == None:
			noneMessages += 1
			# chats[chatName]["hasErrors"] = True
			continue
		if message["isFromPredator"]:
			numberOfPredatorMessages += 1

numberOfVictimMessages = numberOfMessages - numberOfPredatorMessages
# there are only two types of messages

print("In total: %s chats with a total of %s messages, averaging %s messages per chat" % (numberOfChats, numberOfMessages, round(numberOfMessages/numberOfChats)))
print("In total: %s `None` Messages" % (noneMessages))

errorChats = 0
for chatName in chats:
	if chats[chatName]["hasErrors"]: errorChats += 1
print("In total: %s error chats" % (errorChats))


# how many (labelled) chats have errors?

############################ Labels

CODING_LEGEND = {
	"200": "Personal Information (Predator)",
	"210": "Personal Information (Victim)",
	"600": "Grooming (Predator)",
	"610": "Grooming (Victim)",
	"900": "Approach (Predator)",
	"910": "Approach (Victim)"
}

print("\nProcessing labels…")

numberOfLabelsVictimPI = 0
numberOfLabelsVictimG = 0
numberOfLabelsVictimA = 0
numberOfLabelsPredatorPI = 0
numberOfLabelsPredatorG = 0
numberOfLabelsPredatorA = 0

wrongChatNames = 0
noGroomingStage = 0
wrongLineNum = 0

for label in labelsRoot:
	chatName = label.find("name")
	codingVersion = label.find("CodingVersionID") # e.g. 372
	lineNum = label.find("lineNum") # starts with 1
	groomingStage = label.find("category") # e.g. 200
	# userID = label.find("userID") # for some reason this is sometimes escaped with {}
	# dateTime = label.find("dateTime")
	# body = label.find("body")
	# comment = label.find("comment")

	chatName = chatName.text if chatName != None else "[[no chatName]]"
	if chatName not in chats:
		wrongChatNames += 1
		continue

	chats[chatName]["isLabelled"] = True

	# if codingVersion != None: codingVersion = codingVersion.text
	# else: codingVersion = "[[no codingVersion]]"

	lineNum = int(lineNum.text) if lineNum != None else None
	if int(lineNum)-1 >= chats[chatName]["numberOfMessages"]:
		wrongLineNum += 1
		continue

	groomingStage = groomingStage.text if groomingStage != None else None
	if groomingStage == None: noGroomingStage += 1; continue

	if   groomingStage == "200": numberOfLabelsPredatorPI += 1 # "Personal Information (Predator)"
	elif groomingStage == "210": numberOfLabelsVictimPI += 1   # "Personal Information (Victim)"
	elif groomingStage == "600": numberOfLabelsPredatorG += 1  # "Grooming (Predator)"
	elif groomingStage == "610": numberOfLabelsVictimG += 1    # "Grooming (Victim)"
	elif groomingStage == "900": numberOfLabelsPredatorA += 1  # "Approach (Predator)"
	elif groomingStage == "910": numberOfLabelsVictimA += 1    # "Approach (Victim)"

	msg = chats[chatName]["content"][lineNum-1]
	# keep in mind that a message can have multiple labels
	if   groomingStage in ["200", "210"]: msg["labels"].add("PI") # Personal Information
	elif groomingStage in ["600", "610"]: msg["labels"].add("G")  # Grooming
	elif groomingStage in ["900", "910"]: msg["labels"].add("A")  # Approach
	# else: raise Exception("undefined grooming stage `%s`" % groomingStage)


# Labelling statistics

numberOfLabeledVictimMessages   = numberOfLabelsVictimPI   + numberOfLabelsVictimG   + numberOfLabelsVictimA
numberOfLabeledPredatorMessages = numberOfLabelsPredatorPI + numberOfLabelsPredatorG + numberOfLabelsPredatorA
numberOfLabeledMessages = numberOfLabeledPredatorMessages + numberOfLabeledVictimMessages

print("%s messages (%s%%) were by predators" % (numberOfPredatorMessages, round(100*numberOfPredatorMessages/numberOfMessages)))
print("%s messages (%s%%) are labeled. %s (%s%%) of the predator messages were labeled, %s (%s%%) of the victim messages were labeled" % (
	numberOfLabeledMessages,         round(100*numberOfLabeledMessages/numberOfMessages),
	numberOfLabeledPredatorMessages, round(100*numberOfLabeledPredatorMessages/numberOfPredatorMessages),
	numberOfLabeledVictimMessages,   round(100*numberOfLabeledVictimMessages/numberOfVictimMessages)))
print("%s wrongChatNames, %s wrongLineNum" % (wrongChatNames, wrongLineNum))

print("pi = %s" % (numberOfLabelsVictimPI+numberOfLabelsPredatorPI))
print("g = %s" % (numberOfLabelsVictimG+numberOfLabelsPredatorG))
print("a = %s" % (numberOfLabelsVictimA+numberOfLabelsPredatorA))


# insert segments between messages

# we ignore dates, we only consider hours, minutes and seconds
# if we have a scenario like
# (12:10) message from A
# (12:15) message from B
# (None)  message from B
# (13:00)  [[no body]]
# (13:55) message from A
# then we cut before the 13:55 message

totalNoOfSegments = 0 # the first message always starts a new segment
for chatName in chats:
	chat = chats[chatName]
	noOfSegments = 1
	lastTime = None
	i = 0
	while i < len(chat["content"]): # keeps increasing
		msg = chat["content"][i]
		assert msg == None or msg["type"] == "message", "somehow got a %s" % msg["type"]
		if msg == None or msg["dateTime"] is None: i += 1; continue
		# time = msg["time"]

		# todo minutes
		time = msg["dateTime"]
		messageDelay = (time - lastTime).seconds/60 if \
			(time and lastTime) else 0
		# messageDelay = (time - lastTime)/1000/60 if \
		# 	(time and lastTime) else 0
		# if chatName == "HAIRYONE4U": print(messageDelay)
		# if messageDelay < 0, there has to have been at least a day of delay
		startsNewSegment = messageDelay > 25 or messageDelay < 0

		if startsNewSegment:
			# if chatName == "c_meandu": print("new segment before %i" % msg["lineNum"])
			noOfSegments += 1
			chat["content"].insert(i, {"type": "separator"})
			i += 1 # next iteration would be the same message as this one

		if time is not None: lastTime = time
		i += 1

	chat["noOfSegments"] = noOfSegments
	totalNoOfSegments += noOfSegments

print("total segments: %s" % totalNoOfSegments)
print("that's %s on average per chat" % np.round(totalNoOfSegments/len(chats), 2))

# Dump datapack

print("dumping datapack…")

def converter(obj):
	if type(obj) == set: return list(obj)
	return getattr(obj, '__dict__', str(obj))
	# this also serializes DynamicArray to list

outPath = "ChatCoder2/datapacks/"
Path(outPath).mkdir(parents=True, exist_ok=True)
with open(outPath + "datapack-%s.json" % args.datapackID, "w") as file:
	json.dump(datapack, file, default=converter)

print("dumped chats.")
