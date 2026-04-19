# Actor Emotion Coach

![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
[![ML Client CI](https://github.com/swe-students-spring2026/4-containers-team_watermelon/actions/workflows/ml-client-ci.yml/badge.svg?branch=main)](https://github.com/swe-students-spring2026/4-containers-team_watermelon/actions/workflows/ml-client-ci.yml)


## Project Description

This project is a containerized actor training platform built with three connected subsystems: a Flask web app, a machine learning client, and a MongoDB database.

The platform asks users to perform target emotions such as happy, sad, angry, surprised, or neutral. The machine learning client processes facial images and evaluates how strongly the user’s expression matches the requested emotion. The database stores scan records, emotion scores, timestamps, and grading results so that the web app and machine learning client can use the same shared data.


## Team Members

- [Jerry Wang](https://github.com/JerrrryWang)
- [Abir Mahmood](https://github.com/abirmahmood6)
- [Faizan Shamsi](https://github.com/17faizan)
- [Diya Greben](https://github.com/diyagreben)
- [Bella D'Aquino](https://github.com/belladaq)

## Main Features

- User account creation
- User login
- Actor training interface
- Prompted emotion performance tasks
- Facial emotion detection
- Emotion score calculation
- Match score / grading for target emotion
- MongoDB-backed storage
- History of previous scans and results
- Multi-container deployment using Docker Compose

## How to Configure and Run the Project

Before running the project, make sure the following are installed on your machine:

- Docker Desktop
- Docker Compose


You can check this with:

```bash
docker --version
docker compose version
```

From the root of the repository, run:
```bash
docker compose up --build
```

Then open this URL in your browser: http://127.0.0.1:5001/

After signing in, the user can start emotion training tasks, submit facial scans, and review previous scores and results.
