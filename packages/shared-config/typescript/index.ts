"""
Shared Configuration - TypeScript/Node.js
Shared frontend tooling configuration (ESLint, TypeScript, Vite).
"""
import json


def get_eslint_config() -> dict:
    """Return shared ESLint configuration."""
    return {
        "env": {
            "browser": True,
            "es2022": True,
            "node": True,
        },
        "extends": [
            "eslint:recommended",
            "plugin:@typescript-eslint/recommended",
        ],
        "parser": "@typescript-eslint/parser",
        "plugins": ["@typescript-eslint"],
        "rules": {
            "@typescript-eslint/no-unused-vars": "warn",
            "@typescript-eslint/no-explicit-any": "warn",
        },
    }


def get_tsconfig_extends() -> dict:
    """Return shared TypeScript configuration extends."""
    return {
        "compilerOptions": {
            "target": "ES2022",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
        }
    }
