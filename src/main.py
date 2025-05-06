import os
import re
import asyncio
import tiktoken
from openai import OpenAI
import github3
from typing import List, Dict
import logging

logging.basicConfig(level=logging.DEBUG)

# Configure these based on model limits
MAX_CHUNK_TOKENS = 6000
MAX_SUMMARY_TOKENS = 3000
MIN_FILE_TOKENS = 200

# Default prompts
DEFAULT_CHUNK_PROMPT = """You are an experienced code reviewer. Review the following code changes thoroughly:

1. Code Quality & Best Practices:
   - Check for SOLID principles adherence
   - Look for code smells and anti-patterns
   - Verify naming conventions and readability
   - Assess code duplication and DRY violations
   - Review function/method complexity and length

2. Security & Safety:
   - Identify potential security vulnerabilities
   - Check for proper input validation
   - Look for unsafe data handling
   - Verify authentication/authorization checks
   - Review error handling and logging practices

3. Performance & Scalability:
   - Analyze algorithm efficiency
   - Check for resource leaks
   - Review database query patterns
   - Look for potential bottlenecks
   - Assess memory usage patterns

4. Testing & Maintainability:
   - Verify test coverage
   - Check for testability issues
   - Review documentation quality
   - Assess code modularity
   - Look for maintainability concerns

Format your findings as:
- [SEVERITY: HIGH/MEDIUM/LOW] [CATEGORY] File:line - Description
  - Impact: Explain the potential impact
  - Suggestion: Provide specific improvement suggestions
  - Example: Show a code example if relevant

Focus on actionable feedback and specific improvements."""

DEFAULT_SUMMARY_PROMPT = """As a senior code reviewer, create a comprehensive review summary:

1. Overview:
   - Summarize the main changes and their purpose
   - Highlight critical areas that need attention
   - Identify patterns across multiple files

2. Key Findings:
   - Group issues by severity and category
   - Prioritize critical security and performance issues
   - Highlight architectural concerns
   - Note positive patterns and good practices

3. Recommendations:
   - Provide actionable improvement steps
   - Suggest specific refactoring opportunities
   - Recommend additional testing scenarios
   - List potential security hardening measures

Format the summary as:
## Overview
Brief summary of changes and key concerns

## Critical Issues
### [Category]
- [SEVERITY] Description
  - Impact: [Impact description]
  - Location: [File:line]
  - Recommendation: [Specific suggestion]

## Code Quality
### [File]
- [SEVERITY] [Type] Line X: Description
  - Current: [Code snippet]
  - Suggested: [Improved code example]

## Security & Performance
### [Category]
- [SEVERITY] Description
  - Risk: [Risk assessment]
  - Mitigation: [Specific steps]

## Positive Patterns
- [Pattern] - [Why it's good]
  - Example: [Code snippet]

Focus on providing clear, actionable feedback that helps improve code quality."""

