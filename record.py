import time

class Record:
    # log time spent playing
    # log time start
    # log time end

    time_spent = 0
    time_start = 0
    time_end = 0
    def __init__(self):
        self.time_spent = 0
        self.time_start = 0
        self.time_end = 0

    def start(self):
        self.time_start = time.perf_counter()
        print(f"Recording started at {self.time_start}")

    def end(self):
        self.time_end = time.perf_counter()
        print(f"Recording ended at {self.time_end}")
        self.time_spent = self.time_end - self.time_start
        print(f"Total time spent: {self.time_spent:.2f} seconds")

    def convert_to_json(self):
        return {
            "time_spent": self.time_spent,
            "time_start": self.time_start,
            "time_end": self.time_end
        }