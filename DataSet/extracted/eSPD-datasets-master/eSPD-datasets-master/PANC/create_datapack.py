import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
# to be able to import modules from parent directory
import argparse
import os
from util import getUNIXTimestamp
import json
import random
from util import PANC_MIN_MSG_NUM, PANC_MAX_MSG_NUM
from pathlib import Path

parser = argparse.ArgumentParser(description='Evaluate a model')
parser.add_argument(
	"--datapackID",
	dest='datapackID',
	help="the unique identifier that the datapack is going to have",
	default="PANC"
)
parser.add_argument(
	"--PAN12datapackID",
	dest='PAN12datapackID',
	help="ID of the PAN12 datapack to use",
	default="PAN12"
)
parser.add_argument(
	"--CC2datapackID",
	dest='CC2datapackID',
	help="ID of the ChatCoder2 datapack to use",
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

currentDir = os.path.dirname(os.path.abspath(__file__))

# 1. get negative PAN12 segments
print("1. get negative PAN12 segments")

negativeChats = {}
for datasetType in ["train", "test"]:
	path = os.path.join(currentDir, "../PAN12/datapacks/")
	with open(path + "datapack-%s-%s.json" %
			(args.PAN12datapackID, datasetType), "r") as file:
		PAN12datapack = json.load(file)
		for chatName, chat in PAN12datapack["chats"].items():
			if chat["className"] == "non-predator":
				negativeChats[chatName] = chat

# 2. filter negative PAN12 segments
print("2. filter negative PAN12 segments")

for chatName, chat in list(negativeChats.items()):
	# The PAN12 organizers said there would be no segments longer than 150
	# messages, but actually there are. We will filter these for segment
	# comparability. We also filter empty segments.
	hasBadNumOfMessages = \
		not (PANC_MIN_MSG_NUM <= chat["numOfNonemptyMessages"] <= PANC_MAX_MSG_NUM)
	doesNotHaveTwoAuthors = len(chat["authors"]) != 2
	if hasBadNumOfMessages or doesNotHaveTwoAuthors:
		del negativeChats[chatName]; continue

	# string = contentToString(chat["content"])
	# if len(string) > 12970: # is spam
		# del negativeChats[chatName]; continue

# 3. get complete positive ChatCoder2 chats
print("3. get complete positive ChatCoder2 chats")

postiveChats = {}
path = "ChatCoder2/datapacks/datapack-%s.json" % args.CC2datapackID
with open(path, "r") as file:
	CC2Datapack = json.load(file)
	positiveChats = CC2Datapack["chats"]
	# These are complete chats. We HAVE to make sure, that the segments in the
	# complete chats which have >150 messages or <6 are NOT used for training or
	# evaluation! We have to make sure that they are filtered in create_csv.py
	# and in the evaluation scripts. Nevertheless, we include them in the
	# datapack to be able to evaluate with complete positive chats.

# have all chats
chats = {**positiveChats, **negativeChats}

# 4. generate train and test sets
print("4. generate train and test sets")

random.seed(10) # set seed
positiveChatNames = sorted(positiveChats.keys())
negativeChatNames = sorted(negativeChats.keys())
random.shuffle(positiveChatNames)
random.shuffle(negativeChatNames)

trainTestRatio = .6
posSplitIndex = int(len(positiveChats)*trainTestRatio)
negSplitIndex = int(len(negativeChats)*trainTestRatio)

chatNames = {
	"train": positiveChatNames[:posSplitIndex] + negativeChatNames[:negSplitIndex],
	"test": positiveChatNames[posSplitIndex:] + negativeChatNames[negSplitIndex:]
}

def generateDatapack(datasetType):
	datapack = {
		"datapackID": args.datapackID + "-" + datasetType,
		"description": args.description,
		"generatedAtTime": getUNIXTimestamp(),
		"chats": {}
	}

	# filter chats for train/test set
	datasetTypeChats = set(chats.keys()).intersection(chatNames[datasetType])
	for chatName in datasetTypeChats:
		datapack["chats"][chatName] = chats[chatName]

	return datapack

# 5. generate and dump PANC datapack
print("5. generate and dump PANC datapack")

for datasetType in ["train", "test"]:
	datapack = generateDatapack(datasetType)
	print("%s: len(datapack['chats']) = %s" % (datasetType, len(datapack['chats'])))

	# dump generated datapack to json file
	path = os.path.join(currentDir, "datapacks/")
	Path(path).mkdir(parents=True, exist_ok=True)
	with open(path + "datapack-%s-%s.json" %
			(args.datapackID, datasetType), "w") as file:
		json.dump(datapack, file)

# also dump an info file for development
infoFile = "PANC/datapacks/datapack-info-%s.json" % (args.datapackID)
with open(infoFile, "w") as file: json.dump(chatNames, file, indent=4)
