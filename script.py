import os
import json

project_root = os.getcwd()

with open(f"{project_root}/# input.json") as input_json_file:
	data = json.load(input_json_file)

	with open(f"{project_root}/# output.txt", "w") as output_txt_file:
		for message in data["messages"]:
			fixed_msg = message["content"].replace("\n", ". ")
			output_txt_file.write(f"- {fixed_msg}\n")
