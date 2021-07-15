import os
import sys
import subprocess
import mimetypes
# import speech_recognition
import google.cloud.storage
import google.cloud.speech

import _secrets as secrets

script_root = os.getcwd()

file_extension = sys.argv[1]
file_type = mimetypes.guess_type(f"_.{file_extension}")[0].split("/")[0]
sys.exit("unsupported file type") if not (file_type == "video" or file_type == "audio") else None
language_code = sys.argv[2]

storage_client = google.cloud.storage.Client.from_service_account_json(f"{script_root}/_gcp_service_acc_key.json")
bucket = storage_client.bucket(secrets.gcs_bucket_name)

speech_client = google.cloud.speech.SpeechClient.from_service_account_json(f"{script_root}/_gcp_service_acc_key.json")
stt_config = google.cloud.speech.RecognitionConfig(
	encoding = google.cloud.speech.RecognitionConfig.AudioEncoding.LINEAR16 if file_extension == "wav" else google.cloud.speech.RecognitionConfig.AudioEncoding.FLAC,
	sample_rate_hertz = None if (file_extension == "wav" or file_extension == "flac" or file_type == "video") else 16000,
	audio_channel_count = 1,
	max_alternatives = 1, # only highest confidence result
	language_code = language_code,
	profanity_filter = False,
	enable_automatic_punctuation = True,
	enable_word_time_offsets = False
)

for file in os.listdir(f"{script_root}/data"):
	if file.endswith(f".{file_extension}"):
		print(file)
		filepath = f"{script_root}/data/{file}"
		filename_no_ext = os.path.splitext(file)[0]

		audio_channels = -1
		if file_extension == "wav" or file_extension == "flac":
			try:
				audio_channels = int(subprocess.run(["ffprobe", "-i", f"{filepath}", "-show_entries", "stream=channels", "-select_streams", "a:0", "-of", "compact=p=0:nk=1", "-v", "0"], check=True, stdout=subprocess.PIPE, encoding="utf-8").stdout.split("\n")[0])
			except subprocess.CalledProcessError as err:
				sys.exit(err)

		stt_audio_path = f"{script_root}/data/{file}" if file_extension == "wav" else f"{script_root}/data/{filename_no_ext}.flac"

		created_new_file = False
		if not (file_extension == "wav" or file_extension == "flac") or audio_channels != 1:
			stt_audio_path = f"{script_root}/data/{filename_no_ext} (temp).flac"

			print("creating temp audio file")
			try:
				subprocess.run(["ffmpeg", "-i", filepath, "-ac", "1", stt_audio_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			except subprocess.CalledProcessError as err:
				sys.exit(err)
			print("created temp audio file")
			created_new_file = True

		# local method
		# recognizer = speech_recognition.Recognizer()
		# sra = speech_recognition.AudioFile(stt_audio_path)
		# with sra as source:
		# 	print("recording source")
		# 	audio = recognizer.record(source)
		# 	print("recorded source")
		# 	try:
		# 		print("sphinx start")
		# 		text = recognizer.recognize_sphinx(audio, language="en-US") # freezes for large files
		# 		print("sphinx end")

		# 		print("writing transcript to txt file")
		# 		open(f"{script_root}/data/{filename_no_ext}.txt", "w").write(f"{text}\n")
		# 		print("written transcript to txt file")
		# 	except speech_recognition.UnknownValueError as err:
		# 		print(f"could not understand speech: {err}")
		# 	except speech_recognition.RequestError as err:
		# 		print(f"request error: {err}")
		# 	except Exception as err:
		# 		print(err)

		# google method
		try:
			blob = bucket.blob(file)
			print("uploading audio file to gcs")
			blob.upload_from_filename(stt_audio_path)
			print("uploaded audio file to gcs")

			audio = google.cloud.speech.RecognitionAudio(uri=f"gs://{secrets.gcs_bucket_name}/{file}")
			print("starting stt")
			operation = speech_client.long_running_recognize(audio=audio, config=stt_config)
			response = operation.result()
			print("finished stt")

			transcript = ""
			for result in response.results:
				print(result.alternatives[0].confidence)
				transcript += result.alternatives[0].transcript

			print("writing transcript to txt file")
			open(f"{script_root}/data/{filename_no_ext}.txt", "w").write(f"{transcript}\n")
			print("written transcript to txt file")

			print("deleting audio file from gcs")
			blob.delete()
			print("deleted audio file from gcs")
		except Exception as err:
			sys.exit(err)
		
		if created_new_file:
			print(f"deleting temp audio file")
			os.remove(stt_audio_path)
			print(f"deleted temp audio file")

		print()
