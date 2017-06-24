# github_explorer
Simple command line utility, to explore the pull requests of a given repo.

# Installation
github_explorer requires **Python 3.5**. Install with:
<pre>
$ python setup.py install
</pre>

# Usage
To run the utility, invoke the `github_explorer/main.py` script.
```
$ python main.py --repo <REPO> --history <HISTORY STRING> --jira-key <JIRA KEY>
```

The **repo** is the only **required** argument and it should be a valid repository with user/organization, for example `h2o.ai/sparkling-water`.

The **history string** consists of count and unit, for example `1 day`, or `2 weeks`. Supported units are:
* day
* week
* month
* year

The **jira key** might be any string and is used to find offensive pull requests. Offensive pull requests do not contain jira issue number.

An example follows:
```
$ python main.py --repo h2oai/sparkling-water --history '3 days' --jira-key 'SW'
```