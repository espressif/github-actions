#!/usr/bin/env python3
#
# Copyright 2019 Espressif Systems (Shanghai) PTE LTD
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import jira
import github
import json
import sync_to_jira
import sync_issue
import os
import unittest
import unittest.mock
from unittest.mock import create_autospec
import tempfile

MOCK_GITHUB_TOKEN = "iamagithubtoken"


def run_sync_issue(event_name, event, jira_issue=None):
    """
    Run the 'sync_issue' main() function with supplied event (as Python dict), event name, and mocked JIRA PAI.

    If jira_issue is not None, this JIRA issue object will be
    returned as the only result of a call to JIRA.search_issues().
    """
    try:
        # dump the event data to a JSON file
        event_file = tempfile.NamedTemporaryFile('w+', delete=False)
        json.dump(event, event_file)
        event_file.close()

        os.environ['GITHUB_EVENT_NAME'] = event_name
        os.environ['GITHUB_EVENT_PATH'] = event_file.name

        os.environ['GITHUB_TOKEN'] = MOCK_GITHUB_TOKEN
        os.environ['JIRA_PROJECT'] = 'TEST'
        os.environ['JIRA_URL'] = 'https://test.test:88/'
        os.environ['JIRA_USER'] = 'test_user'
        os.environ['JIRA_PASS'] = 'test_pass'
        os.environ['GITHUB_REPOSITORY'] = 'espressif/fake'

        github_class = create_autospec(github.Github)

        # tell repo.has_in_collaborators() to return False by default
        github_class.return_value.get_repo.return_value.has_in_collaborators.return_value = False

        jira_class = create_autospec(jira.JIRA)

        # fake a issue_types response also
        issue_type_bug = create_autospec(jira.resources.IssueType)
        issue_type_bug.name = "Bug"
        issue_type_bug.id = 5001
        issue_type_task = create_autospec(jira.resources.IssueType)
        issue_type_task.name = "Task"
        issue_type_task.id = 5002
        issue_type_new_feature = create_autospec(jira.resources.IssueType)
        issue_type_task.name = "New Feature"
        issue_type_task.id = 5003

        jira_class.return_value.issue_types.return_value = [
            issue_type_bug,
            issue_type_task,
            issue_type_new_feature,
        ]

        if jira_issue is not None:
            jira_class.return_value.search_issues.return_value = [jira_issue]
            remote_link = create_autospec(jira.resources.RemoteLink)
            remote_link.globalId = event["issue"]["html_url"]
            remote_link.relationship = "synced from"
            remote_link.raw = {"object": {
                "title": event["issue"]["title"],
                "status": {},
            }}
            jira_class.return_value.remote_links.return_value = [remote_link]
        else:
            jira_class.return_value.search_issues.return_value = []

        sync_to_jira._JIRA = jira_class
        sync_to_jira.Github = github_class
        sync_issue.Github = github_class
        sync_to_jira.main()

        return jira_class.return_value  # mock JIRA object

    finally:
        os.unlink(event_file.name)


