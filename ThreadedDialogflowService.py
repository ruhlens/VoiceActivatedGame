from threading import Thread
from threading import Semaphore
from DialogflowService import DialogflowService
'''
ThreadedDialogFlowService class.
This class assigns microphone input handling to a thread
*This allows for the microphone to constantly listen for voice input
Author: Dr. Isaac Wang
'''

class ThreadedDialogflowService(object):
    def __init__(self, project_name):
        self.service = DialogflowService(project_name)
        self.result = None
        self.wait_for_result = Semaphore()
        self.thread = Thread(target=ThreadedDialogflowService.thread_func, args=(self,))
        self.running = False

    def request(self):
        if not self.running:
            self.wait_for_result.acquire()
            self.running = True
            self.thread.start()
        result = self.result
        if result is not None:
            self.wait_for_result.release()
            self.result = None
        return result

    def stop(self):
        self.service.close()
        self.wait_for_result.release()
        self.thread.join(1)

    def thread_func(self):
        for x in self.service.generator():
            self.result = x
            self.wait_for_result.acquire()

def sample_code():
    service = ThreadedDialogflowService('PROJECT_NAME')
    while True:  # Pretend this is your pygame loop
        response = service.request()
        if response is not None:
            start_time, end_time, result = response  # Unpack the response
            intent = result.intent.display_name
            # do something with the intent here
        # continue doing pygame things
