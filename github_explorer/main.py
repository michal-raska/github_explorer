import argparse
import getpass
import os
import re
import socket
from datetime import datetime

import github
from dateutil.relativedelta import relativedelta
from github import Github
from termcolor import colored

CHANGED_FILES_PAD = 50

STATE_OPEN = 'open'
STATE_MERGED = 'merged'
STATE_CLOSED = 'closed'


class PullRequestsCounts:
    AUTHORS_COUNTS_ALL_KEY = 'all'
    AUTHORS_COUNTS_OPEN_KEY = 'open'
    AUTHORS_COUNTS_CLOSED_KEY = 'closed'
    AUTHORS_COUNTS_MERGED_KEY = 'merged'
    AUTHORS_COUNTS_OFFENSIVE_KEY = 'offensive'

    SUMMARY_PAD = 47
    AUTHORS_PAD = 35

    def __init__(self, jira_key=None):
        self.__jira_key = jira_key
        self.__open_requests = 0
        self.__closed_requests = 0
        self.__merged_requests = 0
        self.__offensive_requests = 0
        self.__authors = {}

    def count_pull(self, pull):
        author = pull.user.login
        self.__ensure_author_counts(author)
        self.__authors[author][self.AUTHORS_COUNTS_ALL_KEY] += 1

        if pull.state == STATE_OPEN:
            self.__open_requests += 1
            self.__authors[author][self.AUTHORS_COUNTS_OPEN_KEY] += 1
        if pull.state == STATE_CLOSED:
            self.__closed_requests += 1
            self.__authors[author][self.AUTHORS_COUNTS_CLOSED_KEY] += 1
        if pull.merged:
            self.__merged_requests += 1
            self.__authors[author][self.AUTHORS_COUNTS_MERGED_KEY] += 1
        if self.is_offensive(pull):
            self.__offensive_requests += 1
            self.__authors[author][self.AUTHORS_COUNTS_OFFENSIVE_KEY] += 1

    def is_offensive(self, pull):
        return self.jira_key and self.jira_key not in pull.title

    def print_authors(self):
        section_header('AUTHORS')
        sorted_authors = sorted(self.__authors.items(), key=lambda author: author[1][self.AUTHORS_COUNTS_MERGED_KEY],
                                reverse=True)
        for author in sorted_authors:
            labeled_text(0, author[0], label_color='green')
            labeled_text(1, '# merged', author[1][self.AUTHORS_COUNTS_MERGED_KEY], pad=self.AUTHORS_PAD)
            labeled_text(1, '# open', author[1][self.AUTHORS_COUNTS_OPEN_KEY], pad=self.AUTHORS_PAD)
            labeled_text(1, '# closed', author[1][self.AUTHORS_COUNTS_CLOSED_KEY], pad=self.AUTHORS_PAD)
            labeled_text(1, '# closed  w/o merge', author[1][self.AUTHORS_COUNTS_CLOSED_KEY] - author[1][self.AUTHORS_COUNTS_MERGED_KEY], pad=self.AUTHORS_PAD)
            if self.jira_key:
                color = self.__offensive_label_color(author[1][self.AUTHORS_COUNTS_OFFENSIVE_KEY])
                labeled_text(1, '# offensive', author[1][self.AUTHORS_COUNTS_OFFENSIVE_KEY], label_color=color, pad=self.AUTHORS_PAD)
            labeled_text(1, '# all', author[1][self.AUTHORS_COUNTS_ALL_KEY], pad=self.AUTHORS_PAD)
            print()
        section_end()

    def print_summary(self):
        section_header('SUMMARY')
        labeled_text(0, '# merged pull requests', self.merged_requests, pad=self.SUMMARY_PAD)
        labeled_text(0, '# open pull requests', self.open_requests, pad=self.SUMMARY_PAD)
        labeled_text(0, '# closed pull requests', self.closed_requests, pad=self.SUMMARY_PAD)
        labeled_text(0, '# closed pull requests w/o merge', self.closed_requests - self.merged_requests, pad=self.SUMMARY_PAD)
        if self.jira_key:
            color = self.__offensive_label_color(self.offensive_requests)
            labeled_text(0, '# offensive pull requests', self.offensive_requests, label_color=color,
                         pad=self.SUMMARY_PAD)
        labeled_text(0, '# all pull requests', self.all_requests, pad=self.SUMMARY_PAD)
        section_end()

    def __ensure_author_counts(self, author):
        if self.__authors.get(author) is None:
            self.__authors[author] = {
                self.AUTHORS_COUNTS_OPEN_KEY: 0,
                self.AUTHORS_COUNTS_MERGED_KEY: 0,
                self.AUTHORS_COUNTS_CLOSED_KEY: 0,
                self.AUTHORS_COUNTS_ALL_KEY: 0,
                self.AUTHORS_COUNTS_OFFENSIVE_KEY: 0
            }

    @staticmethod
    def __offensive_label_color(count):
        if count > 0:
            return 'red'
        return 'blue'

    @property
    def jira_key(self):
        return self.__jira_key

    @property
    def open_requests(self):
        return self.__open_requests

    @property
    def closed_requests(self):
        return self.__closed_requests

    @property
    def merged_requests(self):
        return self.__merged_requests

    @property
    def all_requests(self):
        return self.open_requests + self.closed_requests

    @property
    def offensive_requests(self):
        return self.__offensive_requests


