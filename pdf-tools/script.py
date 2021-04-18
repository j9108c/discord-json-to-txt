import os
import sys
import pdfrw
import ocrmypdf

project_root = os.getcwd()
out_path = f"{project_root}/# output.pdf"

combined = False

if ("-c" in sys.argv[1:]): # combine flag
	writer = pdfrw.PdfWriter()

	for file in os.listdir(project_root):
		if (file.endswith(".pdf")):
			pdf_path = f"{project_root}/{file}"
			writer.addpages(pdfrw.PdfReader(pdf_path).pages)

	writer.trailer.Info = pdfrw.IndirectPdfDict(Title="")
	writer.write(out_path)
	combined = True

if ("-o" in sys.argv[1:]): # ocr flag
	in_path = None
	if (combined):
		in_path = out_path
	else:
		for file in os.listdir(project_root):
			if (file.endswith(".pdf")):
				in_path = f"{project_root}/{file}"
				break

	pid = os.fork()
	if (pid > 0): # parent process
		os.waitpid(pid, 0) # wait for child process to end
	elif (pid == 0): # child process
		ocrmypdf.ocr(input_file=in_path, output_file=out_path, force_ocr=True, output_type="pdf", language="eng")
		os._exit(0)
