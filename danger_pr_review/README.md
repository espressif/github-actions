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

## Shared DangerJS checks descriptions
#### Check for commit message (prCommitMessage.ts)
Linter for commit messages. Checks if some commit messages are not generated automatically or if they are too vague/short.

*`TODO`: will be updated for the conventional commits linter (module `commitlint`)*

***
#### Check for commit history (prCommitsTooManyCommits.ts)
In case of more than 2 commits in a pull request, the user is suggested to squash his commits and simplify the commit history.

***
#### Check for PR target branch (prTargetBranch.ts)
Checks whether the target branch of the pull request is `master` or `main`.

***
#### Info message for project contributors (prInfoContributor.ts)
Provides an automated message to project contributors. If the contributor is known to the project, it will only post a simple "thank you for contributing" message.

If the contributor is unknown (a first-time contributor), it will then also explain the review and merge process in the published message, so that people know what to expect regarding their pull request.

There is a link to the `Contributions Guide` which points to the main README file of the project. **If your project uses the `Contributions Guide`, please add a link to it in the README.**

***
#### Check for PR description (prDescription.ts)
Evaluates whether the pull request has a sufficient description (longer than 100 characters). Comments in HTML comment tags `<!--` and `-->` are ignored.

**As PR description is considered all text before first `#` character** (markdown header). 

For example in case of:
```
This PR changes documentation of CI process
- guide for GitHub action workflow
- guide for usage of self-hosted runners

## Related
- https://github.com/espressif/esptool/pull/900

```

... as description will be considered only this part:
```
This PR changes documentation of CI process
- guide for GitHub action workflow
- guide for usage of self-hosted runners
```

If you are using pull request templates (e.g. `.github/pull_request_template.md`) for your project, modify them accordingly:
- keep the user instructions in the HTML comment tags `<!--` and `-->`
- structure markdown headers so the actual PR description does NOT follow any `#` header (e.g. avoid adding a `# Description` header)

This is a good example of a `.github/pull_request_template.md` file that DangerJS can handle correctly:
```markdown
<!-- HERE FILL IN A DESCRIPTION OF THE CHANGE, at least 100 characters
Make sure other people will be able to understand what your pull request is about -->

# Fix the bug(s)
<!-- If your change fixes any bugs, list them in this section. 
  Otherwise, delete this section, including the section header "# Fix the bug(s)" 

PLEASE INCLUDE THE ISSUE URL OR # ISSUE NUMBER HERE. -->

# Tested with
<!-- In this section, describe the hardware and software combinations with which you tested the PR change - operating system(s), development board name(s), ESP8266 and/or ESP32.

  IF YOU DID NOT PERFORM ANY TESTING, WRITE "NO TESTING" in this section. -->

# CI and integration tests

<!-- I ran automatic integration tests of esptool.py with this change and the above hardware. The results were as follows:  

Details here: https://docs.espressif.com/projects/esptool/en/latest/contributing.html#automated-integration-tests

  IF YOU DID NOT PERFORM ANY TESTING, WRITE "NO TESTING" in this section. 
-->

```
***
***


## Example Workflow yaml file
```yml
name: DangerJS Check
on:
  pull_request:
    types: [opened, edited, reopened, synchronize]

permissions:
  pull-requests: write
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


**If you are about to create a new DangerJS shared check, please consider that it must be relevant for all Espressif projects. It doesn't make sense to add project-specific checks to this GitHub action. We are trying to make this GitHub action as universal as possible.**

If you have created a new DangerJS check, please be sure to document it in this file in the `## Descriptions of DangerJS Shared Controls` section so that others will know what it does.


#### Local testing when developing DangerJS checks
Danger checks can be also tested locally (without running the GitHub action pipeline). For local testing move to `danger_pr_review/dangerjs` and install `npm` dependencies:
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
npx danger pr <pull_request_url>   # copy url from browser
```

The result will appear in your terminal.
