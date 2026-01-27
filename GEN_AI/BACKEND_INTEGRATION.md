# 🔗 Backend Integration Guide

## Understanding pets-backend

The pets-backend is a **GraphQL server** that provides:
- Authentication APIs (login, etc.)
- User management
- GraphQL endpoints

## Integration Strategy

Your GEN_AI app (FastAPI) can connect to pets-backend (GraphQL) in two ways:

### Option 1: Keep Separate (Recommended)
- GEN_AI: FastAPI backend (video generation, pet detection)
- pets-backend: GraphQL backend (authentication, user management)
- Frontend connects to both

### Option 2: Integrate into GEN_AI
- Add GraphQL support to GEN_AI
- Merge authentication from pets-backend
- Single unified backend

---

**Let me analyze the pets-backend structure first...**
