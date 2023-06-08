from google.cloud import dialogflow
import pyaudio
import random
from queue import Queue
from datetime import datetime
import os
'''
Microphone stream class.
This class handles microphone input.
Author: Dr. Isaac Wang
'''

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 5)


class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except Exception:
                    break

            yield b''.join(data)


class DialogflowService(object):
    def __init__(self, project_id, session_id=None, rate=RATE, chunk_size=CHUNK, lang='en-US'):
        self.project_id = project_id
        self.session_id = session_id
        self.rate = rate
        self.chunk_size = chunk_size
        self.lang = lang

        # Generate session id if needed
        if self.session_id is None:
            self.session_id = random.randint(0, 10000)

        # Init microphone stream
        self.mic_stream = MicrophoneStream(self.rate, self.chunk_size)
        self.mic_stream.__enter__()

        # Init Dialogflow session
        self.session_client = dialogflow.SessionsClient()
        self.session = self.session_client.session_path(self.project_id, self.session_id)

        # Init Dialogflow configuration
        audio_config = dialogflow.InputAudioConfig(
            audio_encoding=dialogflow.AudioEncoding.AUDIO_ENCODING_LINEAR_16,
            language_code=self.lang,
            sample_rate_hertz=self.rate
        )
        self.query_input = dialogflow.QueryInput(audio_config=audio_config)

        self.running = False

    def __request_generator(self, audio_generator):
        # The first request contains the configuration.
        yield dialogflow.StreamingDetectIntentRequest(session=self.session, query_input=self.query_input, single_utterance=True)

        # Continually send chunks of mic stream data to the server
        for chunk in audio_generator:
            yield dialogflow.StreamingDetectIntentRequest(input_audio=chunk)

    def generator(self):
        """Returns query_results from continous Dialogflow recognition."""

        self.running = True

        # Continuously send audio to the server
        while self.running:
            self.mic_stream.closed = False  # Resume streaming audio
            requests = self.__request_generator(self.mic_stream.generator())  # Must get new generator every time if it is closed
            responses = self.session_client.streaming_detect_intent(requests)

            # Cached final result
            final_result = None
            start_time = None
            end_time = None

            try:
                for response in responses:
                    # Cache start time (first utterance from user)
                    if start_time is None:
                        start_time = datetime.now()

                    # Cache intent result
                    if response.query_result.intent.display_name:
                        final_result = response.query_result

                    if response.recognition_result.message_type == dialogflow.StreamingRecognitionResult.MessageType.END_OF_SINGLE_UTTERANCE:
                        self.mic_stream.closed = True  # Stop streaming audio; requests will stop sending

                        # Set the end time for the utterance
                        if end_time is None:
                            end_time = datetime.now()
            except Exception as ex:
                # Just in case the server decides to drop the connection early
                #print(ex)
                pass

            # Yield cached result
            if final_result is not None:
                # Just in case: set the end timestamp
                if end_time is None:
                    end_time = datetime.now()

                yield (start_time, end_time, final_result)

    def close(self):
        self.mic_stream.closed = True  # Will stop the mic streaming
        self.running = False  # Will stop the generator

        self.mic_stream.__exit__(None, None, None)





def test_service():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'keysFile.json'

    service = DialogflowService('voiceactivatedgame')
    query_results = service.generator()
    print('-' * 20)

    # Start processing results
    try:
        #"""
        for start_time, end_time, result in query_results:
            intent = result.intent.display_name
            print('Transcript: {}'.format(result.query_text))
            print('Detected intent: {}'.format(intent))
        """
        while True:
            start_time, end_time, result = next(query_results)  # Call me to start streaming audio until an intent is returned
            intent = result.intent.display_name
            print('Transcript: {}'.format(result.query_text))
            print('Detected intent: {}'.format(intent))
        #"""

    except KeyboardInterrupt:
        print('-' * 20)
        print('Closing Dialogflow service...')
        service.close()  # Safely close Dialogflow service
        print('Done.')


if __name__ == '__main__':
    test_service()
