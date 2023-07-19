import { DangerDSLType, DangerResults } from "danger";
declare const danger: DangerDSLType;
declare const warn: (message: string, results?: DangerResults) => void;

/**
 * Check if pull request has has a sufficiently accurate description
 *
 * @dangerjs WARN
 */
export default function (): void {
    let prDescription: string = danger.github.pr.body;
    const shortPrDescriptionThreshold: number = 100; // Description is considered too short below this number of characters

    // Remove HTML comments from the PR description
    prDescription = prDescription.replace(/<!--[\s\S]*?-->/g, '');

    // Split the PR description on the '#' character (markdown header) - consider as description only the text before the first header
    prDescription = prDescription.split('#')[0].trim();

    if (prDescription.length < shortPrDescriptionThreshold) {
        return warn(
            "The PR description looks very brief, please check if more details can be added."
        );
    }
}