def create_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', help='Name of the repository', required=True)
    parser.add_argument('--history', help='Since when to list the PRs', default='1 day')
    parser.add_argument('--jira-key', help='Prefix of the JIRA Issue', default=None)
    return parser


def create_github_accessor():
    print('Please enter your GitHub credentials. To proceed without authentication, use empty username and password')
    username = input('Username: ')
    password = getpass.getpass()
    if username == '' and password == '':
        print(colored(
            'Warning: No authentication supplied, rate limit may apply.\n',
            'yellow'))
        return Github()
    else:
        return Github(username, password)


def check_access(repo):
    repo.name


def labeled_text(indent_level, label, text=None, label_color='blue', text_color='white', pad=30):
    indent = indent_level * '\t'
    label_text = colored("%s%s: " % (indent, label), label_color).ljust(pad)
    value_text = ''
    if text is not None:
        value_text = colored(text, text_color)
    print(label_text + value_text)


def section_header(header):
    decorated_header = "# %s #" % header
    colored_header = "# %s %s" % (colored(header, 'green'), colored('#', 'blue'))
    header_length = len(decorated_header)
    print(colored(header_length * '#', 'blue'))
    print(colored(colored_header, 'blue'))
    print(colored(header_length * '#', 'blue'))
    print()


def section_end():
    print()
    print(colored(40 * '-', 'blue'))
    print()


def state_colored(state):
    if state == STATE_CLOSED:
        return colored(STATE_CLOSED, 'yellow')
    if state == STATE_OPEN:
        return colored(STATE_OPEN, 'red')
    if state == STATE_MERGED:
        return colored(STATE_MERGED, 'green')
    return state


def process_repo_details(repo):
    section_header('REPO DETAILS')
    labeled_text(0, 'Name', repo.name)
    labeled_text(0, 'Description', repo.description)
    labeled_text(0, 'Modified', repo.last_modified)
    section_end()


def timedelta_from_history_arg(history_arg):
    if not re.compile('\d+ (hour(s|)|day(s|)|week(s|)|month(s|)|year(s|))').match(history_arg):
        notify_history_argument_invalid()
    (count, unit) = history_arg.split(' ')
    if int(count) == 0:
        notify_history_argument_invalid()
    if unit in ['hour', 'hours']:
        return relativedelta(hours=int(count))
    if unit in ['day', 'days']:
        return relativedelta(days=int(count))
    if unit in ['week', 'weeks']:
        return relativedelta(weeks=int(count))
    if unit in ['month', 'months']:
        return relativedelta(months=int(count))
    if unit in ['year', 'years']:
        return relativedelta(years=int(count))
    raise ValueError('History unit %s not supported' % unit)


