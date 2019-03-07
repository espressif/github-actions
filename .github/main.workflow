workflow "Run sync_issues_to_jira tests" {
  on = "push"
  resolves = ["Run JIRA Sync Unit Tests"]
}

action "Run JIRA Sync Unit Tests" {
  uses = "./sync_issues_to_jira"
  runs = [ "/test_sync_issue.py" ]
}
