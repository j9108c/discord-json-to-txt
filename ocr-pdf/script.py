import os
import ocrmypdf

project_root = os.getcwd()

input = f"{project_root}/# input.pdf"
output = f"{project_root}/# output.pdf"

pid = os.fork()
if (pid > 0): # parent process
	os.waitpid(pid, 0) # wait for child process to end
elif (pid == 0): # child process
	ocrmypdf.ocr(input, output, force_ocr=True, language="eng") # output pdf is PDF/A compliant
	os._exit(0)
