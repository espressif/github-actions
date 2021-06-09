from github import Github
import os
import re

def handle_push_event(event):
    issue_numbers = []
    for commit in event['commits']:
        commit_message = commit['message']
        issue_numbers += parse_commit_message(commit_message)
    
    github = Github(os.environ['GITHUB_TOKEN'])
    repo = github.get_repo(os.environ['GITHUB_REPOSITORY'])
    for issue in issue_numbers:
        gh_issue = repo.get_issue(int(issue))
        if gh_issue.pull_request:
            update_pull_request(gh_issue.as_pull_request())

def update_pull_request(pull_request):
    print("Updating %s" % pull_request)
    if pull_request.state == 'open':
        print('Pull request is open, nothing to update.')
        return
    original_title = pull_request.title
    # Prepend [Merged] to the pull request title
    new_title = '[Merged] ' + original_title
    pull_request.edit(title=new_title)
    # Thank contributor for opening pull request. Let them know we didn't throw it away
    pull_request.create_issue_comment('The pull request has been cherry-picked, the commit is linked above.\
        Thank you for your contribution!')


def parse_commit_message(commit_message):
    # Regex matches numbers that come after Fix, fix, Fixed, fixed, Fixes, fixes keyword followed by any
    # combination of spaces and colons, followed by exactly one hashtag. The same applies for Close and Resolve
    # keywords and their combinations. Note: fixing, closing and resolving don't work.
    # Only first number is picked. To match multiple numbers you have to add fix or close or resolve or implement keyword
    # for each of them.
    # Example:
    # fixed: #1 #2 #3
    # resolved   ::: ::: :: #4
    # closes: ##5
    # fix: # 6
    # asdfresolves #7
    # closeasdf: #8
    # closes #9 <any sting in between> fixed #10
    # fixing #11
    # Matches: [1, 4, 7, 9, 10]
    pattern = re.compile('(?:[Ff]ix(?:e[sd]?)(?:\ |:)+|(?:[Cc]los(?:e[sd]?)(?:\ |:)+)|(?:[Rr]esolv(?:e[sd]?)(?:\ |:)+))#(\d+)')
    return pattern.findall(commit_message)