class TestIssuesEvents(unittest.TestCase):

    def test_issue_opened(self):
        issue = {"html_url": "https://github.com/espressif/fake/issues/3",
                 "repository_url": "https://github.com/espressif/fake",
                 "number": 3,
                 "title": "Test issue",
                 "body": "I am a new test issue\nabc\n测试\n",
                 "user": {"login": "testuser"},
                 "labels": [{"name": "bug"}],
                 "state": "open",
                 }
        event = {"action": "opened",
                 "issue": issue
                 }

        m_jira = run_sync_issue('issues', event)

        # Check that create_issue() was called with fields param resembling the GH issue
        fields = m_jira.create_issue.call_args[0][0]
        self.assertIn(issue["title"], fields["summary"])
        self.assertIn(issue["body"], fields["description"])
        self.assertIn(issue["html_url"], fields["description"])

        # Mentions 'issue', no mention of 'pull request'
        self.assertIn("issue", fields["description"])
        self.assertNotIn("pr", fields["summary"].lower())
        self.assertNotIn("pull request", fields["description"].lower())

        # Check that add_remote_link() was called
        rl_args = m_jira.add_remote_link.call_args[1]
        self.assertEqual(m_jira.create_issue.return_value, rl_args["issue"])
        self.assertEqual(issue["html_url"], rl_args["globalId"])

        # check that the github repo was updated via expected sequence of API calls
        sync_issue.Github.assert_called_with(MOCK_GITHUB_TOKEN)
        github_obj = sync_issue.Github.return_value
        github_obj.get_repo.assert_called_with("espressif/fake")
        repo_obj = github_obj.get_repo.return_value
        repo_obj.get_issue.assert_called_with(issue["number"])
        issue_obj = repo_obj.get_issue.return_value
        update_args = issue_obj.edit.call_args[1]
        self.assertIn("title", update_args)

    def test_issue_closed(self):
        m_jira = self._test_issue_simple_comment("closed")

        # check resolved was set
        new_object = m_jira.remote_links.return_value[0].update.call_args[0][0]
        new_status = new_object["status"]
        self.assertEqual(True, new_status["resolved"])

    def test_issue_deleted(self):
        self._test_issue_simple_comment("deleted")

    def test_issue_reopened(self):
        m_jira = self._test_issue_simple_comment("reopened")

        # check resolved was cleared
        new_object = m_jira.remote_links.return_value[0].update.call_args[0][0]
        new_status = new_object["status"]
        self.assertEqual(False, new_status["resolved"])

    def test_issue_edited(self):
        issue = {"html_url": "https://github.com/espressif/fake/issues/11",
                 "repository_url": "https://github.com/espressif/fake",
                 "number": 11,
                 "title": "Edited issue",
                 "body": "Edited issue content goes here",
                 "user": {"login": "edituser"},
                 "state": "open",
                 "labels": [],
                 }

        m_jira = self._test_issue_simple_comment("edited", issue)

        # check the update resembles the edited issue
        m_issue = m_jira.search_issues.return_value[0]

        update_args = m_issue.update.call_args[1]
        self.assertIn("description", update_args["fields"])
        self.assertIn("summary", update_args["fields"])
        self.assertIn(issue["title"], update_args["fields"]["summary"])

    def _test_issue_simple_comment(self, action, gh_issue=None):
        """
        Wrapper for the simple case of updating an issue (with 'action'). GitHub issue fields can be supplied, or generic ones will be used.
        """
        if gh_issue is None:
            gh_number = hash(action) % 43
            gh_issue = {"html_url": "https://github.com/espressif/fake/issues/%d" % gh_number,
                        "number": gh_number,
                        "title": "Test issue",
                        "body": "I am a test issue\nabc\n\n",
                        "user": {"login": "otheruser"},
                        "labels": [{"name": "Type: New Feature"}],
                        "state": "closed" if action in ["closed", "deleted"] else "open",
                        }
        event = {"action": action,
                 "issue": gh_issue
                 }

        m_issue = create_autospec(jira.Issue)(None, None)
        jira_id = hash(action) % 1001
        m_issue.id = jira_id

        m_jira = run_sync_issue('issues', event, m_issue)

        # expect JIRA API added a comment about the action
        comment_jira_id, comment = m_jira.add_comment.call_args[0]
        self.assertEqual(jira_id, comment_jira_id)
        self.assertIn(gh_issue["user"]["login"], comment)
        self.assertIn(action, comment)

        return m_jira

    def test_pr_opened(self):
        pr = {"html_url": "https://github.com/espressif/fake/pulls/4",
              "base": {"repo": {"html_url": "https://github.com/espressif/fake"}},
              "number": 4,
              "title": "Test issue",
              "body": "I am a new Pull Request!\nabc\n测试\n",
              "user": {"login": "testuser"},
              "labels": [{"name": "bug"}],
              "state": "open",
              }
        event = {"action": "opened",
                 "pull_request": pr
                 }

        m_jira = run_sync_issue('pull_request', event)

        # Check that create_issue() mentions a PR not an issue
        fields = m_jira.create_issue.call_args[0][0]
        self.assertIn("PR", fields["summary"])
        self.assertIn("Pull Request", fields["description"])
        self.assertIn(pr["html_url"], fields["description"])


class TestIssueCommentEvents(unittest.TestCase):

    def test_issue_comment_created(self):
        self._test_issue_comment("created")

    def test_issue_comment_deleted(self):
        self._test_issue_comment("deleted")

    def test_issue_comment_edited(self):
        self._test_issue_comment("edited", extra_event_data={"changes": {"body": {"from": "I am the old comment body"}}})

    def _test_issue_comment(self, action, gh_issue=None, gh_comment=None, extra_event_data={}):
        """
        Wrapper for the simple case of an issue comment event (with 'action'). GitHub issue and comment fields can be supplied, or generic ones will be used.
        """
        if gh_issue is None:
            gh_number = hash(action) % 50
            gh_issue = {"html_url": "https://github.com/espressif/fake/issues/%d" % gh_number,
                        "repository_url": "https://github.com/espressif/fake",
                        "number": gh_number,
                        "title": "Test issue",
                        "body": "I am a test issue\nabc\n\n",
                        "user": {"login": "otheruser"},
                        "labels": []
                        }
        if gh_comment is None:
            gh_comment_id = hash(action) % 404
            gh_comment = {"html_url": gh_issue["html_url"] + "#" + str(gh_comment_id),
                          "repository_url": "https://github.com/espressif/fake",
                          "id": gh_comment_id,
                          "user": {"login": "commentuser"},
                          "body": "ZOMG a comment!"
                          }
        event = {"action": action,
                 "issue": gh_issue,
                 "comment": gh_comment
                 }
        event.update(extra_event_data)

        m_issue = create_autospec(jira.Issue)(None, None)
        jira_id = hash(action) % 1003
        m_issue.id = jira_id
        m_issue.key = "FAKEFAKE-%d" % (hash(action) % 333,)

        m_jira = run_sync_issue('issue_comment', event, m_issue)

        # expect JIRA API added a comment about the action
        comment_jira_id, comment = m_jira.add_comment.call_args[0]
        self.assertEqual(jira_id, comment_jira_id)
        self.assertIn(gh_comment["user"]["login"], comment)
        self.assertIn(gh_comment["html_url"], comment)
        if action != "deleted":
            self.assertIn(gh_comment["body"], comment)  # note: doesn't account for markdown2wiki

        return m_jira


if __name__ == '__main__':
    unittest.main()
