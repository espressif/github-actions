# DangerJS pull request automatic review tool - GitHub

This is the DangerJS pull request linter GitHub action, that can be called from another repositories. It's purpose is to keep the style of each PR in the specified style and automatically check for simple things like correct PR description, meaningful git messages, correct PR target branch, etc.

Because DangerJS does this automatically, human reviewers can focus more on code changes and spend their time reviewing PRs more productively.

Danger JS checks from this GH action are common to all projects. 

| check                      | purpose                                                        |
| -------------------------- | -------------------------------------------------------------- |
| prCommitMessage.ts         | linter for commit messages                                     |
| prCommitsTooManyCommits.ts | keeping git history simple, no more than 2 commits             |
| prDescription.ts           | ensure PR description is present an sufficient                 |
| prInfoContributor.ts       | info message for new / known contributors about review process |
| prTargetBranch.ts          | ensure that PR target branch is default branch of GH project   |

You can have additional Danger checks in your individual project alongside this Danger GH action. These checks can be stored and run in the project-specific Dangerfile. In that case you also need to add another job to project workflow yaml file, that will run these additional checks.

## Example Workflow yaml file
```yml
name: DangerJS Check
on:
  pull_request:
    types: [opened, edited, reopened, synchronize]

permissions:
  statuses: write


jobs:
  pull-request-style-linter:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: DangerJS pull request linter
      uses: espressif/github-actions/danger_pr_review@master
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

* The `GITHUB_TOKEN` is needed to access repo and PR content, as well as to create automatic Danger BOT comments in PR. The token is automatically obtained from the GitHub project and its specific permissions are set in the yaml workflow file. Avoid adding unnecessarily high permissions to this token, keep it set as in the example above.

## Implementation and development of this GitHub action
When adding a new Danger rule or updating existing one, might be a good idea to test it on the developer's fork of GitHub project. This way, the new feature can be tested using a GitHub action without concern of damaging Espressif's GitHub repository.

Danger for Espressif GitHub is implemented in TypeScript. This makes the code more readable and robust than plain JavaScript. 
Compilation to JavaScript code (using `tsc`) is not necessary; Danger handles TypeScript natively.

A good practice is to store each Danger rule in a separate module, and then import these modules into the main Danger file `danger_pr_review/dangerjs/dangerfile.ts` (see how this is done for currently present modules when adding a new one).

If the Danger module (new check/rule) uses an external NPM module (e.g. `axios`), be sure to add this dependency to `danger_pr_review/dangerjs/package.json` and also update `danger_pr_review/dangerjs/package-lock.json`.

In the GitHub action, `danger` is not installed globally (nor are its dependencies) and the `npx` call is used to start the `danger` checks in CI.


#### Test locally
Danger rules can be tested locally (without running the GitHub action pipeline). For local testing move to `danger_pr_review/dangerjs` and install dependencies:
```sh
cd danger_pr_review/dangerjs && npm install
```

You have to also export the variables used by Danger in your local shell session:

```sh
# GITHUB_TOKEN must have access to the repository with a pull request
export GITHUB_TOKEN='**************************************'
```

Now you can call Danger by:
```sh
npx danger pr <pull_request_url>   # copy url form browser
```

The result will appear in your terminal.
