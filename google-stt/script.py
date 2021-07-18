import os
import sys
import subprocess
import mimetypes
import time
import functools
# import speech_recognition
import google.cloud.storage
import google.cloud.speech

import _secrets as secrets

def ffprobe(filepath, stream):
	return subprocess.run(["ffprobe", "-i", filepath, "-show_entries", f"stream={stream}", "-select_streams", "a:0", "-of", "compact=p=0:nk=1", "-v", "0"], check=True, stdout=subprocess.PIPE, encoding="utf-8")

def ffmpeg(filepath, stt_audio_path, sample_rate=None):
	if sample_rate:
		subprocess.run(["ffmpeg", "-i", filepath, "-ar", str(sample_rate), "-ac", "1", stt_audio_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	else:
		subprocess.run(["ffmpeg", "-i", filepath, "-ac", "1", stt_audio_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stt_callback(future, script_root, file, filename_no_ext, blob, created_new_file, stt_audio_path):
	print(f"({file}) finished stt")
	response = future.result()

	transcript = ""
	confidences = []
	for result in response.results:
		transcript += result.alternatives[0].transcript
		confidences.append(str(result.alternatives[0].confidence))

	print(f"({file}) confidences ({', '.join(confidences)})")

	print(f"({file}) writing transcript to txt file")
	open(f"{script_root}/data/{filename_no_ext}.txt", "w").write(f"{transcript}\n")
	print(f"({file}) written transcript to txt file")

	print(f"({file}) deleting audio file from gcs")
	blob.delete()
	print(f"({file}) deleted audio file from gcs")

	if created_new_file:
		print(f"({file}) deleting temp audio file")
		os.remove(stt_audio_path)
		print(f"({file}) deleted temp audio file")

if __name__ == "__main__":
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
		sample_rate_hertz = None if (file_extension == "wav" or file_extension == "flac" or file_type == "video") else 16000, # 8000−48000 supported (https://cloud.google.com/speech-to-text/docs/basics#sample-rates)
		audio_channel_count = 1,
		max_alternatives = 1, # only highest confidence result
		language_code = language_code,
		profanity_filter = False,
		enable_automatic_punctuation = True,
		enable_word_time_offsets = False
	)

	stt_operations = []

	for file in os.listdir(f"{script_root}/data"):
		if file.endswith(f".{file_extension}"):
			filepath = f"{script_root}/data/{file}"
			filename_no_ext = os.path.splitext(file)[0]

			audio_sample_rate = None
			audio_channels = None
			try:
				audio_sample_rate = int(ffprobe(filepath, "sample_rate").stdout.split("\n")[0])
				audio_channels = int(ffprobe(filepath, "channels").stdout.split("\n")[0])
			except subprocess.CalledProcessError as err:
				sys.exit(err)

			stt_audio_path = None
			created_new_file = False
			if not (file_extension == "wav" or file_extension == "flac") or not (audio_sample_rate >= 8000 and audio_sample_rate <= 48000) or audio_channels != 1:
				stt_audio_path = f"{script_root}/data/{filename_no_ext} (temp).flac"

				print(f"({file}) creating temp audio file")
				try:
					if audio_sample_rate >= 16000:
						ffmpeg(filepath, stt_audio_path, 16000)
						stt_config.sample_rate_hertz = 16000
					elif audio_sample_rate >= 8000:
						ffmpeg(filepath, stt_audio_path)
						stt_config.sample_rate_hertz = audio_sample_rate
					else:
						ffmpeg(filepath, stt_audio_path, 8000)
						stt_config.sample_rate_hertz = 8000
				except subprocess.CalledProcessError as err:
					sys.exit(err)
				print(f"({file}) created temp audio file")
				created_new_file = True
			else:
				stt_audio_path = filepath
				stt_config.sample_rate_hertz = audio_sample_rate

			stt_audio_filename = os.path.splitext(stt_audio_path)[0].split("/")[-1] + os.path.splitext(stt_audio_path)[1]

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
				blob = bucket.blob(stt_audio_filename)
				print(f"({file}) uploading audio file to gcs")
				blob.upload_from_filename(stt_audio_path)
				print(f"({file}) uploaded audio file to gcs")

				audio = google.cloud.speech.RecognitionAudio(uri=f"gs://{secrets.gcs_bucket_name}/{stt_audio_filename}")
				print(f"({file}) starting stt")
				stt_operation = speech_client.long_running_recognize(audio=audio, config=stt_config)
				stt_operation.add_done_callback(functools.partial(stt_callback, script_root=script_root, file=file, filename_no_ext=filename_no_ext, blob=blob, created_new_file=created_new_file, stt_audio_path=stt_audio_path))
				stt_operations.append(stt_operation)
			except Exception as err:
				sys.exit(err)

	while not all([operation.done() for operation in stt_operations]):
		time.sleep(1)

	print("completed with no errors")
