# !zsh
# setup code:
# python3 -m venv .venv
. .venv/bin/activate && pytest

echo "Press any key to test Dev"
read "a"
http http://localhost:7071
http http://localhost:7071/manager-book-anchor
http http://localhost:7071/random-page/a-anchor
http http://localhost:7071/random-page#inline-anchor

echo "Press any key to test Staging"
read "a"

http https://manager-book-dev.azurewebsites.net/
http https://manager-book-dev.azurewebsites.net/manager-book-anchor
http https://manager-book-dev.azurewebsites.net/random-page/a-anchor
http https://manager-book-dev.azurewebsites.net/random-page#inline-anchor

echo "Press any key to test Prod"
read "a"

http https://idvorkin.azurewebsites.net/
http https://idvorkin.azurewebsites.net/manager-book-anchor
http https://idvorkin.azurewebsites.net/random-page/a-anchor
http https://idvorkin./random-page#inline-anchor
echo "Done"
read "a"
