# storage.py
import json
import os
from typing import Dict

DAILY_GIVEAWAYS_FILE = "daily_giveaways.json"

class DailyGiveawayData:
    def __init__(self, prize: str, duration_seconds: int, winners_count: int, 
                 channel_id: int, next_run: str):
        self.prize = prize
        self.duration_seconds = duration_seconds
        self.winners_count = winners_count
        self.channel_id = channel_id
        self.next_run = next_run
    
    def to_dict(self) -> dict:
        return {
            "prize": self.prize,
            "duration_seconds": self.duration_seconds,
            "winners_count": self.winners_count,
            "channel_id": self.channel_id,
            "next_run": self.next_run
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'DailyGiveawayData':
        return DailyGiveawayData(
            prize=data["prize"],
            duration_seconds=data["duration_seconds"],
            winners_count=data["winners_count"],
            channel_id=data["channel_id"],
            next_run=data["next_run"]
        )

def load_daily_giveaways() -> Dict[str, DailyGiveawayData]:
    """Load daily giveaways from file"""
    if not os.path.exists(DAILY_GIVEAWAYS_FILE):
        return {}
    
    with open(DAILY_GIVEAWAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {g_id: DailyGiveawayData.from_dict(g_data) for g_id, g_data in data.items()}

def save_daily_giveaways(giveaways: Dict[str, DailyGiveawayData]):
    """Save daily giveaways to file"""
    data = {g_id: g_data.to_dict() for g_id, g_data in giveaways.items()}
    with open(DAILY_GIVEAWAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)