import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
# to be able to import modules from parent directory
import argparse
import os
import json
from util import getUNIXTimestamp
from pathlib import Path

parser = argparse.ArgumentParser(description='Evaluate a model')
parser.add_argument(
	"--datapackID",
	dest='datapackID',
	help="the unique identifier that the datapack is going to have",
	default="VTPAN"
)
parser.add_argument(
	"--PAN12datapackID",
	dest='PAN12datapackID',
	help="path of the PAN12 datapack to use",
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
print()

currentDir = os.path.dirname(os.path.abspath(__file__))

VTPAN_ID_paths = {
	"train": os.path.join(currentDir, "VTPAN_train_IDs.txt"),
	"test": os.path.join(currentDir, "VTPAN_test_IDs.txt")
}
VTPAN_IDs = {
	"train": [],
	"test": []
}

# read IDs from file
for datasetType in ["train", "test"]:
	with open(VTPAN_ID_paths[datasetType]) as file:
		IDs = [line.strip() for line in file.readlines()]
	VTPAN_IDs[datasetType] = IDs

# if chatName not in VTPAN_IDs[datasetType]: continue
# if datasetType == "test" and chatName not in VTPAN_IDs["test"]: continue
# if datasetType == "train" and chatName not in VTPAN_IDs["train"]: continue

print("len(VTPAN_IDs['train']) = %s" % (len(VTPAN_IDs['train'])))
print("len(VTPAN_IDs['test']) = %s" % (len(VTPAN_IDs['test'])))

def generateDatapack(PAN12datapack, datasetType):
	datapack = PAN12datapack

	# set metadata
	datapack["datapackID"] = "%s-%s" % (args.datapackID, datasetType)
	datapack["description"] = args.description
	datapack["generatedAtTime"] = getUNIXTimestamp() # unix timestamp

	# filter chats from datapack that are not in VTPAN
	for chatName in list(datapack["chats"].keys()):
		if chatName not in VTPAN_IDs[datasetType]:
			del datapack["chats"][chatName]

	return datapack

for datasetType in ["train", "test"]:
	path = os.path.join(currentDir, "../PAN12/datapacks/")
	with open(path + "datapack-%s-%s.json" %
			(args.PAN12datapackID, datasetType), "r") as file:
		PAN12datapack = json.load(file)
		datapack = generateDatapack(PAN12datapack, datasetType)
		print("len(datapack['chats']) = %s" % len(datapack['chats']))
		assert len(set(VTPAN_IDs[datasetType])-set(datapack['chats'].keys())) = 0
		# dump generated datapack to json file
		Path(currentDir + "/datapacks/").mkdir(parents=True, exist_ok=True)
		outputFile = os.path.join(currentDir, "datapacks/datapack-%s-%s.json" %
			(args.datapackID, datasetType))
		with open(outputFile, "w") as file:
			json.dump(datapack, file)
