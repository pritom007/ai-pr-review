import os
from openai import OpenAI
import github3

def get_pr_diff(github_token, repo_name, pr_number):
    gh = github3.login(token=github_token)
    owner, repo_name = repo_name.split('/')
    repo = gh.repository(owner, repo_name)
    pr = repo.pull_request(pr_number)
    # Get comparison between base and head
    comparison = repo.compare_commits(pr.base.sha, pr.head.sha)
    diff_text = ""
    
    for file in comparison.files:
        diff_text += f"File: {file['filename']}\n"
        diff_text += f"{file['patch']}\n\n"
    
    return diff_text[:12000]  # Truncate to avoid token limits

def generate_review(diff_text, config):
    client = OpenAI(base_url=config.get('base_url', 'https://api.openai.com'),
                    api_key=config['api_key'])
    
    print(config.get('base_url', 'https://api.openai.com'))
    print(config['api_key'])
    response = client.chat.completions.create(
        model=config['model_name'],
        messages=[
            {"role": "system", "content": "You are a senior software engineer reviewing a pull request."},
            {"role": "user", "content": f"""Please review this code diff and provide feedback. Consider:
- Code quality and best practices
- Potential bugs and edge cases
- Security vulnerabilities
- Performance improvements
- Maintainability and readability
- Documentation and comments
- Style consistency

Write the review in {config['language']}. Format as markdown. Highlight important points.

Diff:
{diff_text}"""}
        ],
        temperature=config['temperature'],
        max_tokens=config['max_tokens']
    )

    return response.choices[0].message.content

def main(github_token, repo_name, pr_number, config):
    # Get PR diff
    diff_text = get_pr_diff(github_token, repo_name, pr_number)
    
    # Generate review
    review = generate_review(diff_text, config)
    
    # Post review as comment
    gh = github3.login(token=github_token)
    owner, repo_name = repo_name.split('/')
    repo = gh.repository(owner, repo_name)
    pr = repo.pull_request(pr_number)
    pr.create_comment(review)

if __name__ == "__main__":
    # Get inputs
    config = {
        'api_key': os.getenv('INPUT_API_KEY'),
        'model_name': os.getenv('INPUT_MODEL_NAME', 'gpt-4'),
        'base_url': os.getenv('INPUT_BASE_URL'),
        'temperature': float(os.getenv('INPUT_TEMPERATURE', '0.7')),
        'max_tokens': int(os.getenv('INPUT_MAX_TOKENS', '1000')),
        'language': os.getenv('INPUT_LANGUAGE', 'English')
    }
    
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = int(os.getenv('GITHUB_REF').split('/')[-2])
    
    main(github_token, repo_name, pr_number, config)