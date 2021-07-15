import os
import sys

script_root = os.getcwd()

flag = sys.argv[1]

if flag == "-c": # combine
	import pdfrw

	writer = pdfrw.PdfWriter()

	for file in os.listdir(f"{script_root}/data"):
		if file.endswith(".pdf"):
			print(file)
			pdf_path = f"{script_root}/data/{file}"
			writer.addpages(pdfrw.PdfReader(pdf_path).pages)

	writer.trailer.Info = pdfrw.IndirectPdfDict(Title="")
	writer.write(f"{script_root}/data/# out.pdf")
elif flag == "-o": # ocr
	import ocrmypdf

	for file in os.listdir(f"{script_root}/data"):
		if file.endswith(".pdf"):
			print(file)
			pdf_path = f"{script_root}/data/{file}"

			pid = os.fork()
			if pid > 0: # parent process
				os.waitpid(pid, 0) # wait for child process to end
			elif pid == 0: # child process
				ocrmypdf.ocr(input_file=pdf_path, output_file=f"{os.path.splitext(ppt_path)[0]} (ocr).pdf", force_ocr=True, output_type="pdf", language="eng")
				os._exit(0)
elif flag == "-p": # ppt
	import comtypes.client

	powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
	powerpoint.Visible = 1

	for file in os.listdir(f"{script_root}/data"):
		if file.endswith(".ppt") or file.endswith(".pptx"):
			print(file)
			ppt_path = f"{script_root}/data/{file}"
			deck = powerpoint.Presentations.Open(ppt_path)
			deck.SaveAs(f"{os.path.splitext(ppt_path)[0]}.pdf", 32) # https://docs.microsoft.com/en-us/office/vba/api/powerpoint.ppsaveasfiletype "ppSaveAsPDF"
			deck.Close()
			
	powerpoint.Quit()
else:
	print("invalid args")
