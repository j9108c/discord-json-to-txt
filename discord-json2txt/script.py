import os
import json

script_root = os.getcwd()

input = json.load(open(f"{script_root}/data/# in.json", "r"))
output = open(f"{script_root}/data/# out.txt", "w")

for msg in input["messages"]:
	fixed_msg = msg["content"].replace("\n", ". ")
	output.write(f"- {fixed_msg}\n")

output.close()
