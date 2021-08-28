# !zsh
# setup code:
# python3 -m venv .venv
. .venv/bin/activate && pytest

echo "Deployed on Staging"
http https://manager-book-dev.azurewebsites.net/
http https://manager-book-dev.azurewebsites.net/manager-book-anchor
http https://manager-book-dev.azurewebsites.net/random-page/a-anchor

echo "Deployed on Prod"

http https://manager-book.azurewebsites.net/
http https://manager-book.azurewebsites.net/manager-book-anchor
http https://manager-book.azurewebsites.net/random-page/a-anchor

Pushing to deploy-prod deploys to  https://manager-book.azurewebsites.net
