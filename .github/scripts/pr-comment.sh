#!/usr/bin/env bash
# Keeps one preview comment on a pull request. It edits the comment that starts with $MARKER, or posts a new one.
#   pr-comment.sh <pr-number> <body> [--only-update]    (needs GH_TOKEN, GITHUB_REPOSITORY and MARKER)
set -euo pipefail
pr="${1:?pr number}"
body="${2:?body}"
only_update="${3:-}"
id=$(gh api --paginate "repos/${GITHUB_REPOSITORY}/issues/${pr}/comments" \
  -q ".[] | select(.user.type == \"Bot\" and (.body | startswith(\"${MARKER}\"))) | .id" | head -n 1)
if [ -n "$id" ]; then
  gh api -X PATCH "repos/${GITHUB_REPOSITORY}/issues/comments/${id}" -f body="$body" >/dev/null
  echo "updated comment ${id}"
elif [ "$only_update" != "--only-update" ]; then
  gh api -X POST "repos/${GITHUB_REPOSITORY}/issues/${pr}/comments" -f body="$body" >/dev/null
  echo "posted the preview comment"
fi
