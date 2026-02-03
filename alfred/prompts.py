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