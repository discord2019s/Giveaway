# giveaway_state.py
# Dictionary to store active giveaways
active_giveaways = {}
winner_active_giveaways = {}

def register_giveaway(message_id: int, giveaway_view, is_winner: bool = False):
    """Register an active giveaway"""
    if is_winner:
        winner_active_giveaways[message_id] = giveaway_view
    else:
        active_giveaways[message_id] = giveaway_view

def unregister_giveaway(message_id: int, is_winner: bool = False):
    """Unregister a giveaway"""
    if is_winner:
        if message_id in winner_active_giveaways:
            del winner_active_giveaways[message_id]
    else:
        if message_id in active_giveaways:
            del active_giveaways[message_id]

def get_active_giveaways():
    """Get all active giveaways"""
    return {**active_giveaways, **winner_active_giveaways}

def get_giveaway_by_message(message_id: int):
    """Get a giveaway by message_id"""
    if message_id in active_giveaways:
        return active_giveaways[message_id]
    if message_id in winner_active_giveaways:
        return winner_active_giveaways[message_id]
    return None