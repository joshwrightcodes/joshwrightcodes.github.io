#!/usr/bin/env bash
# Deletes a pull request preview: the custom domains of the site-pr-<n> Worker, then the Worker.
# It is safe to run again. It only touches site-pr-<number>.
#   pr-preview-teardown.sh <pr-number>    (needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID)
set -euo pipefail
pr="${1:?pr number}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "not a PR number: $pr" >&2; exit 1; }
name="site-pr-${pr}"
api="https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers"
auth=(-H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}")
response="$(mktemp)"
trap 'rm -f "$response"' EXIT

for id in $(curl -fsS "${auth[@]}" "${api}/domains?service=${name}" | jq -r '.result[]?.id'); do
  curl -fsS -X DELETE "${auth[@]}" "${api}/domains/${id}" >/dev/null
  echo "deleted custom domain ${id} of ${name}"
done

code=$(curl -s -o "$response" -w '%{http_code}' -X DELETE "${auth[@]}" "${api}/scripts/${name}?force=true")
case "$code" in
  200) echo "deleted Worker ${name}" ;;
  404) echo "Worker ${name} was already gone" ;;
  *) echo "deleting ${name} failed: HTTP ${code}" >&2; cat "$response" >&2; exit 1 ;;
esac
