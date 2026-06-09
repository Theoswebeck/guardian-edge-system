import sys
sys.path.insert(0, "..") # to be able to import modules from parent directory
from collections import Counter
import argparse
import numpy as np
import json
from util import getSegments
from pathlib import Path
from util import isGood, isNonemptyMsg

parser = argparse.ArgumentParser(description='Create a tsv dataset from a datapack')
parser.add_argument(
	"--dataset",
	dest='dataset',
	help="from which dataset the datapack is",
	required=True
)
parser.add_argument(
	"--datapackID",
	dest='datapackID',
	help="the unique identifier that the datapack is going to have"
)
args = parser.parse_args()
if args.datapackID is None: args.datapackID = args.dataset

print("\n---           Arguments           ---")
for key, val in args.__dict__.items(): print("%20s: %s" % (key, val))
print()

# will be aggregated

globalSegmentLengths = {"predator": [], "non-predator": []}
globalSegmentLengthsWords = {"predator": [], "non-predator": []}
globalPredatorChatLengths = []
globalPredatorChatLengthsWords = []
global20GroomingMessages = []

def getStatistics(datapack, datasetType):
	global globalPredatorChatLengths, globalSegmentLengths, globalPredatorChatLengthsWords, globalSegmentLengthsWords, global20GroomingMessages
	segmentLengths = {"predator": [], "non-predator": []}
	segmentLengthsWords = {"predator": [], "non-predator": []}
	predatorChatLengths = []
	predatorChatLengthsWords = []

	chatClassCount = Counter()
	segmentClassCount = Counter()
	for chatName, chat in datapack["chats"].items():
		chatClassCount.update([chat["className"]])
		if chat["className"] == "predator":
			# stats for full length predator chats
			nonemptyMessages = [msg for msg in chat["content"] if isNonemptyMsg(msg)]

			# length in messages
			length = len(nonemptyMessages)
			predatorChatLengths.append(length)
			globalPredatorChatLengths.append(length)

			# length in words
			lengthWords = sum([len(msg["body"].split()) for msg in nonemptyMessages])
			predatorChatLengthsWords.append(lengthWords)
			globalPredatorChatLengthsWords.append(lengthWords)

			if sum(["G" in msg["labels"] for msg in nonemptyMessages]) >= 20:
				j = 0
				for i, msg in enumerate(nonemptyMessages):
					if "G" in msg["labels"]:
						global20GroomingMessages.append(i)
						j += 1
						if j == 20: break

		for i, segment in enumerate(getSegments(chat)):
			if not isGood(segment, args.dataset): continue
			# stats for (non-)predator segments

			segmentClassCount.update([chat["className"]])
			nonemptyMessages = [msg for msg in segment if isNonemptyMsg(msg)]

			# length in messages
			length = len(nonemptyMessages)
			segmentLengths[chat["className"]].append(length)
			globalSegmentLengths[chat["className"]].append(length)

			# length in words
			lengthWords = sum([len(msg["body"].split()) for msg in nonemptyMessages])
			segmentLengthsWords[chat["className"]].append(lengthWords)
			globalSegmentLengthsWords[chat["className"]].append(lengthWords)

	print("In %s:" % datasetType)
	total = segmentClassCount["predator"] + segmentClassCount["non-predator"]
	print("\tnumber of segments: %s" % total)
	print("\tchatClassCount = %s" % chatClassCount)
	print("\tsegmentClassCount = %s" % segmentClassCount)
	print("\tpredator class ratio: predator/all = %s/%s = %s%%" % (
		segmentClassCount["predator"], total,
		np.round(segmentClassCount["predator"]/total*100, 2)
	))
	print("\tSplit segment lengths in messages:")
	print('\tnp.mean(segmentLengths["predator"]) = %s' % np.mean(segmentLengths["predator"]))
	print('\tnp.std(segmentLengths["predator"]) = %s' % np.std(segmentLengths["predator"]))
	print('\tnp.mean(segmentLengths["non-predator"]) = %s' % np.mean(segmentLengths["non-predator"]))
	print('\tnp.std(segmentLengths["non-predator"]) = %s' % np.std(segmentLengths["non-predator"]))
	print('\tnp.mean(predatorChatLengths) = %s' % np.mean(predatorChatLengths))
	print('\tnp.std(predatorChatLengths) = %s' % np.std(predatorChatLengths))

	print("\tSplit segment lengths in words:")
	print('\tnp.mean(segmentLengthsWords["predator"]) = %s' % np.mean(segmentLengthsWords["predator"]))
	print('\tnp.std(segmentLengthsWords["predator"]) = %s' % np.std(segmentLengthsWords["predator"]))
	print('\tnp.mean(segmentLengthsWords["non-predator"]) = %s' % np.mean(segmentLengthsWords["non-predator"]))
	print('\tnp.std(segmentLengthsWords["non-predator"]) = %s' % np.std(segmentLengthsWords["non-predator"]))
	print('\tnp.mean(predatorChatLengthsWords) = %s' % np.mean(predatorChatLengthsWords))
	print('\tnp.std(predatorChatLengthsWords) = %s' % np.std(predatorChatLengthsWords))

	print('\n\tnp.median(globalPredatorChatLengths) = %s' % np.median(globalPredatorChatLengths))


