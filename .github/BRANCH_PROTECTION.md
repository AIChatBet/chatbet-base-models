# Branch Protection Rules Setup

This document outlines the recommended branch protection rules for the ChatBet Base Models repository to ensure code quality and prevent breaking changes.

## 🛡️ Branch Protection Configuration

### For `main` branch:

Go to: **Settings** → **Branches** → **Add rule** or **Edit rule**

#### Required Settings:

1. **Branch name pattern**: `main`

2. **Restrict pushes that create files that are larger than 100MB**: ✅ Checked

3. **Require a pull request before merging**: ✅ Checked
   - **Require approvals**: 1 (minimum)
   - **Dismiss stale PR approvals when new commits are pushed**: ✅ Checked
   - **Require review from CODEOWNERS**: ✅ Checked (if you have CODEOWNERS file)

4. **Require status checks to pass before merging**: ✅ Checked
   - **Require branches to be up to date before merging**: ✅ Checked
   - **Status checks that are required**:
     - `test (3.10)` - Python 3.10 tests
     - `test (3.11)` - Python 3.11 tests
     - `test (3.12)` - Python 3.12 tests
     - `test-summary` - Test completion summary

5. **Require conversation resolution before merging**: ✅ Checked

6. **Require signed commits**: ✅ Checked (recommended)

7. **Include administrators**: ✅ Checked

8. **Allow force pushes**: ❌ Unchecked

9. **Allow deletions**: ❌ Unchecked

### For `develop` branch:

1. **Branch name pattern**: `develop`

2. **Require a pull request before merging**: ✅ Checked
   - **Require approvals**: 1 (minimum)

3. **Require status checks to pass before merging**: ✅ Checked
   - **Require branches to be up to date before merging**: ✅ Checked
   - **Status checks that are required**:
     - `test (3.11)` - At minimum Python 3.11 tests
     - `test-summary` - Test completion summary

4. **Allow force pushes**: ❌ Unchecked

### For `staging` branch:

1. **Branch name pattern**: `staging`

2. **Require a pull request before merging**: ✅ Checked

3. **Require status checks to pass before merging**: ✅ Checked
   - **Status checks that are required**:
     - `test (3.11)` - At minimum Python 3.11 tests

## 🚨 Critical Quality Gates

The CI pipeline will **FAIL** and **prevent merging** if:

- ❌ Any test fails (131 tests must pass)
- ❌ Code coverage is below **80%**

## 📋 Pre-merge Checklist

Before any code can be merged to `main`:

- [ ] All tests pass (131 tests minimum)
- [ ] Code coverage ≥ 80%
- [ ] At least 1 code review approval
- [ ] All conversations resolved
- [ ] Branch is up to date with target

## 🔄 Workflow Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:

1. **Runs on every push** to main, develop, staging
2. **Runs on every pull request** to main, develop, staging
3. **Tests across Python versions** 3.10-3.12
4. **Enforces 80% coverage minimum** with `--cov-fail-under=80`
5. **Reports coverage** to Codecov
6. **Blocks merging** if any test fails or coverage drops

## 🛠️ Setup Commands

To configure these rules via GitHub CLI:

```bash
# Enable branch protection for main
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test (3.11)","test-summary"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null

# Enable branch protection for develop  
gh api repos/:owner/:repo/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test (3.11)"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

## 📝 Notes

- **Coverage threshold**: Set to 80% minimum, but current project has much higher coverage
- **Multi-Python testing**: Ensures compatibility across supported Python versions 3.10-3.12
- **Simple but effective**: Focuses on core quality - tests and coverage
- **Test summary**: Provides clear summary of test execution results

This configuration ensures that only well-tested, high-quality code reaches the main branch.