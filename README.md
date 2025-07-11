# Infinite Vocabulary - Backend API

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic"/>
  <img src="https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase"/>
  <img src="https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white" alt="Google Cloud"/>
</p>

This repository contains the backend service for the Infinite Vocabulary application. It is a robust Flask-based API designed to manage users, words, categories, and administrative functions, utilizing Google Firestore as its database.

---

## ✨ Key Features

This application goes beyond basic CRUD operations to provide a feature-rich experience:

- **Complete User & Word Management**: Full lifecycle management for users and their vocabulary words, including descriptions and examples.
- **Categorization System**: Users can create custom categories and link words to them for better organization.
- **Scoring & Leaderboard**: Tracks user scores and provides a public leaderboard.
- **Tiered Admin Roles**: A secure, two-tier admin system (`admin`, `super-admin`) with distinct permissions for managing the platform and its users.
- **Full Student Management**: Admins can take users under their custody, manage their progress, and assign assessment scores.
- **Comprehensive Search**: A dedicated search endpoint for finding words and categories simultaneously.
- **Secure Authentication**: All endpoints are protected using Firebase JWT-based authentication.

---

## 🏛️ Architecture

The API is built using a **Layered Architecture** (also known as N-Tier Architecture). This pattern ensures a strong separation of concerns, making the application more maintainable, scalable, and testable. The three core layers are `Routes`, `Services`, and the `Data Access Layer (DAL)`.

#### Conversation Pattern Between Layers (Modern Implementation)

The layers communicate in a clear, top-down pattern where each layer is only aware of the one directly beneath it.

> - **Routes** asks **Schema** "is this request valid?"
>   - → **Schema** validates and returns clean data
> - **Routes** passes the validated Schema to the **Service**
> - **Service** asks **Factory** "create a Category with business validation from this validated schema"
>   - → **Factory** validates business rules and creates a typed Category model
> - **Service** takes the model and asks the **DAL** to save it
> - **Service** returns the model back to **Routes**
> - **Routes** calls `category.model_dump(by_alias=True)` for automatic JSON conversion

> **Note**: The project currently contains two co-existing architectural patterns. The "Modern" Pydantic-based pattern described above is the target architecture, while a "Legacy" pattern exists in the `words` module. For more details, see the [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) file.

---

## 🚀 Setup and Running Instructions

Follow these steps to get the backend server running on your local machine for development.

### 1. Prerequisites

- **Node.js and npm**: Required to install the Firebase CLI.
- **Python 3.10+**
- A **Google Cloud Platform (GCP) project** with Firebase enabled.

### 2. Install Firebase CLI

The Firebase Command Line Interface is required to run the local emulators. Install it globally and log in to your Firebase account.

```bash
npm install -g firebase-tools
firebase login
```

### 3. Clone the Repository & Setup Environment

```bash
# Clone this repository
git clone https://github.com/moyeh04/infinite_vocab
cd infinite_vocab

# Create a Python virtual environment
python3 -m venv venv

# Activate it (on macOS/Linux)
source venv/bin/activate
```

### 4. Install Dependencies

This project uses `requirements.txt` for dependency management.

```bash
pip install -r requirements.txt
```

> **Note on `pyproject.toml`**: While `pyproject.toml` is the modern standard for Python projects (used with tools like Poetry or PDM), this project is configured to use the traditional `venv` and `pip` workflow, which is perfectly suitable.

### 5. Configure Firebase Service Account

The Python backend needs a service account key to communicate with Google Cloud services, even when using local emulators.

1. In your Google Cloud project, navigate to **IAM & Admin > Service Accounts**.
2. Create a new service account or select an existing one.
3. Go to the **Keys** tab, click **Add Key**, and create a new **JSON** key.
4. A JSON file will be downloaded. **Rename this file to `serviceAccountKey.json`** and place it in the root directory of this project.

**⚠️ Important**: The `serviceAccountKey.json` file contains sensitive credentials and should **NEVER** be committed to version control. The `.gitignore` file is already configured to ignore it.

### 6. Initialize and Run Firebase Emulators

First, initialize the emulators for this project.

```bash
# Run this from the project root
firebase init emulators
```

When prompted, select **only** the **Authentication Emulator** and the **Firestore Emulator**. Use the default ports. This will create a `firebase.json` file.

Now, in a **separate terminal window**, start the emulators:

```bash
firebase emulators:start --only auth,firestore
```

Keep this terminal running. The emulators are now active.

### 7. Configure Environment & Run the Application

#### A) First-Time Setup

In your **original terminal** (where you activated the virtual environment in step 3), use the provided helper script to set the necessary environment variables:

```bash
# This script points the app to the local emulators and the service account key
source ./set_env.sh local
```

Then, run the Flask application:

```bash
flask run
```

#### B) Quick Start (For Subsequent Sessions)

When you open a new terminal session to work on the project, you can use this single command to activate the virtual environment and set the environment variables at the same time:

```bash
# Activate venv AND set environment variables for local development
source venv/bin/activate && source ./set_env.sh local
```

Then, simply run the app:

```bash
flask run
```

The API will now be running and available at `http://127.0.0.1:5000`.

---

## 🗺️ API Endpoints Summary

The API is organized into several modules using Flask Blueprints:

- `/api/v1/users`: User registration, profile management, and leaderboard.
- `/api/v1/admin`: Admin-specific actions like listing/managing users and students.
- `/api/v1/words`: Full CRUD operations for words and their sub-collections.
- `/api/v1/categories`: Full CRUD for categories and linking words to them.
- `/api/v1/search`: Global search for words and categories.

A complete and interactive API specification is available in the OpenAPI format, which can be imported into tools like Postman or Insomnia.
