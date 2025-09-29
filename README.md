# GitHub Issue Digest Bot

🤖 Automated GitHub Issues and PRs digest tool that sends you daily email summaries of issues and PRs you need to focus on.

## ✨ Features

- 📧 **Daily Email Digest**: Automatically sends Issues and PRs summaries to your email
- 🔍 **Smart Filtering**: Supports priority labels, exclude labels, and assignee filtering
- 📋 **PR Support**: Shows both PRs that need review and issues that need attention
- 🎨 **Beautiful Interface**: HTML formatted emails with grouped display and color coding
- ⚙️ **Flexible Configuration**: Customize query conditions and email settings via GitHub Secrets
- 🕐 **Scheduled Execution**: Runs automatically daily with manual trigger support

## 🚀 Quick Start

### 1. Fork this Repository

Click the "Fork" button in the top right corner to fork this repository to your GitHub account.

### 2. Configure GitHub Secrets

Go to your repository Settings > Secrets and variables > Actions, and add the required secrets.

**Required secrets:**
- `GH_TOKEN` - GitHub Personal Access Token
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` - Email server configuration
- `EMAIL_FROM`, `EMAIL_TO` - Email addresses

**Optional secrets (with defaults):**
- `SEARCH_QUERIES` - Custom issue search queries
- `PR_QUERIES` - Custom PR search queries  
- `PRIORITY_LABELS` - Priority labels to filter by
- `EXCLUDE_LABELS` - Labels to exclude
- `EXCLUDE_ASSIGNEES` - Assignees to exclude

📋 **See [example.env](example.env) for detailed configuration examples and all available options.**

### 3. Enable Workflow

The workflow will run automatically daily at UTC 16:00. You can also trigger it manually:

1. Go to the Actions page
2. Select "Daily GitHub Issue Digest"
3. Click "Run workflow"

## 📧 Email Example

```
Daily GitHub Issues & PRs Digest
Generated at 2025-01-15 16:00 UTC

📋 Pull Requests (3)
- feat: add user authentication system
- fix: resolve memory leak in data processing
- docs: update API documentation

🐛 Issues (5)
- Add dark mode support to the application
- Improve error handling for network requests
- Optimize database queries for better performance
- Add unit tests for user management module
- Update dependencies to latest versions
...
```

## 🔧 Configuration

The bot is highly customizable through GitHub Secrets. You can configure:

- **Search queries** for issues and PRs
- **Label filtering** (priority and exclude labels)
- **Assignee filtering** 
- **Email settings** (SMTP server, addresses)
- **Result limits** (max issues/PRs per digest)

📋 **For detailed configuration examples, see [.env.example](.env.example)**

### Key Features:
- **Flexible queries**: Use GitHub's search syntax for precise filtering
- **Label-based filtering**: Show/hide items based on labels
- **Multiple repositories**: Query across multiple repos
- **Time filtering**: Filter by creation/update dates
- **Custom email settings**: Works with Gmail, Outlook, and other SMTP providers

## 🛠️ Local Development

### Requirements

- Python 3.11+
- pip

### Install Dependencies

```bash
pip install requests python-dateutil
```

### Local Testing

```bash
# Set environment variables
export GH_TOKEN="your_github_token"
export SEARCH_QUERIES="is:issue is:open no:assignee"
export PR_QUERIES="is:pr is:open review-requested:@me"
export PRIORITY_LABELS="enhancement,feature"
export EXCLUDE_LABELS="low-priority"
export MAX_ISSUES="10"
export MAX_PRS="10"

# Run the script
python digest.py --out test_digest.html
```

## 📁 Project Structure

```
├── .github/
│   └── workflows/
│       └── daily-issue-digest.yml    # GitHub Actions workflow
├── digest.py                         # Main script
├── example.env                       # Configuration examples
└── README.md                         # Project documentation
```

## 🔍 Troubleshooting

### Common Issues

1. **Email sending failed**
   - Check if SMTP configuration is correct
   - Verify email password or app-specific password
   - Check network connection

2. **GitHub API access failed**
   - Verify `GH_TOKEN` is correct
   - Check if token permissions are sufficient
   - Confirm repository access permissions

3. **Empty query results**
   - Check if query syntax is correct
   - Verify repository names and permissions
   - Adjust query conditions

### Debugging Methods

1. **View workflow logs**
   - Go to Actions page
   - Click on failed runs
   - View detailed logs

2. **Local testing**
   - Use local environment variables
   - Run `python digest.py` to test

3. **Manual trigger**
   - Manually run workflow in Actions page
   - Check if email is received

## 🤝 Contributing

Contributions are welcome! Please feel free to submit Issues and Pull Requests.

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [GitHub API](https://docs.github.com/en/rest) - For fetching Issues and PRs data
- [dawidd6/action-send-mail](https://github.com/dawidd6/action-send-mail) - For sending emails
- [GitHub Actions](https://github.com/features/actions) - For automation workflows

## 📞 Support

If you encounter issues or have suggestions, please:

1. Check the [Issues](https://github.com/Shan533/Github-Issue-Digest-Bot/issues) page
2. Create a new issue describing your problem
3. Or contact the maintainer directly

---

⭐ If this project helps you, please give it a star!
