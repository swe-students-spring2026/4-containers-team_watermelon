<<<<<<< HEAD
# Actor Emotion Coach

=======
>>>>>>> origin/main
[![ML Client CI](https://github.com/swe-students-spring2026/4-containers-team_watermelon/actions/workflows/ml-client-ci.yml/badge.svg?branch=main)](https://github.com/swe-students-spring2026/4-containers-team_watermelon/actions/workflows/ml-client-ci.yml)
[![Web App CI](https://github.com/swe-students-spring2026/4-containers-team_watermelon/actions/workflows/web-app-ci.yml/badge.svg?branch=main)](https://github.com/swe-students-spring2026/4-containers-team_watermelon/actions/workflows/web-app-ci.yml)

# Actor Cam

## Project Description

Actor Cam is an application designed to analyze an actor's performatnce in real time. The actor chooses an emotion they want to practice, and Actor Cam grades how convincing their performance is!

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

## How to Configure Environment Variables

This project requires environment variables to securely connect the web app and machine learning client to the MongoDB database. 

1. Navigate to the `machine-learning-client` folder.
2. Locate the `.env.example` file, duplicate it in the same location, and rename the copy to `.env`.
3. Ensure the `machine-learning-client/.env` file contains the following exact configuration:
```text
   MONGO_URI=mongodb://mongodb:27017
   DB_NAME=emotion_db
   COLLECTION_NAME=scans
   POLL_INTERVAL=3
```

4. Navigate to the `web-app` folder.
5. Locate the `.env.example` file, duplicate it in the same location, and rename the copy to `.env`.
6. Ensure the `web-app/.env` file contains the following exact configuration:
```text
   MONGO_URI=mongodb://mongodb:27017
   DB_NAME=emotion_db
   COLLECTION_NAME=scans
```

## How to Run the Project

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

NOTE: No additional starter data is required.
