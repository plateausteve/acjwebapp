#! /usr/local/bin/python3.8

import os, pandas

csv = pandas.read_csv("/path/to/csv/file but I don't know it")

root = "/home/drawingtest/acjwebapp/acjapp/media/" # won't work for local testing, it'd be dangerous to try in deployment
directory = os.path.join(root, "scripts/pdfs")
os.chdir(directory)
for file in os.listdir("."):


# check what's in the pdfs folder



# for each row of the csv:
	# check if it's in the folder
	# check if there's a script with that id
		# if not, make one for it (how though?)
		# what information is required here?

# for everything that's new (name doesn't match DB entry?) create a new item for it