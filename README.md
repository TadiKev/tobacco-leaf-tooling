🌿 Tobacco Leaf Disease Detection Platform

An end-to-end system for identifying tobacco leaf diseases from photos, combining a machine learning model with a mobile capture app, a web admin dashboard, and a Django/PostgreSQL backend.



🎥 Demo video: [Insert demo video link]



Overview

Farmers and field agronomists can photograph a tobacco leaf and receive an instant diagnosis of common leaf diseases, helping catch crop issues early and reduce yield loss. The platform is split into four cooperating services:





mobile/ — Expo/React Native app for capturing leaf photos in the field and submitting them for diagnosis



ml/ — Jupyter-based ML workspace for training and evaluating the leaf disease classification model



web-admin/ — React admin dashboard for reviewing submissions, managing diagnosis records, and monitoring model performance



backend/ — Django + PostgreSQL API that serves predictions, stores results, and connects the mobile and web clients



tfjs_model_output/ — Exported TensorFlow.js model artifacts for on-device / browser inference



Tech Stack







Layer



Technology





Backend



Django, PostgreSQL





Web Admin



React





Mobile



React Native (Expo)





ML



TensorFlow / TensorFlow.js, Jupyter





Infrastructure



Docker, Docker Compose



Getting Started

The project ships as a Docker Compose skeleton for local development.

Requirements: Docker Desktop

# 1. Copy the environment template and edit as needed
cp .env.example .env

# 2. Build and start all services
docker compose up --build

Services once running:







Service



URL





Django backend (API)



http://localhost:8000





React web admin



http://localhost:3000





Jupyter (ML workspace)



http://localhost:8888 (token printed in container logs)





PostgreSQL



localhost:5432



Notes





The backend connects to the db Postgres container automatically.



Uploaded leaf images are persisted to ./backend/media.



Postgres data is stored in the named Docker volume postgres_data.



This Compose setup is intended for local development/demo use, not production deployment.



Architecture

┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│ Mobile App  │─────▶│  Django API  │◀────▶│  PostgreSQL DB  │
│ (Expo/RN)   │      │  (backend)   │      └────────────────┘
└─────────────┘      └──────┬───────┘
                             │
┌─────────────┐             │
│  Web Admin  │◀────────────┘
│  (React)    │
└─────────────┘

      ML training/eval happens in ml/ (Jupyter);
      trained model is exported to tfjs_model_output/
      for lightweight inference.



Roadmap





Expand disease class coverage



Add offline inference support in the mobile app



Production deployment guide (env hardening, managed Postgres, HTTPS)
