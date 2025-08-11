import datetime


class Record:
    time_start: datetime.datetime = None
    time_end: datetime.datetime = None

    def __init__(self):
        self.time_start = None
        self.time_end = None

    def start(self):
        self.time_start = datetime.datetime.now(datetime.timezone.utc)
        print(f"Recording started at {self.time_start}")

    def end(self):
        self.time_end = datetime.datetime.now(datetime.timezone.utc)
        print(f"Recording ended at {self.time_end}")

    def convert_to_json(self):
        return {
            "time_start": self.time_start.isoformat() if self.time_start else None,
            "time_end": self.time_end.isoformat() if self.time_end else None
        }
