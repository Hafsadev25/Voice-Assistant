# Python Voice Assistant

A Python voice assistant that listens to spoken audio commands, performs actions, and speaks back responses.

## Privacy & Security Considerations

This project adheres to strict local-first data processing guidelines:

1. **Audio Capture**: Microphones capture audio strictly during an active session when listening for commands.
2. **Speech Processing**: Transcripts are passed securely to Google Speech Recognition over standard HTTPS GET/POST requests and are not stored permanently by the local assistant.
3. **Local Natural Language Processing**: Intent classification, phrase tokenization via `nltk`, custom commands, and QA logic run entirely on your local CPU.
4. **Credential Isolation**: SMTP email app passwords and API keys are stored locally in variable configs and are never transmitted to third parties beyond standard API endpoints (`api.openweathermap.org` & `smtp.gmail.com`).
