class EntityDoesNotExist(Exception):
    """
    Throw an exception when the data does not exist in the database.
    """


class EntityAlreadyExists(Exception):
    """
    Throw an exception when the data already exist in the database.
    """

class DatabaseError(Exception):
    """
    Throw general exception when the error is not suited to any other.
    """