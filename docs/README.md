# Documentation Index

Welcome to the V3Trading project documentation. This directory contains detailed guides for different aspects of the project.

## Documentation Structure

### 📚 Core Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Getting started, development workflow, local setup | Developers (new & existing) |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Project structure, architecture decisions | Developers, Technical leads |
| [AUTHENTICATION.md](./AUTHENTICATION.md) | OAuth flow, security implementation | Developers, Security reviewers |
| [API.md](./API.md) | API endpoints, data models, examples | Frontend developers, API consumers |
| [UI_FRAMEWORK.md](./UI_FRAMEWORK.md) | PrimeVue integration, components, theming | Frontend developers, Designers |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Docker, CI/CD, production deployment | DevOps, Deployment engineers |
| [RELEASES.md](./RELEASES.md) | Release management, versioning | Release managers, DevOps |

## Quick Links

### 🚀 Getting Started
New to the project? Start here:
1. [Development Setup](./DEVELOPMENT.md#getting-started)
2. [Running the Application](./DEVELOPMENT.md#running-the-application)
3. [Google OAuth Setup](./AUTHENTICATION.md#configuration)

### 🏗️ Building Features
Adding new functionality:
1. [Frontend Component Guide](./DEVELOPMENT.md#adding-new-features)
2. [Backend Endpoint Guide](./DEVELOPMENT.md#adding-new-features)
3. [State Management](./DEVELOPMENT.md#state-management)
4. [UI Components](./UI_FRAMEWORK.md)

### 🔐 Security & Auth
Understanding authentication:
1. [OAuth Flow](./AUTHENTICATION.md#google-oauth-flow)
2. [Security Features](./AUTHENTICATION.md#security-features)
3. [Route Guards](./AUTHENTICATION.md#route-guards)

### 📡 API Integration
Working with the API:
1. [API Endpoints](./API.md#endpoints)
2. [Data Models](./API.md#data-models)
3. [Response Examples](./API.md#api-response-examples)

### 🎨 UI Development
Creating beautiful interfaces:
1. [PrimeVue Components](./UI_FRAMEWORK.md#primevue-integration)
2. [Layout System](./UI_FRAMEWORK.md#layout-system)
3. [Dashboard Widgets](./UI_FRAMEWORK.md#dashboard)
4. [Theming](./UI_FRAMEWORK.md#theme-configuration)

### 🚢 Deployment
Deploying to production:
1. [Docker Setup](./DEPLOYMENT.md#docker-configuration)
2. [CI/CD Pipeline](./DEPLOYMENT.md#cicd-pipeline)
3. [Creating Releases](./RELEASES.md#creating-a-release)
4. [SSL/HTTPS Setup](./DEPLOYMENT.md#ssltls-configuration-https)

## Document Maintenance

### When to Update

| Scenario | Document to Update |
|----------|-------------------|
| Added new API endpoint | [API.md](./API.md) |
| Changed project structure | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Modified OAuth flow | [AUTHENTICATION.md](./AUTHENTICATION.md) |
| Added UI component/widget | [UI_FRAMEWORK.md](./UI_FRAMEWORK.md) |
| Changed deployment process | [DEPLOYMENT.md](./DEPLOYMENT.md) |
| Updated development workflow | [DEVELOPMENT.md](./DEVELOPMENT.md) |
| Modified release process | [RELEASES.md](./RELEASES.md) |

### Documentation Standards
- Use Markdown formatting
- Include code examples where relevant
- Keep examples up-to-date with codebase
- Add links between related documents
- Update "Last Updated" date when making changes
- Test all commands/examples before documenting

## Contributing to Documentation

When adding or updating documentation:
1. Ensure accuracy with current codebase
2. Use clear, concise language
3. Include practical examples
4. Add links to related sections
5. Update this index if adding new documents
6. Test all code examples
7. Update the main [CLAUDE.md](../CLAUDE.md) if adding major sections

## Need Help?

- **Project Overview**: See [CLAUDE.md](../CLAUDE.md) in the root directory
- **Code Issues**: Check [DEVELOPMENT.md](./DEVELOPMENT.md#troubleshooting)
- **Deployment Issues**: Check [DEPLOYMENT.md](./DEPLOYMENT.md#troubleshooting)
- **Contact**: David P. Brazda (davidbrazda61@gmail.com)

---

**Last Updated**: October 8, 2025
