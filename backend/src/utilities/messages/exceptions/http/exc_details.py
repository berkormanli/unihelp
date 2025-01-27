def http_400_username_details(username: str) -> str:
    return f"The username {username} is taken! Be creative and choose another one!"


def http_400_email_details(email: str) -> str:
    return f"The email {email} is already registered! Be creative and choose another one!"


def http_400_signup_credentials_details() -> str:
    return "Signup failed! Recheck all your credentials!"


def http_400_sigin_credentials_details() -> str:
    return "Signin failed! Recheck all your credentials!"

def http_400_already_verified() -> str:
    return f"This user is already verified!"

def http_400_invalid_verification_code() -> str:
    return f"Invalid verification code"


def http_401_unauthorized_details() -> str:
    return "Refused to complete request due to lack of valid authentication!"


def http_403_forbidden_details() -> str:
    return "Refused access to the requested resource!"


def http_404_id_details(id: int) -> str:
    return f"Either the account with id `{id}` doesn't exist, has been deleted, or you are not authorized!"


def http_404_username_details(username: str) -> str:
    return f"Either the account with username `{username}` doesn't exist, has been deleted, or you are not authorized!"


def http_404_email_details(email: str) -> str:
    return f"Either the account with email `{email}` doesn't exist, has been deleted, or you are not authorized!"

def http_404_post_id_details(*, post_id: int) -> str:
    return f"The post with id `{post_id}` does not exist!"

def http_404_poll_id_details(*, poll_id: int) -> str:
    return f"The poll with id `{poll_id}` does not exist!"

def http_404_photo_id_details(*, photo_id: int) -> str:
    return f"The photo with id `{photo_id}` does not exist!"

def http_404_comment_id_details(*, comment_id: int) -> str:
    return f"The comment with id `{comment_id}` does not exist!"

def http_409_post_poll_conflict(*, post_id: int) -> str:
    return f"The post with id `{post_id}` already has a poll!"

def http_409_poll_already_voted(*, poll_id: int) -> str:
    return f"You have already voted on the poll with id `{poll_id}`!"
