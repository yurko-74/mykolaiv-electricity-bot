users = set()

def add_user(user_id):
    users.add(user_id)

def is_allowed(user_id):
    return user_id in users

def get_all_users():
    return users
