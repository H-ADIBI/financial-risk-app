# Deploying to Azure

This app is stateless per-session (portfolio state lives in Streamlit's
session state, not a database), which makes it a good fit for either
**Azure App Service** (simplest) or **Azure Container Apps** (more
control, scales to zero). Both paths below start from the same
`deployment/Dockerfile`.

## 0. Prerequisites

- Azure CLI installed and logged in (`az login`)
- An Azure Container Registry (ACR), or use `az acr build` which builds
  in the cloud without needing Docker locally
- Your Groq API key

## 1. Build and push the image

Run these from the **project root** (the Dockerfile lives in
`deployment/` but expects to be built with the project root as its
build context, so it can `COPY` the whole app):

```bash
az acr create --resource-group <rg> --name <youracrname> --sku Basic
az acr build --registry <youracrname> --image risk-studio:latest -f deployment/Dockerfile .
```

(Building locally with plain Docker instead: `docker build -f deployment/Dockerfile -t risk-studio:latest .`)

## 2a. Option A: Azure App Service (Web App for Containers)

```bash
az appservice plan create --name risk-studio-plan --resource-group <rg> --is-linux --sku B1

az webapp create \
  --resource-group <rg> \
  --plan risk-studio-plan \
  --name <your-app-name> \
  --deployment-container-image-name <youracrname>.azurecr.io/risk-studio:latest

az webapp config appsettings set \
  --resource-group <rg> \
  --name <your-app-name> \
  --settings GROQ_API_KEY=<your-key> WEBSITES_PORT=8000
```

Your app will be live at `https://<your-app-name>.azurewebsites.net`.

## 2b. Option B: Azure Container Apps (via the provided Bicep template)

```bash
az deployment group create \
  --resource-group <rg> \
  --template-file deployment/azure/container-app.bicep \
  --parameters acrLoginServer=<youracrname>.azurecr.io imageName=risk-studio:latest groqApiKey=<your-key>
```

The deployment output includes the app's public URL.

## Notes / next steps

- **Secrets**: never bake `GROQ_API_KEY` into the image. Both paths
  above inject it as an environment variable/secret at deploy time.
- **Scaling**: this demo app holds portfolio state in Streamlit session
  state per browser session, which is fine for a single instance. If you
  scale to multiple replicas behind a load balancer, either enable sticky
  sessions or move portfolio state into a shared store (e.g. Azure Cache
  for Redis) before scaling out.
- **CI/CD**: wire `az acr build` + `az webapp config container set` (or
  a Container Apps revision update) into a GitHub Actions workflow to
  deploy on every push to `main`.
- **Custom domain / TLS**: both App Service and Container Apps support
  custom domains with managed certificates via `az webapp config hostname`
  or `az containerapp hostname` commands.
