# models.py
from datetime import datetime
from typing import List

class Giveaway:
    def __init__(self, giveaway_id: str, channel_id: int, message_id: int, prize: str, 
                 winners_count: int, end_time: datetime, is_daily: bool = False):
        self.giveaway_id = giveaway_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.prize = prize
        self.winners_count = winners_count
        self.end_time = end_time
        self.is_daily = is_daily
        self.participants: List[int] = []
        self.ended = False

class DailyGiveawayData:
    def __init__(self, prize: str, duration_seconds: int, winners_count: int, channel_id: int, next_run: str):
        self.prize = prize
        self.duration_seconds = duration_seconds
        self.winners_count = winners_count
        self.channel_id = channel_id
        self.next_run = next_run
    
    def to_dict(self):
        return {
            "prize": self.prize,
            "duration_seconds": self.duration_seconds,
            "winners_count": self.winners_count,
            "channel_id": self.channel_id,
            "next_run": self.next_run
        }
    
    @staticmethod
    def from_dict(data: dict):
        return DailyGiveawayData(
            prize=data["prize"],
            duration_seconds=data["duration_seconds"],
            winners_count=data["winners_count"],
            channel_id=data["channel_id"],
            next_run=data["next_run"]
        )