def notify_history_argument_invalid():
    print(colored(
        'ERROR: \tArgument --history not valid. Valid argument contains a positive number and an unit. For example \'1 '
        'month\' or \'2 days\'. Supported units are: hour, day, month, year',
        'red'))
    exit(1)


def process_pull_files_change(repo, pull):
    changed_files = repo.get_pull(pull.number).get_files()
    changed_extensions = {}
    for changed_file in changed_files:
        file, ext = os.path.splitext(changed_file.filename)
        if changed_extensions.get(ext):
            changed_extensions[ext] += 1
        else:
            changed_extensions[ext] = 1
    for (ext, count) in changed_extensions.items():
        if ext == '':
            ext = 'no ext.'
        labeled_text(2, '# %s files changed' % ext, count, pad=CHANGED_FILES_PAD)


def process_pull_details(repo, pull, pull_requests_counts):
    labeled_text(0, pull.title, label_color='green')
    if pull_requests_counts.is_offensive(pull):
        labeled_text(1, 'offensive flag', 'OFFENSIVE', text_color='red')
    labeled_text(1, '#', pull.number)
    labeled_text(1, 'created by', pull.user.login)
    labeled_text(1, 'created at', pull.created_at)
    if pull.merged:
        labeled_text(1, 'state', state_colored(STATE_MERGED))
    else:
        labeled_text(1, 'state', state_colored(pull.state))
    if pull.merged:
        labeled_text(1, 'merge', '')
        labeled_text(2, 'by', pull.merged_by.login)
        labeled_text(2, 'at', pull.merged_at)
        labeled_text(2, 'after', pull.merged_at - pull.created_at)
    labeled_text(1, 'files', '')
    labeled_text(2, '# changed', pull.changed_files, pad=CHANGED_FILES_PAD)
    process_pull_files_change(repo, pull)

    print()


def process_pulls_details(pulls, pull_requests_counts, print_header=True, print_section_end=True):
    if print_header:
        section_header('PULL REQUESTS')

    requested_history = timedelta_from_history_arg(args.history)

    for pull in pulls:
        merged_before_requested_frame = pull.merged and pull.merged_at < datetime.now() - requested_history
        created_before_requested_frame = pull.created_at < datetime.now() - requested_history
        if merged_before_requested_frame or created_before_requested_frame:
            break

        process_pull_details(repo, pull, pull_requests_counts)

        pull_requests_counts.count_pull(pull)

    if print_section_end:
        section_end()

    return pull_requests_counts


if __name__ == '__main__':
    args = create_args_parser().parse_args()

    if args.jira_key is None:
        print(colored(
            'Warning: Jira key not set, offensive commits will not be marked. JIRA issue key can be set with the --jira-key <KEY> switch.\n',
            'yellow'))

    try:
        github_accessor = create_github_accessor()

        repo = github_accessor.get_repo(args.repo)
        check_access(repo)
        process_repo_details(repo)

        pulls = repo.get_pulls(state=STATE_OPEN)
        pull_requests_counts = PullRequestsCounts(args.jira_key)
        process_pulls_details(pulls, pull_requests_counts, print_section_end=False)
        pulls = repo.get_pulls(state=STATE_CLOSED)
        process_pulls_details(pulls, pull_requests_counts, print_header=False)

        pull_requests_counts.print_authors()

        pull_requests_counts.print_summary()
    except github.BadCredentialsException:
        print(colored('ERROR: Invalid credentials.', 'red'))
        exit(1)
    except github.UnknownObjectException:
        print(colored('ERROR: Cannot find repo %s.' % args.repo, 'red'))
        exit(1)
    except github.RateLimitExceededException:
        print(colored('ERROR: Rate limit exceeded. Please authenticate.', 'red'))
        exit(1)
    except (socket.timeout, socket.gaierror):
        print(colored('ERROR: Cannot reach Github. Please check your Internet connection.', 'red'))
