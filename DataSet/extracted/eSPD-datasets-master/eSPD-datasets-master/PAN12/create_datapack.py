import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
# to be able to import modules from parent directory
import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime, timezone
from util import getUNIXTimestamp
from DynamicArray import DynamicArray
from util import isNonemptyMsg
import json
import argparse
from pathlib import Path

verbose = True
def ndprint(string=""):
	if not verbose: print(string)
	return False
def dprint(string=""):
	if verbose: print(string)
	return False

parser = argparse.ArgumentParser(description='Creates PAN12 datapacks')
parser.add_argument(
	"--datapackID",
	dest='datapackID',
	help="an datapackID for the datapack",
	default="PAN12"
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


def bodyPreprocessing(body):
	body = html.unescape(body)
	# there is some stuff like &amp;amp;#8212; in there. There is even a discussion about escaping. ab7faae5d7b250ea8606486575f8f79c
	# fix html escapes
	# .replace("&apos;", "'")
	# .replace("&quot;", "\"")
	# .replace("&amp;", "&")
	# .replace("&lt;", "<")
	# .replace("&gt;", ">")
	# .replace("&#39;", "'")
	# .replace("\\", "\\\\")
	body = re.sub(r"\r", "", body) # remove carriage returns
	body = re.sub(r"\n+", "\\n", body)
	body = re.sub(r"\s+", " ", body) # the one time to replace tabs with spaces
	body = body.strip()
	return body


def processDataset(datasetType, messageDatasetPath, predIDsPath):
	datapack = {
		"datapackID": args.datapackID + "-" + datasetType,
		"description": args.description,
		"generatedAtTime": getUNIXTimestamp(), # unix timestamp
		"chats": {}
	}
	chats = datapack["chats"] # shorthand

	chatNo = 0
	messages = 0
	numOfPredatorMessages = 0
	predatorChats = 0

	# finding errors
	noChatID = 0
	noMessageLine = 0
	noAuthor = 0
	noTime = 0
	noBodyCount = 0
	errorMessages = 0

	dprint("parsing chat logs for %s…" % datapack["datapackID"])
	dprint("using %s dataset, from the file %s" % (datasetType, messageDatasetPath))
	dprint("and predIDsPath %s" % predIDsPath)

	logs = ET.parse('PAN12/raw_dataset/%s' % messageDatasetPath)
	logsRoot = logs.getroot()

	dprint("parsing predator list…")
	with open('PAN12/raw_dataset/%s' % predIDsPath) as file:
	    predatorList = [line.rstrip() for line in file]
	dprint("parsing done!")

	#	The xml file is organized as follows:
	#	<?xml version="1.0" encoding="UTF-8"?>
	#	<conversations>
	#	  <conversation id="id_of_the_conversation">
	#	    <message line="1">
	#	      <author>author_1_id</author>
	#	      <time>02:56</time>
	#	      <text>Bla bla bla bla</text>
	#	    </message>
	#	    <message line="2">
	#	      <author>author_2_id</author>
	#	      <time>02:56</time>
	#	      <text>bla bla</text>
	#	    </message>
	#	    [...]
	#	    <message line="n">
	#	      <author> author_1_id </author>
	#	      <time>07:12</time>
	#	      <text>bla bla bla</text>
	#	    </message>
	#	  </conversation>
	#	  [...]
	#	</conversations>

	for chatObj in logsRoot:
		chatNo += 1

		chatName = chatObj.get('id')
		if chatName == None: noChatID += 1 # TODO continue? does this happen?

		chat = {
			# "description": "Some comments about the chat",
			"hasErrors": False,
			"className": "non-predator", # gets set on demand
			"authorOnRightSide": None, # appears on the right side in visualizations
			# "predictedClassName": "negative",
			"isLabelled": False,
			"numOfNonemptyMessages": 0,
			"numOfPredatorMessages": 0,
			"numOfNonPredatorMessages": 0,
			"authors": set(),

			# This array stores different content types of the chat.
			# Currently there are
			# - messages (regular text messages) and
			# - separators (displayed as horizontal rules, e.g. to indicate
			#   time has passed between messages)
			# In the future, we might add other types of content like images
			# and voice messages.
			"content": DynamicArray()
		}


		# authorMessageNo = Counter()

		# find out the kind of chat we're in and keep statistics
		for messageObj in chatObj:
			messages += 1

			# get info
			author = messageObj.find("author")
			textNode = messageObj.find("text")
			timeNode = messageObj.find("time")
			lineNum = int(messageObj.get("line"))

			author = author.text if author != None else None
			if author is None: noAuthor += 1; continue # never happens
			else: chat["authors"].add(author)

			body = textNode.text if textNode is not None else None
			if body is None: noBodyCount += 1; continue

			time = timeNode.text if timeNode is not None else None
			if time is None: noTime += 1; continue # TODO really continue?
			time = datetime.strptime("1/1/1970 " + time, "%d/%m/%Y %H:%M")
			time = time.replace(tzinfo=timezone.utc) # make UTC because we don't know the time zone

			# process info

			body = bodyPreprocessing(body)

			# set className
			isFromPredator = author in predatorList
			if isFromPredator: chat["className"] = "predator"

			# set author on right side
			if chat["authorOnRightSide"] is None and not isFromPredator:
				chat["authorOnRightSide"] = author

			# keep track of number of messages per author
			# authorMessageNo.update([author])

			msg = {
				"type": "message",
				"author": author,
				"body": body,
				"time": time.timestamp()*1000, # unix timestamp
				"isFromPredator": isFromPredator,
				"labels": set(),

				# "prediction": 0.3256,
				# "labels": ["bar"],
				# "HTMLclassNames": ["warning"]

				"type": "message",
				"lineNum": lineNum,
			}

			# update message counts
			if isFromPredator: chat["numOfPredatorMessages"] += 1
			else: chat["numOfNonPredatorMessages"] += 1
			if isNonemptyMsg(msg): chat["numOfNonemptyMessages"] += 1

			chat["content"][lineNum-1] = msg

		if chat["className"] == "predator": predatorChats += 1

		# chat["lowMessagesPerUser"] = any(val < 6 for val in authorMessageNo.values())
		# listOfListsOfWords = [msg["body"].split() if msg and msg["body"] else []  for msg in chat["messages"]]
		# chat["noOfWords"] = len(list(chain(*listOfListsOfWords)))
		chats[chatName] = chat

	# Stats

	errorMessages = noChatID + noMessageLine + noAuthor + noTime + noBodyCount

	dprint("There are %s chats" % chatNo)
	dprint("There are %s messages (%s on average per chat)" % (
		messages, round(messages/chatNo)))

	dprint("There are %s predator chats (%s%% out of all chats)" % (
		predatorChats, round(predatorChats/chatNo*100, 2)))
	dprint("There are %s predator messages (%s%% out of all messages)" % (
		numOfPredatorMessages, round(numOfPredatorMessages/messages*100, 2)))

	dprint("There are %s error messages (%s%% out of all messages)" % (
		errorMessages, round(errorMessages/messages*100, 2)))
	dprint("Number of messages with \n    noChatID %s, noMessageLine %s, noAuthor %s, noTime %s, noBodyCount %s" % (noChatID, noMessageLine, noAuthor, noTime, noBodyCount))


	def datapackConverter(obj):
		if type(obj) == set: return list(obj)
		return getattr(obj, '__dict__', str(obj))
		# this also serializes DynamicArray to list

	print("dumping datapack…")

	outPath = "PAN12/datapacks/"
	Path(outPath).mkdir(parents=True, exist_ok=True)
	with open(outPath + "datapack-%s.json" % (datapack["datapackID"]), "w") as file:
		json.dump(datapack, file, default=datapackConverter)
	print("dumped chats.")

################################################################################

chatFiles = {
	"train": "pan12-sexual-predator-identification-training-corpus-2012-05-01.xml",
	"test": "pan12-sexual-predator-identification-test-corpus-2012-05-17.xml"
}
predatoryAuthorFiles = {
	"train": "pan12-sexual-predator-identification-training-corpus-predators-2012-05-01.txt",
	"test": "pan12-sexual-predator-identification-groundtruth-problem1.txt"
}

# test is bigger
for t in ["train", "test"]:
	processDataset(t, chatFiles[t], predatoryAuthorFiles[t])
