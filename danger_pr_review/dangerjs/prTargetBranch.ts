import { DangerDSLType, DangerResults } from 'danger';
import { Octokit } from '@octokit/rest';
declare const danger: DangerDSLType;
declare const fail: (message: string, results?: DangerResults) => void;

/**
 * Check if the target branch is "master" or "main".
 *
 * @dangerjs FAIL
 */
export default async function (): Promise<void> {
	const prTargetBranch: string = danger.github.pr.base.ref;
	const repoOwner: string = danger.github.pr.base.repo.owner.login;
	const repoName: string = danger.github.pr.base.repo.name;

    // Get repo details from GitHub API
	const octokit = new Octokit();
	const { data: repo } = await octokit.repos.get({
		owner: repoOwner,
		repo: repoName,
	});

	const defaultBranch = repo.default_branch;

	if (prTargetBranch !== defaultBranch) {
		return fail(`
        The target branch for this pull request should be the default branch of the project (${defaultBranch}).\n
        If you would like to add this feature to a different branch, please state this in the PR description and we will consider it.
        `);
	}
}
