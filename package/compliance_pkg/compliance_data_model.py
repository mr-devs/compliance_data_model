"""
Data model to handle Twitter Decahose compliance data objects.

Reference: https://developer.twitter.com/en/docs/twitter-api/enterprise/compliance-firehose-api/overview

Date: 2022-11-06
Author: Matthew DeVerna
"""
import datetime
import json


from .utils import get_dict_val

USER_ACTIONS = set(
    [
        "user_delete",
        "user_protect",
        "user_suspend",
        "user_undelete",
        "user_unprotect",
        "user_unsuspend",
        "user_withheld",
    ]
)
TWEET_ACTIONS = set(["delete", "tweet_edit", "status_withheld"])
DROP_ACTIONS = set(["drop", "undrop"])
GEO_ACTIONS = set(["scrub_geo"])
LIKE_ACTIONS = set(["delete"])

# Static methods
# --------------------
def return_possible_actions(action_class):
    """
    Return a set of all possible types of compliance messages for the specified type.

    Parameters:
    -----------
    - action_class (str): the class of compliance messages to return
        Options: ['user', 'tweet', 'drop', 'scrub_geo', 'like']
    """
    options = ["user", "tweet", "drop", "scrub_geo", "like"]
    if action_class not in options:
        raise TypeError(f"`action_class` must be one of: {options}")

    if action_class == "user":
        return USER_ACTIONS
    elif action_class == "tweet":
        return TWEET_ACTIONS
    elif action_class == "drop":
        return DROP_ACTIONS
    elif action_class == "scrub_geo":
        return GEO_ACTIONS
    elif action_class == "like":
        return LIKE_ACTIONS


# Base class
# --------------------
class ComplianceBase:
    """
    Base class for compliance data objects. Utilized to distinguish different
    types of compliance objects from one another.
    """

    def __init__(self, comp_object=None):
        """
        This function initializes the instance by binding the compliance object
        Parameters:
            - comp_object (dict): the JSON object of the social media post
        """
        if comp_object is None:
            raise ValueError("Compliance object cannot be None!")
        self.comp_object = comp_object

        # Identify action type
        self.action = list(self.comp_object.keys())[0]
        self.is_user_action = True if self.action in USER_ACTIONS else False
        self.is_tweet_action = True if self.action in TWEET_ACTIONS else False
        self.is_drop_action = True if self.action in DROP_ACTIONS else False
        self.is_geo_action = True if self.action in GEO_ACTIONS else False
        self.is_like_action = True if self.action in LIKE_ACTIONS else False

        # Throw error if unknown action encountered
        all_action_flags = [
            self.is_user_action,
            self.is_tweet_action,
            self.is_drop_action,
            self.is_geo_action,
            self.is_like_action,
        ]
        if sum(all_action_flags) != 1:
            raise TypeError(
                "Unknown action encountered!!\n\n"
                f"Compliance object: {self.comp_object}"
            )

    def get_value(self, key_list: list = []):
        """
        Return a dictionary value from the compliance data object with `key_list`.
        From left to right, each string in the key_list
        indicates another nested level further down in the dictionary.
        If no value is present after reaching the end of the indicated `key_list`
        path, `None` is returned.

        Parameters:
        ----------
        - dictionary (dict) : the dictionary object to traverse
        - key_list (list) : list of strings indicating what dict_obj
            item to retrieve

        Returns:
        ----------
        - key value (if present) or None (if not present)
        """
        return get_dict_val(self.comp_object, key_list)

    def get_timestamp(self, as_datetime=False):
        """
        Return time of compliance message.

        Parameters:
        -----------
        - as_datetime (bool): whether to convert the timestamp to a datetime object.
            Default=False.

        Returns:
        - time (str/datetime.datetime): the time of the compliance message
            - If as_datetime=False: timestamp (str) containing milliseconds
                returned
            - If as_datetime=True: datetime.datetime object containing
                milliseconds returned

        NOTE: returned time  will include milliseconds!
        """
        # All this complexity is just to handle user_withheld objects
        # which are annoyingly stored in ISO format
        is_dt_obj = False
        if self.is_user_action:
            if self.is_user_withheld:
                iso_fmt_time = self.get_value([self.action, "timestampMs"])
                dt_obj = datetime.datetime.fromisoformat(iso_fmt_time).replace(
                    tzinfo=None
                )
                is_dt_obj = True
            else:
                timestamp_ms = self.get_value([self.action, "timestamp_ms"])
        else:
            timestamp_ms = self.get_value([self.action, "timestamp_ms"])

        # If this is True, we must have the user_withheld dt_obj
        if is_dt_obj:
            if as_datetime:
                return dt_obj
            return str(int(dt_obj.timestamp() * 1000))
        # Otherwise, we have the regular epoch timestamp string containing milliseconds
        elif as_datetime:
            return datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000)
        return timestamp_ms

    def to_json(self):
        """Render a nice JSON string to print dictionaries cleanly"""
        return json.dumps(self.comp_object, indent=2)

    def __str__(self):
        """
        Define the representation of the object when using print().
        """
        return f"{self.to_json()}"

    def __repr__(self):
        """
        Define the representation of the object.
        """
        return (
            f"<{self.__class__.__name__}() object>\n"
            f"Action: {self.action}\n"
            f"Data:\n{self.to_json()}"
        )


