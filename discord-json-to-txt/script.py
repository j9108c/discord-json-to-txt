import os
import json

project_root = os.getcwd()

input = json.load(open(f"{project_root}/# input.json", "r"))
output = open(f"{project_root}/# output.txt", "w")

for message in input["messages"]:
	fixed_msg = message["content"].replace("\n", ". ")
	output.write(f"- {fixed_msg}\n")