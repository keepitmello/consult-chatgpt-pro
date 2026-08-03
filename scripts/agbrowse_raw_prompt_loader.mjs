const QUESTION_MODULE_SUFFIX = '/web-ai/question.mjs';
const RAW_PROMPT_ENV = 'CONSULT_AGBROWSE_RAW_PROMPT';
const FUNCTION_MARKER = 'function renderNormalizedEnvelope(envelope) {\n    const blocks = [];';

const RAW_PROMPT_BRANCH = `function renderNormalizedEnvelope(envelope) {
    if (process.env.${RAW_PROMPT_ENV} === '1') {
        const composerText = envelope.question || envelope.prompt;
        if (composerText.length > INLINE_CHAR_LIMIT) {
            throw new WebAiError({
                errorCode: 'context.over-budget',
                stage: 'context-preflight',
                retryHint: 'reduce-files',
                message: \`inline prompt too large: \${composerText.length}/\${INLINE_CHAR_LIMIT} chars\`,
                evidence: { length: composerText.length, limit: INLINE_CHAR_LIMIT },
            });
        }
        return {
            markdown: composerText,
            composerText,
            estimatedChars: composerText.length,
            warnings: [],
        };
    }
    const blocks = [];`;

export async function load(url, context, nextLoad) {
    const result = await nextLoad(url, context);
    if (process.env[RAW_PROMPT_ENV] !== '1' || !url.endsWith(QUESTION_MODULE_SUFFIX)) {
        return result;
    }

    const source = String(result.source);
    if (!source.includes(FUNCTION_MARKER) || !source.includes("renderTrustedSection('USER'")) {
        throw new Error(
            'Consult raw-prompt transport is incompatible with this agbrowse question renderer; ' +
            'verify the installed agbrowse release before sending.',
        );
    }

    return {
        ...result,
        source: source.replace(FUNCTION_MARKER, RAW_PROMPT_BRANCH),
    };
}
