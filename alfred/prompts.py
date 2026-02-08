"""
Code review prompts for different analysis types
"""

SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.

Your reviews should be:
- Specific and actionable
- Prioritized by severity (Critical, High, Medium, Low)
- Constructive and educational
- Focused on real issues, not nitpicks

For each issue found, provide:
1. Severity level
2. Line number (if applicable)
3. Clear description of the problem
4. Why it's a problem
5. Suggested fix with code example
"""

def get_review_prompt(code: str, filename: str, focus: str = "general") -> str:
    """Generate a review prompt based on focus area"""
    
    focus_instructions = {
        "general": "Review for bugs, code quality, best practices, and potential improvements.",
        "security": "Focus on security vulnerabilities, injection risks, authentication issues, and data exposure.",
        "performance": "Analyze for performance bottlenecks, inefficient algorithms, and resource usage.",
        "style": "Check code style, naming conventions, documentation, and readability.",
        "bugs": "Hunt for logical errors, edge cases, null pointer issues, and runtime errors."
    }
    
    instruction = focus_instructions.get(focus, focus_instructions["general"])
    
    return f"""Please review this {filename} file.

Focus: {instruction}

Code to review:
```
{code}
```

Provide your review in this format:

## Summary
[Brief overview of code quality]

## Issues Found

### Critical Issues
[List critical bugs/security issues]

### High Priority
[Important improvements needed]

### Medium Priority
[Good-to-have improvements]

### Low Priority
[Style and minor improvements]

## Positive Aspects
[What's done well]

## Overall Score: X/10
[Your rating with brief justification]
"""


def get_pr_review_prompt(pr_info: dict, diff: str, focus: str = "general") -> str:
    """
    Generate a review prompt for a Pull Request
    
    Args:
        pr_info: PR metadata dict
        diff: Unified diff string
        focus: Review focus area
        
    Returns:
        Formatted prompt string
    """
    focus_instructions = {
        "general": "Review for bugs, code quality, best practices, breaking changes, and potential issues.",
        "security": "Focus on security vulnerabilities, injection risks, authentication issues, and data exposure in the changes.",
        "performance": "Analyze the changes for performance impact, inefficient algorithms, and resource usage.",
        "style": "Check code style consistency, naming conventions, and readability in the changes.",
        "bugs": "Hunt for logical errors, edge cases, race conditions, and runtime errors introduced by the changes."
    }
    
    instruction = focus_instructions.get(focus, focus_instructions["general"])
    
    # Truncate diff if too large
    max_diff_size = 100000
    if len(diff) > max_diff_size:
        diff = diff[:max_diff_size] + f"\n\n[... diff truncated, total size: {len(diff)} chars]"
    
    return f"""Please review this Pull Request.

## PR Information
- **Number:** #{pr_info.get('number', 'N/A')}
- **Title:** {pr_info.get('title', 'N/A')}
- **Author:** {pr_info.get('author', 'N/A')}
- **Files Changed:** {pr_info.get('files_changed', 0)}
- **Additions:** +{pr_info.get('additions', 0)}
- **Deletions:** -{pr_info.get('deletions', 0)}
- **Description:** {pr_info.get('description', 'No description provided')[:500]}

## Review Focus
{instruction}

## Changes (Unified Diff)
```diff
{diff}
```

Provide your review in this format:

## 📋 Summary
[Brief overview of the PR - what does it do? Is it good to merge?]

## ⚠️ Issues Found

### 🚨 Critical Issues
[Blocking issues that must be fixed before merging]

### ⚡ High Priority
[Important issues that should be addressed]

### 💡 Medium Priority
[Good-to-have improvements]

### 🎨 Low Priority / Suggestions
[Style improvements and minor suggestions]

## ✅ Positive Aspects
[What's done well in this PR]

## 🎯 Recommendation
- [ ] **Approve** - Ready to merge
- [ ] **Request Changes** - Issues must be fixed
- [ ] **Comment** - Suggestions but okay to merge

[Your recommendation with brief justification]

## 📊 Overall Quality Score: X/10
[Brief explanation of the score]
"""

def get_git_diff_review_prompt(diff: str, focus: str = "general") -> str:
    """
    Generate a review prompt for git diff
    
    Args:
        diff: Git diff output (unified diff format)
        focus: Review focus area
        
    Returns:
        Formatted prompt string
    """
    focus_instructions = {
        "general": "Review for bugs, code quality, breaking changes, and potential issues in the changes.",
        "security": "Focus on security implications of these changes: new vulnerabilities, exposed data, auth issues.",
        "performance": "Analyze performance impact of these changes: new bottlenecks, inefficient code, resource usage.",
        "style": "Check code style consistency, naming conventions, and readability of the changes.",
        "bugs": "Hunt for bugs introduced by these changes: logic errors, edge cases, potential runtime issues."
    }
    
    instruction = focus_instructions.get(focus, focus_instructions["general"])
    
    # Truncate diff if too large
    max_diff_size = 50000  # ~50KB
    if len(diff) > max_diff_size:
        diff = diff[:max_diff_size] + f"\n\n[... diff truncated, total size: {len(diff)} chars]"
    
    return f"""Please review these git changes.

## Review Focus
{instruction}

## Git Diff
```diff
{diff}
```

Provide your review in this format:

## 📋 Summary
[Brief overview of the changes - what was modified and why?]

## ⚠️ Issues Found

### 🚨 Critical Issues
[Breaking changes, bugs, or security issues that must be fixed]

### ⚡ High Priority
[Important issues that should be addressed]

### 💡 Medium Priority
[Good-to-have improvements]

### 🎨 Low Priority / Suggestions
[Style improvements and minor suggestions]

## ✅ Positive Aspects
[What's done well in these changes]

## 🎯 Recommendation
- [ ] **Safe to commit** - Changes look good
- [ ] **Fix issues first** - Address problems before committing
- [ ] **Needs discussion** - Changes require team input

[Your recommendation with brief justification]

## 📊 Overall Quality Score: X/10
[Brief explanation of the score]
"""