for datasetType in ["train", "test"]:
	datapackPath = "%s/datapacks/datapack-%s-%s.json" % (
		args.dataset, args.datapackID, datasetType)
	csvPath = "%s/csv/%s-%s.csv" % (
		args.dataset, args.datapackID, datasetType)
	with open(datapackPath, "r") as file:
		datapack = json.load(file)

		getStatistics(datapack, datasetType)

print("Global segment lengths in messages:")
print('np.mean(globalSegmentLengths["predator"]) = %s' % np.mean(globalSegmentLengths["predator"]))
print('np.std(globalSegmentLengths["predator"]) = %s' % np.std(globalSegmentLengths["predator"]))
print('np.mean(globalSegmentLengths["non-predator"]) = %s' % np.mean(globalSegmentLengths["non-predator"]))
print('np.std(globalSegmentLengths["non-predator"]) = %s' % np.std(globalSegmentLengths["non-predator"]))
print('np.mean(globalPredatorChatLengths) = %s' % np.mean(globalPredatorChatLengths))
print('np.std(globalPredatorChatLengths) = %s' % np.std(globalPredatorChatLengths))

print("Global segment lengths in words:")
print('np.mean(globalSegmentLengthsWords["predator"]) = %s' % np.mean(globalSegmentLengthsWords["predator"]))
print('np.std(globalSegmentLengthsWords["predator"]) = %s' % np.std(globalSegmentLengthsWords["predator"]))
print('np.mean(globalSegmentLengthsWords["non-predator"]) = %s' % np.mean(globalSegmentLengthsWords["non-predator"]))
print('np.std(globalSegmentLengthsWords["non-predator"]) = %s' % np.std(globalSegmentLengthsWords["non-predator"]))
print('np.mean(globalPredatorChatLengthsWords) = %s' % np.mean(globalPredatorChatLengthsWords))
print('np.std(globalPredatorChatLengthsWords) = %s' % np.std(globalPredatorChatLengthsWords))

print('\nnp.median(globalPredatorChatLengths) = %s' % np.median(globalPredatorChatLengths))

# save segment lengths to file
outPath = "%s/statistics/" % args.dataset
Path(outPath).mkdir(parents=True, exist_ok=True)
with open(outPath + "segment-lengths-%s.json" % args.datapackID, "w") as file:
	json.dump(globalSegmentLengths, file)

allSegmentLengths = globalSegmentLengths["predator"] + globalSegmentLengths["non-predator"]
medianSegmentLength = np.median(allSegmentLengths)
print("overall medianSegmentLength = %s" % medianSegmentLength)
print("np.median(global20GroomingMessages) = %s" % np.median(global20GroomingMessages))
print("np.mean(global20GroomingMessages) = %s" % np.mean(global20GroomingMessages))