# Action message classes
# --------------------
class TweetAction(ComplianceBase):
    """
    Class to handle compliance tweet objects.
    """

    def __init__(self, tweet_action):
        """
        This function initializes the instance by binding the comp_object to
        the TweetAction class.

        Parameters:
        -----------
        - user_action (ComplianceBase, dict): the compliance base object or the
            JSON object from the compliance firehose
        """
        if isinstance(tweet_action, ComplianceBase):
            super().__init__(tweet_action.comp_object)
        elif isinstance(tweet_action, dict):
            super().__init__(tweet_action)
        else:
            TypeError("`tweet_action` type must be one of: [ComplianceBase, dict]")

        if not self.is_tweet_action:
            raise TypeError(
                "ComplianceBase does not contain a tweet action!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

        self.is_delete = True if self.action == "delete" else False
        self.is_tweet_edit = True if self.action == "tweet_edit" else False
        self.is_tweet_witheld = True if self.action == "status_withheld" else False
        all_action_flags = [
            self.is_delete,
            self.is_tweet_edit,
            self.is_tweet_witheld,
        ]
        if sum(all_action_flags) != 1:
            raise TypeError(
                "Unknown action encountered!!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

    def get_tweet_id(self):
        """
        Return the tweet ID (str) of the object.

        NOTE: If a "tweet_edit" action, this will return the latest tweet ID.
            See the specialized `get_tweet_edit_ids()` method.
        """
        if self.is_delete or self.is_tweet_witheld:
            return self.get_value([self.action, "status", "id_str"])
        elif self.is_tweet_edit:
            return self.get_value([self.action, "tweet_edit", "id"])
        else:
            return None

    def get_edit_tweet_ids(self):
        """
        Return all tweet ID info from an "edit_tweet" action object. If not
        an edit_tweet action, return tuple of None values.

        Returns:
        -----------
        (id, initial_id, edit_tweet_ids) : a tuple of all tweet edit ID information
        - id (str) : current tweet ID of edited tweet
        - initial_id (str) : initial tweet ID of edited tweet
        - edit_tweet_ids (list) : all tweet IDs that the tweet has held.
            Temporally ordered where first index is `initial_id` and the
            last is `id`.
        """
        if not self.is_tweet_edit:
            return (None, None, None)
        return (
            self.get_value([self.action, "id"]),
            self.get_value([self.action, "initial_tweet_id"]),
            self.get_value([self.action, "edit_tweet_ids"]),
        )

    def get_user_id(self):
        """
        Return user ID information. Only present for `tweet_withheld` and
            `tweet_delete` actions. If action is `tweet_edit`, returns None
        """
        if self.is_delete or self.is_tweet_witheld:
            return self.get_value([self.action, "status", "user_id_str"])
        return None

    def get_withheld_countries(self):
        """
        Return list of countries in which a tweet is withheld.

        If not `tweet_withheld` message, return None
        """
        if self.is_tweet_witheld:
            return self.get_value([self.action, "withheld_in_countries"])
        return None


class UserAction(ComplianceBase):
    """
    Class to handle compliance user actions.
    """

    def __init__(self, user_action):
        """
        This function initializes the instance by binding the comp_object to
        the UserAction class.

        Parameters:
        -----------
        - user_action (ComplianceBase, dict): the compliance base object or the
            JSON object from the compliance firehose
        """
        if isinstance(user_action, ComplianceBase):
            super().__init__(user_action.comp_object)
        elif isinstance(user_action, dict):
            super().__init__(user_action)
        else:
            TypeError("`user_action` type must be one of: [ComplianceBase, dict]")

        if not self.is_user_action:
            raise TypeError(
                "ComplianceBase does not contain a user action!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

        # Mark message type within the user object
        self.is_user_delete = True if self.action == "user_delete" else False
        self.is_user_protect = True if self.action == "user_protect" else False
        self.is_user_suspend = True if self.action == "user_suspend" else False
        self.is_user_undelete = True if self.action == "user_undelete" else False
        self.is_user_unprotect = True if self.action == "user_unprotect" else False
        self.is_user_unsuspend = True if self.action == "user_unsuspend" else False
        self.is_user_withheld = True if self.action == "user_withheld" else False
        # Ensure it is exactly one of these options
        all_action_flags = [
            self.is_user_delete,
            self.is_user_protect,
            self.is_user_suspend,
            self.is_user_undelete,
            self.is_user_unprotect,
            self.is_user_unsuspend,
            self.is_user_withheld,
        ]
        if sum(all_action_flags) != 1:
            raise TypeError(
                "Unknown action encountered!!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

    def get_user_id(self):
        """
        Return the user ID (str) of the action object.

        NOTE: If a "tweet_edit" action, this will return the latest tweet ID.
            See the specialized `get_tweet_edit_ids()` method.
        """
        if not self.is_user_withheld:
            return str(self.get_value([self.action, "id"]))
        return self.get_value([self.action, "user", "id_str"])

    def get_withheld_countries(self):
        """
        Return list of countries in which a tweet is withheld.
        """
        if self.is_user_withheld:
            return self.get_value([self.action, "withheld_in_countries"])
        return None


class DropAction(ComplianceBase):
    """
    Class to handle compliance drop actions.
    """

    def __init__(self, drop_action):
        """
        This function initializes the instance by binding the comp_object to
        the DropAction class.

        Parameters:
        -----------
        - drop_action (ComplianceBase, dict): the compliance base object or the
            JSON object from the compliance firehose
        """
        if isinstance(drop_action, ComplianceBase):
            super().__init__(drop_action.comp_object)
        elif isinstance(drop_action, dict):
            super().__init__(drop_action)
        else:
            TypeError("`drop_action` type must be one of: [ComplianceBase, dict]")

        if not self.is_drop_action:
            raise TypeError(
                "ComplianceBase does not contain a drop action!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

        # Mark message type within the user object
        self.is_drop = True if self.action == "drop" else False
        self.is_undrop = True if self.action == "undrop" else False
        # Ensure it is exactly one of these options
        all_action_flags = [
            self.is_drop,
            self.is_undrop,
        ]
        if sum(all_action_flags) != 1:
            raise TypeError(
                "Unknown action encountered!!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

    def get_tweet_id(self):
        """
        Return the user ID (str) of the action object.
        """
        return self.get_value([self.action, "status", "id_str"])

    def get_user_id(self):
        """
        Return the user ID (str) of the action object.
        """
        return self.get_value([self.action, "status", "user_id_str"])


class ScrubGeoAction(ComplianceBase):
    """
    Class to handle compliance scrub geo actions.
    """

    def __init__(self, geo_action):
        """
        This function initializes the instance by binding the comp_object to
        the ScrubGeoAction class.

        Parameters:
        -----------
        - geo_action (ComplianceBase, dict): the compliance base object or the
            JSON object from the compliance firehose
        """
        if isinstance(geo_action, ComplianceBase):
            super().__init__(geo_action.comp_object)
        elif isinstance(geo_action, dict):
            super().__init__(geo_action)
        else:
            TypeError("`geo_action` type must be one of: [ComplianceBase, dict]")

        if not self.is_geo_action:
            raise TypeError(
                "ComplianceBase does not contain a scrub geo action!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

    def get_user_id(self):
        """
        Return the user ID (str) of the action object.
        """
        return self.get_value([self.action, "user_id_str"])

    def get_up_to_status_id(self):
        """
        Return the up_to_status_id (str) of the action object.
        """
        return self.get_value([self.action, "up_to_status_id_str"])


class DeleteLikeAction(ComplianceBase):
    """
    Class to handle compliance delete like actions.
    """

    def __init__(self, like_action):
        """
        This function initializes the instance by binding the comp_object to
        the DeleteLikeAction class.

        Parameters:
        -----------
        - like_action (ComplianceBase, dict): the compliance base object or the
            JSON object from the compliance firehose
        """
        if isinstance(like_action, ComplianceBase):
            super().__init__(like_action.comp_object)
        elif isinstance(like_action, dict):
            super().__init__(like_action)
        else:
            TypeError("`like_action` type must be one of: [ComplianceBase, dict]")

        if not self.is_like_action:
            raise TypeError(
                "ComplianceBase does not contain a like action!\n"
                f"ComplianceBase Action: {self.action}"
                f"ComplianceBase Object:\n{self.comp_object}"
            )

    def get_tweet_id(self):
        """
        Return the tweet ID (str) of the action object.
        """
        return self.get_value([self.action, "favorite", "tweet_id_str"])

    def get_user_id(self):
        """
        Return the user ID (str) of the action object.
        """
        return self.get_value([self.action, "favorite", "user_id_str"])
