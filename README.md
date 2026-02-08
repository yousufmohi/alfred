# Alfred 🤖

Alfred is a code reviewing AI agent that reviews your local code and GitHub PR's.

## ✨ Features

- **Local Code Reviews** - Review any file with AI analysis
- **GitHub PR Integration** - Review pull requests and post comments
- **Cost Tracking** - Monitor API spending with detailed breakdowns
- **Review History** - Search and replay past reviews

## 🚀 Quick Start

### Install & Build 🛠️

Clone the repository and run the install script:

**Windows (PowerShell):**
```powershell
git clone https://github.com/yousufmohi/alfred
cd alfred
.\install.ps1
```

**Mac/Linux:**
```bash
git clone https://github.com/yousufmohi/alfred
cd alfred
chmod +x install.sh
./install.sh
```

**Windows (CMD):**
```cmd
git clone https://github.com/yousufmohi/alfred
cd alfred
install.bat
```

### Initial Setup ⚙️

1. Get your Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
2. Run setup:
```bash
alfred setup
```
3. Paste your API key when prompted

**Optional:** Set your balance for tracking:
```bash
alfred balance set 10  # Set to your current balance
```

## 📖 Usage

### Core Commands

| Command | Description |
|---------|-------------|
| `alfred setup` | Configure Anthropic API key |
| `alfred review <file>` | Review a code file |
| `alfred review <file> --focus security` | Security-focused review |
| `alfred costs` | View cost tracking and usage |
| `alfred balance` | Check remaining API balance |
| `alfred history` | View past reviews |
| `alfred version` | Show version info |

### Code Review Examples

**Basic review:**
```bash
alfred review script.py
```

**Focus on specific areas:**
```bash
alfred review app.js --focus security     # Security issues
alfred review main.py --focus performance # Performance bottlenecks
alfred review api.py --focus bugs         # Bug hunting
alfred review utils.py --focus style      # Code style
```

**Review options:**
```bash
alfred review file.py --no-cost           # Hide cost info
alfred review file.py --verbose           # Detailed output
```

### GitHub Integration 🔗

**Login to GitHub:**
```bash
alfred github-login
```

**Review pull requests:**
```bash
alfred review-pr https://github.com/user/repo/pull/123
alfred review-pr 123                      # Auto-detects repo
alfred review-pr 123 --comment            # Post review as comment
alfred review-pr 123 --focus security     # Security-focused PR review
```

**Check GitHub status:**
```bash
alfred github-status                      # Check login status
alfred github-logout                      # Logout from GitHub
```

### Cost & Balance Tracking 💰

**Set your balance:**
```bash
alfred balance set 4.80                   # Update from Anthropic console
alfred balance                            # Check remaining balance
```

**View costs:**
```bash
alfred costs                              # Recent reviews
alfred costs --total                      # All-time statistics
alfred costs --limit 20                   # Last 20 reviews
```

### Review History 📚

**List reviews:**
```bash
alfred history                            # Recent reviews
alfred history --limit 20                 # Last 20 reviews
alfred history --file script.py           # All reviews of a file
```

**View past reviews:**
```bash
alfred history show 5                     # View review #5
alfred history search "SQL injection"     # Search reviews
alfred history stats                      # Statistics
```

## 🎯 Review Focus Areas

| Focus | What It Checks |
|-------|----------------|
| `general` | Overall code quality, bugs, and best practices |
| `security` | Vulnerabilities, injection risks, authentication issues |
| `performance` | Bottlenecks, inefficient algorithms, resource usage |
| `style` | Code style, naming, documentation, readability |
| `bugs` | Logic errors, edge cases, runtime issues |


## 📊 Example Workflow

```bash
# Setup (one time)
alfred setup
alfred balance set 10
alfred github-login

# Daily usage
alfred review src/main.py --focus security
alfred history                              # Check what you've reviewed
alfred balance                              # Check remaining credits

# PR review
alfred review-pr 456 --comment              # Review and comment on PR

# Cost check
alfred costs --total                        # See total spending
```

## 🛠️ Troubleshooting

**"No API key found"**
- Run `alfred setup` and enter your Anthropic API key

**"Not logged in to GitHub"**
- Run `alfred github-login` to authenticate

**"Insufficient balance"**
- Add credits at [console.anthropic.com](https://console.anthropic.com)
- Update balance: `alfred balance set <amount>`

---

