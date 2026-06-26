from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, email, first_name, last_name, role, languages=None):
        self.id = str(user_id)
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        # Languages is a list of strings, applicable mainly to guides
        self.languages = languages if languages else []

    @property
    def is_guide(self):
        return self.role == 'guide'

    @property
    def is_participant(self):
        return self.role == 'participant'