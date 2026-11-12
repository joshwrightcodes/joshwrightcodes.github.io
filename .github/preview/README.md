# Pull request previews

Each pull request from this repository gets a preview at `https://site-pr-<n>.wright.codes`. A comment on the pull request carries the link, and each push updates the preview. Anyone with the link can open the preview. Search engines are told not to index it.

Draft pull requests and pull requests from forks do not get a preview.

The preview is deleted when the pull request closes. A daily sweep deletes any preview that a failed teardown left behind.

## Set up the previews

Do these steps one time. An engineer only needs to create the token and set the two secrets.

1. In the Cloudflare dashboard, open **Manage Account**, then **Account API Tokens**.
2. Create a custom token with the name `site-pr-preview` and these permissions:

   | Scope | Permissions |
   |---|---|
   | Account | Workers · Admin, Account Settings · Read |
   | Zone `wright.codes` | Workers Routes · Edit |

3. Create the environment `preview-pr` in this repository, and limit it to the `main` branch.
4. Pipe the token from your secret manager to GitHub. Do not write it to a file:

   ```sh
   <print-token-command> | gh secret set CLOUDFLARE_API_TOKEN --env preview-pr
   ```

5. Set the account ID in the same way:

   ```sh
   gh secret set CLOUDFLARE_ACCOUNT_ID --env preview-pr --body "<account-id>"
   ```

## Replace the token

Roll the token in the Cloudflare dashboard, and repeat step 4. Then start the sweep to confirm that the new token works:

```sh
gh workflow run pr-preview-deploy.yml --ref main
```

## Run the checks

```sh
node --test .github/scripts/pr-preview-config.test.mjs
```
