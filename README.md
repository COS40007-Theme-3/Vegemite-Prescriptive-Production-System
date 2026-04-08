<p align="center">
  <img src="./public/Vegemite.webp" alt="Vegemite Prescriptive Production System" width="120">
</p>

<h1 align="center">Vegemite Prescriptive Production System</h1>

<p align="center">
  An AI-driven prescriptive analytics system designed to optimize production efficiency and quality control within the manufacturing process.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
</p>

---

## Overview

The Vegemite Prescriptive Production System is a comprehensive decision-support platform that leverages machine learning to provide actionable insights for production operators. Unlike traditional descriptive tools, this system focuses on prescriptive analytics—identifying the optimal parameters to achieve desired quality outcomes and minimize downtime.

## Key Features

- **Real-time Monitoring**: centralized dashboard for production KPIs, machine health, and operational status.
- **Quality Prediction**: Estimating product quality metrics based on current machine input parameters.
- **Set-Point Optimization**: Recommending optimal machine settings to maximize yield and ensure consistency.
- **Risk Assessment**: Proactive identification of potential downtime risks and sensor instability.
- **Data Visualization**: High-fidelity charts for trend analysis, set-point deviations, and comparative performance.
- **Operational Interface**: Dedicated controls for machine configuration and parameter adjustments.

## Project Structure

```bash
├── app/               # Next.js App Router (Routes, Layouts, and API endpoints)
├── components/        # Reusable UI components and feature-specific widgets
│   ├── ui/            # Base design system components
│   └── charts/        # Specialized visualization components
├── models/            # Machine Learning artifacts and inference logic
├── data/              # Static configurations and regional datasets
├── lib/               # Shared utilities, constants, and logging services
├── hooks/             # Custom React hooks for state and data fetching
└── public/            # Static assets and media files
```

## Implementation Status

The current iteration of the system includes:

1.  **Production Intelligence**: A responsive web interface built with Next.js and Tailwind CSS.
2.  **Machine Learning Integration**: Built-in support for Task 1 (Quality Prediction) and Task 2 (Prescriptive Recommendation) models.
3.  **Real-time Analytics**: Hooks and services for monitoring machine stability and downtime risks.
4.  **Audit Logging**: Persistent activity logs for tracking manual adjustments and system-generated recommendations.
5.  **Design System**: A scalable component architecture based on professional design principles.

## Getting Started

### Prerequisites

- **Node.js** (v18.x or later)
- **pnpm** (Package manager used for this project)
- **Python** (v3.9 or later)

### 1. Setup Python Environment (Backend / Machine Learning)

The project relies on a Python script (`models/serve_recommend_sp.py`) acting as the AI engine behind Next.js API routes. You must set up a virtual environment and keep it active or configured so the Node app can call it.

```bash
# Navigate to the project directory
cd Vegemite-Prescriptive-Production-System

# Create a virtual environment named "venv"
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required ML libraries
pip install pandas numpy scikit-learn lightgbm joblib
```

### 2. Setup Next.js Environment (Frontend & API)

Open a terminal (ensure you are still in the project root) and install the Node.js frontend dependencies using `pnpm`:

```bash
# Install Node.js dependencies
pnpm install
```

### 3. Run the Fullstack Application

Because Next.js handles both the Frontend UI and Backend API routes, you don't even need to start the Python ML file manually. The API will spawn the Python models under the hood.

Make sure your Python virtual environment is activated before running the project:

```bash
pnpm dev
```

The application will be available at [http://localhost:3000](http://localhost:3000). 
- **Frontend** runs on React + Next.js App Router.
- **Backend APIs** (`/api/recommend-sp`, `/api/data`) reside in the `app/api/` folder and trigger the `models/serve_recommend_sp.py` script automatically to serve predictions!

### (Optional) Testing Python Model directly
If you want to debug or test the machine learning model independent from the Next.js UI, you can run the python script standalone:

```bash
# Still within your virtual environment
python models/serve_recommend_sp.py
```
*Note: The script expects a JSON input via stdin to run a test prediction.*

## Technology Stack

- **Frontend**: Next.js (App Router), React, TypeScript
- **Styling**: Tailwind CSS, Shadcn UI
- **Data Visualization**: Recharts
- **Backend/Logic**: Python, Scikit-Learn
- **State Management**: React Hooks, Context API
- **Icons**: Lucide React


