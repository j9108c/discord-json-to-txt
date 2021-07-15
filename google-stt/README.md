# google-stt
speech to text from video or audio files using ffmpeg and Google Cloud Platform
<br/>
<br/>
- per-file length limit: [8h](https://cloud.google.com/speech-to-text/quotas "Asynchronous Requests")
- command: <python script.py {file extension} {language code}>
	- file extensions: "wav", "mp3", "mp4", etc
	- language codes: "en-US", "en-GB", "en-CA", "en-HK", [etc](https://cloud.google.com/speech-to-text/docs/languages "BCP-47")
