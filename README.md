# AI-Powered Pull Request Review Action 🔍🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions Version](https://img.shields.io/github/v/release/pritom007/ai-pr-review)](https://github.com/pritom007/ai-pr-review/releases)
[![Build Status](https://github.com/pritom007/ai-pr-review/actions/workflows/test.yml/badge.svg)](https://github.com/pritom007/ai-pr-review/actions)
[![Issues](https://img.shields.io/github/issues/pritom007/ai-pr-review)](https://github.com/pritom007/ai-pr-review/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/pritom007/ai-pr-review)](https://github.com/pritom007/ai-pr-review/pulls)
[![Stars](https://img.shields.io/github/stars/pritom007/ai-pr-review)](https://github.com/pritom007/ai-pr-review/stargazers)

Automated code review for GitHub pull requests powered by large language models (LLMs). Supports OpenAI, Groq, Azure OpenAI, and any OpenAI-compatible API endpoint.

![PR Review Example](https://via.placeholder.com/800x400.png?text=AI+PR+Review+Demo+Output)

## Table of Contents

- [Features] (#features)

- [Supported Providers] (#supported-providers)

- [Quick Start] (#quick-start)

- [Configuration] (#configuration)

- [Example Output] (#example-output)

- [Roadmap] (#roadmap)

- [Troubleshooting] (#troubleshooting)

- [License] (#license)

## Features ✨

- **Smart Analysis:** Detect bugs, security issues, and optimization opportunities
- **Multi-LLM Support:** Works seamlessly with leading AI providers
- **Customizable Feedback:** Control review depth, creativity, and response length (To-Do)
- **Rich Markdown Formatting:** Clear, structured, and detailed review outputs
- **Enterprise Ready:** Dockerized with secure handling of secrets
- **Multi-language Support:** Reviews are available in 100+ languages (Any language supported by the LLM provider)

## Supported Providers 🤖

| Provider     | Base URL                           | Models                                 |
|--------------|------------------------------------|----------------------------------------|
| OpenAI       | `https://api.openai.com/v1`        | `gpt-4`, `gpt-3.5-turbo`               |
| Groq         | `https://api.groq.com/openai/v1`   | `llama3-70b-8192`, `mixtral-8x7b-32768`|
| Azure OpenAI | Your Azure endpoint                | `gpt-4`, `gpt-35-turbo`                |
| Local/Custom | `http://localhost:port/v1`         | OpenAI-compatible                      |

## Quick Start 🚀

### 1. Set API Key Secret

In your GitHub repository:

```yaml
Settings → Secrets and variables → Actions → New repository secret
Name: INPUT_API_KEY  # make sure this is the name of the secret
Value: your-api-key-here
```

### 2. Add Workflow File

Create `.github/workflows/pr-review.yml`:

```yaml
name: AI Code Review
on: [pull_request]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: pritom007/ai-pr-review@v1
        with:
          api-key: ${{ secrets.INPUT_API_KEY }}
          model-name: "llama3-70b-8192"
          base-url: "https://api.groq.com/openai/v1"
          temperature: "0.7"
          max-tokens: "1000"
          language: "English"
```
Set the llm model api key in your github secrets as `INPUT_API_KEY`. Also make sure you gave `read` permission to the `contents` and `write` premission to the `pull-requests`.

## Configuration ⚙️

| Parameter    | Required | Default                | Description                   |
|--------------|----------|------------------------|-------------------------------|
| api-key      | ✅       | -                      | Your LLM provider's API key   |
| model-name   | ✅       | -                      | Specific LLM model to use     |
| base-url     | ❌       | OpenAI endpoint        | API URL of your LLM provider  |
| temperature  | ❌       | 0.7                    | 0 (Precise) ↔ 2 (Creative)    |
| max-tokens   | ❌       | 1000                   | Limit of response length      |
| language     | ❌       | English                | Language for the review       |
| custom-chunk-prompt | ❌ | -                  | Custom prompt for analyzing code chunks |
| custom-summary-prompt | ❌ | -                | Custom prompt for generating final summary |

### Advanced Usage

#### Custom Prompts

You can customize the prompts used for code review by providing your own prompts. This allows you to:
- Focus on specific aspects of code review
- Use your team's preferred review format
- Add domain-specific requirements
- Customize the output format

Example with custom prompts:

```yaml
name: AI Code Review
on: [pull_request]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: pritom007/ai-pr-review@v1
        with:
          api-key: ${{ secrets.INPUT_API_KEY }}
          model-name: "llama3-70b-8192"
          base-url: "https://api.groq.com/openai/v1"
          custom-chunk-prompt: |
            Review the following code changes with focus on:
            1. Security vulnerabilities
            2. Performance optimizations
            3. Code style consistency
            
            Format findings as:
            - [SEVERITY] [TYPE] Line X: Description
          custom-summary-prompt: |
            Generate a security-focused summary:
            1. List all security findings
            2. Group by vulnerability type
            3. Include remediation steps
            
            Format as:
            ## Security Findings
            ### [Vulnerability Type]
            - [Severity] Description (Line X)
```

## Example Output 📝

## .github/workflows 
### test.yml
- [LOW] [Code Quality] Line 1-31: The file name 'test.yml' might be misleading as it seems to be a workflow for AI PR review rather than a test. Consider renaming it to something more descriptive like 'ai-pr-review.yml'. 
```yml
name: AI PR Review
```
- [MEDIUM] [Security] Line 22: The 'github-token' is passed as an input to the 'ai-pr-review' action. Although it's using the 'secrets.GITHUB_TOKEN', ensure that the 'pritom007/ai-pr-review' action handles the token securely.
```yml
      - name: AI PR Review
        uses: pritom007/ai-pr-review@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```
- [MEDIUM] [Service boundaries] Line 20-30: The workflow uses an external action 'pritom007/ai-pr-review' which interacts with an external API 'https://api.groq.com/openai/v1'. This might introduce service boundary issues, such as dependency on the external API or potential data leaks.
```yml
      - name: AI PR Review
        uses: pritom007/ai-pr-review@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          ref: ${{ github.event.ref }}
          api-key: ${{ secrets.API_KEY }}
          api-url: https://api.groq.com/openai/v1
```

- [HIGH] [Error handling] Line 19-30: There is no error handling mechanism in place for the 'ai-pr-review' action. Consider adding try-except blocks or error handling mechanisms to handle potential errors or exceptions raised by the action.
```yml
      - name: AI PR Review
        uses: pritom007/ai-pr-review@v1
        with:
          # ...

```

## Roadmap 🗺️

- [ ] Support for customizable prompt templates
- [ ] Enhanced security review capabilities
- [ ] Integration with additional code hosting platforms

## Troubleshooting 🛠️

### Common Errors

### 401 Unauthorized

- Ensure your secret key matches the configured workflow input

Test your API key:

```bash
curl -H "Authorization: Bearer $KEY" $BASE_URL/models
```

### Model Not Found

- Verify exact model ID and regional availability

## Long Response Times

- Lower `max-tokens` or switch to lighter models

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> **Important:** AI reviews should complement human judgment, not replace it. Always manually verify critical changes.
