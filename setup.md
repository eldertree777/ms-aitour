# setting

## install

- vscode extentions > Azurite 설치 필요
- func start를 위한 설치 (Azure Functions Core Tools)
    - `bash npm install -g azure-functions-core-tools@4 --unsafe-perm true`
- az login을 위한 설치 (Azure CLI)
    - window
        - `bash winget install -e --id Microsoft.AzureCLI `
    - 직접 설치:
        - [Azure CLI](https://learn.microsoft.com/ko-kr/cli/azure/install-azure-cli-windows?view=azure-cli-latest&pivots=winget)

## todo action

- az login
    - `bash az login`
-

# Deployment (확인중)

- `bash func azure functionapp publish <APP_NAME> `
