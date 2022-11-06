# compliance_data_model

This repo contains a small package called `compliance_pkg` for handling Twitter's compliance firehose data objects.

### Installing
From you terminal run
```sh
git clone git@github.com:mr-devs/compliance_data_model.git
```

Then run
```sh
pip install -e ./compliance_data_model/package
```

This should install the package locally.

You can check this was successful by then running
```sh
pip show compliance_pkg
```

If successful, it will show something like
```
Name: compliance-pkg
Version: 0.1
Summary: Package for working with Twitter's compliance firehose data
Home-page: None
Author: Matthew DeVerna
Author-email: None
License: None
Location: /path1/path2/path3/compliance_data_model/package
Requires:
Required-by:
```

### Usage

First, import all that the package has to offer (there isn't too much).
```python
from compliance_pkg import *
```

There is one convenience function, one base data class, and a class object for each of the specific types of action messages that Twitter sends through the compliance firehose.

Here is a list of everything:
- `return_possible_actions` : the convenience function. Pass one of `['user', 'tweet', 'drop', 'scrub_geo']` to return a set of the types of action messages parsed by the related class object
- `ComplianceBase` : the base data class. It's main purpose is to distinguish different types of compliance objects from one another, so it is a good idea to pass everything through this before any of the below objects.
- `TweetAction` : handles action messages related to tweets. E.g., delete tweet, tweet edit, etc.
- `UserAction` : handles action messages related to user. E.g., delete user, protect user, etc.
- `DropAction` : handles action messages related to dropped tweets. They are: drop tweet and undrop tweet.
- `ScrubGeoAction` : handles action messages related to scrubbing geographical info from tweets. Only option is scrub geo.

With everything imported, we can now read a file like

```py
import gzip
import json

file_name = "XXXXXXX.json.gz"

# Read the first compliance message
with gzip.open(file_name, "rb") as f:
    for line in f:
        # This will be a dictionary
        comp_msg = json.loads(line.decode())
        break # We only want the first tweet for this example
```

Then you can initialize a `ComplianceBase` class like.

```py
comp_obj = ComplianceBase(comp_msg)
```
> Note: If you pass in a `comp_msg` that does not match any of the data object forms outlined [here](https://developer.twitter.com/en/docs/twitter-api/enterprise/compliance-firehose-api/guides/compliance-data-objects), this will raise an error.

This will automatically determine which type of message you've just read. As mentioned above, there are four options: `['user', 'tweet', 'drop', 'scrub_geo']`.

To access the original dictionary, you can use `comp_obj.comp_object`.

You can then use `comp_obj` to determine which message you're holding and create that message's specific data object by doing something like:

```py
if self.is_drop_action:
    action_obj = DropAction(comp_obj)
elif self.is_geo_action:
    action_obj = ScrubGeoAction(comp_obj)
elif self.is_tweet_action:
    action_obj = TweetAction(comp_obj)
else:
    action_obj = UserAction(comp_obj)
```
> Note: All of these functions can also read the raw compliance message dictionary. I.e., `DropAction(comp_obj) == DropAction(comp_obj.comp_object)`

With the specific data object parsed, you can then access all fields within the dictionary with the methods.

## Methods available in all action message classes (i.e., inherited from `ComplianceBase`)

- `get_timestamp(as_datetime=[True or False])`: Return time of compliance message. Will include milliseconds.
- `get_value(key_list=list())`: Return a dictionary value from the compliance data object specified by `key_list`. 
- `to_json()`: Return a nice JSON string to print dictionaries cleanly

## Methods in `TweetAction`

- `get_tweet_id()`: Return the tweet ID (str) of the object.
- `get_edit_tweet_ids()`: Return a tuple of tweet ID info from an "edit_tweet" action object.
- `get_user_id()`: Return the user ID (str).
- `get_withheld_countries()`: Return list of countries in which a tweet is withheld.

## Methods in `UserAction`

- `get_user_id()`: Return the user ID (str) of the action object.
- `get_withheld_countries()`:Return list of countries in which a tweet is withheld.

## Methods in `DropAction`

- `get_tweet_id()`: Return the user ID (str) of the action object.
- `get_user_id()`: Return the user ID (str) of the action object.

## Methods in `ScrubGeoAction`

- `get_user_id()`: Return the user ID (str) of the action object.
- `get_up_to_status_id()`: Return the up_to_status_id (str) of the action object.