def get_pr_diff(github_token: str, repo_name: str, pr_number: int) -> List[Dict]:
    """Retrieve PR diff with validation"""
    try:
        gh = github3.login(token=github_token)
        owner, repo_name = repo_name.split('/')
        repo = gh.repository(owner, repo_name)
        pr = repo.pull_request(pr_number)
        
        # Get actual diff text from GitHub API
        diff_response = repo._get(f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/files")
        files = []
        
        for file in diff_response.json():
            if not file['filename'].endswith(('png', 'jpg', 'jar')) and file['patch']:
                files.append({
                    'filename': file['filename'],
                    'patch': file['patch'],
                    'status': file['status'],
                    'changes': file['changes'],
                    'additions': file['additions'],
                    'deletions': file['deletions']
                })
        
        return files
        
    except Exception as e:
        logging.error(f"Diff retrieval failed: {str(e)}")
        return []

def is_binary_file(filename: str) -> bool:
    return bool(re.search(r'\.(bin|png|jpg|jar|zip|exe|dll)$', filename))

def chunk_files(files: List[Dict], tokenizer) -> List[List[Dict]]:
    """Group related files into context chunks"""
    if not files:  # Handle empty input
        return []
        
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    try:
        # Sort files by directory to group related files
        sorted_files = sorted(
            [f for f in files if f and f.get('filename')],  # Filter out None entries
            key=lambda x: os.path.dirname(x['filename'])
        )
        
        for file in sorted_files:
            content = f"{file['filename']}\n{file['patch']}"
            file_tokens = len(tokenizer.encode(content))
            
            if file_tokens > MIN_FILE_TOKENS:
                if current_tokens + file_tokens > MAX_CHUNK_TOKENS:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_tokens = 0
                
                current_chunk.append(file)
                current_tokens += file_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
            
    except Exception as e:
        print(f"Error chunking files: {e}")
        return []
    
    return chunks

async def process_chunk(chunk: List[Dict], config: Dict) -> str:
    """Analyze with strict context binding"""
    client = OpenAI(**config['openai_params'])
    
    # Build diff with line numbers
    diff_text = []
    for file in chunk:
        lines = file['patch'].split('\n')
        annotated = [f"File: {file['filename']} ({file['status']})"]
        annotated += [f"{i+1}: {line}" for i, line in enumerate(lines) if line]
        diff_text.append('\n'.join(annotated))
    
    full_diff = '\n\n'.join(diff_text)
    
    # Validate diff content
    if not full_diff.strip():
        logging.warning("Empty diff chunk skipped")
        return ""
    
    logging.debug(f"Processing chunk with {len(full_diff)} characters")
    
    response = client.chat.completions.create(
        model=config['model_name'],
        messages=[
            {"role": "system", "content": config['chunk_prompt']},
            {"role": "user", "content": f"CODE DIFF:\n{full_diff}\n\nANALYSIS REQUEST:\n{config['chunk_prompt']}"}
        ],
        temperature=0.3,  # More focused
        max_tokens=1500
    )
    
    return response.choices[0].message.content

async def synthesize_reviews(reviews: List[str], config: Dict) -> str:
    """Create final summary from chunk reviews"""
    client = OpenAI(**config['openai_params'])
    combined = "\n\n---\n\n".join(reviews)
    
    response = client.chat.completions.create(
        model=config['model_name'],
        messages=[
            {"role": "system", "content": config['summary_prompt']},
            {"role": "user", "content": combined}
        ],
        temperature=0.2,  # More deterministic for summary
        max_tokens=MAX_SUMMARY_TOKENS
    )
    
    return response.choices[0].message.content

async def main():
    config = {
        'openai_params': {
            'api_key': os.getenv('INPUT_API_KEY'),
            'base_url': os.getenv('INPUT_BASE_URL', 'https://api.openai.com')
        },
        'model_name': os.getenv('INPUT_MODEL_NAME', 'gpt-4'),
        'temperature': float(os.getenv('INPUT_TEMPERATURE', 0.7)),
        'max_tokens': int(os.getenv('INPUT_MAX_TOKENS', 1000)),
        'chunk_prompt': os.getenv('INPUT_CUSTOM_CHUNK_PROMPT', DEFAULT_CHUNK_PROMPT),
        'summary_prompt': os.getenv('INPUT_CUSTOM_SUMMARY_PROMPT', DEFAULT_SUMMARY_PROMPT)
    }
    
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    # Get PR data
    github_token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPOSITORY')
    pr_number = int(os.getenv('GITHUB_REF').split('/')[-2])
    
    files = get_pr_diff(github_token, repo_name, pr_number)
    chunks = chunk_files(files, tokenizer)
    
    # Process chunks in parallel
    chunk_reviews = await asyncio.gather(*[
        process_chunk(chunk, config) for chunk in chunks
    ])
    
    # Generate final summary
    final_report = await synthesize_reviews(chunk_reviews, config)
    
    # Post to GitHub
    gh = github3.login(token=github_token)
    owner, repo = repo_name.split('/')
    pr = gh.repository(owner, repo).pull_request(pr_number)
    pr.create_comment(final_report)

if __name__ == "__main__":
    asyncio.run(main())