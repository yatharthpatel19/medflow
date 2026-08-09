import os

files = {
    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: medflow_db
    environment:
      POSTGRES_DB: medflow
      POSTGRES_USER: medflow_user
      POSTGRES_PASSWORD: medflow_secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: medflow_backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://medflow_user:medflow_secure_password@db:5432/medflow
      JWT_SECRET: medflow_super_secret_jwt_key_2026
      MOCK_SMS_MODE: "True"
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: medflow_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
""",

    "cpp-engine/CMakeLists.txt": """cmake_minimum_required(VERSION 3.14)
project(medflow_engine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 REQUIRED)
include_directories(include)

file(GLOB SOURCES "src/*.cpp")
pybind11_add_module(medflow_engine ${SOURCES})
""",

    "cpp-engine/include/Job.hpp": """#ifndef JOB_HPP
#define JOB_HPP

#include <string>
#include <chrono>
#include <functional>

enum class JobPriority { CRITICAL = 0, HIGH = 1, NORMAL = 2, LOW = 3 };
enum class JobStatus { QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED };

struct JobTask {
    std::string id;
    std::string type;
    JobPriority priority;
    int patient_id;
    int report_id;
    std::function<bool()> work_payload;
    JobStatus status{JobStatus::QUEUED};
    std::string error_message{""};
    
    std::chrono::system_clock::time_point created_at{std::chrono::system_clock::now()};
    std::chrono::system_clock::time_point started_at;
    std::chrono::system_clock::time_point completed_at;

    bool operator<(const JobTask& other) const {
        if (priority != other.priority) return static_cast<int>(priority) > static_cast<int>(other.priority);
        return created_at > other.created_at;
    }
};

#endif
""",

    "cpp-engine/include/ThreadPool.hpp": """#ifndef THREADPOOL_HPP
#define THREADPOOL_HPP

#include "Job.hpp"
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <future>
#include <atomic>
#include <memory>

struct WorkerStats {
    int id;
    bool is_busy{false};
    std::string current_job_id{""};
    std::string current_job_type{""};
    std::atomic<uint64_t> completed_jobs{0};
    std::atomic<uint64_t> failed_jobs{0};
    double total_execution_time_ms{0.0};
};

class ThreadPool {
public:
    explicit ThreadPool(size_t num_threads = std::thread::hardware_concurrency());
    ~ThreadPool();

    void start();
    void shutdown();

    struct PoolMetrics {
        size_t total_workers;
        size_t active_workers;
        size_t queue_size;
        uint64_t total_completed;
        uint64_t total_failed;
        double avg_execution_ms;
        double throughput_per_min;
    };

    PoolMetrics get_metrics();

private:
    void worker_loop(size_t worker_id);

    std::vector<std::thread> workers_;
    std::priority_queue<std::shared_ptr<JobTask>, std::vector<std::shared_ptr<JobTask>>, 
                        std::function<bool(const std::shared_ptr<JobTask>&, const std::shared_ptr<JobTask>&)>> task_queue_;

    std::mutex queue_mutex_;
    std::condition_variable cv_task_;
    std::atomic<bool> stop_flag_{false};

    std::vector<std::unique_ptr<WorkerStats>> worker_stats_;
    std::atomic<uint64_t> total_completed_jobs_{0};
    std::atomic<uint64_t> total_failed_jobs_{0};
    std::atomic<double> accum_execution_time_ms_{0.0};
    std::chrono::system_clock::time_point start_time_;
};

#endif
""",

    "backend/requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pydantic==2.6.0
pyjwt==2.8.0
passlib[bcrypt]==1.7.4
reportlab==4.0.9
qrcode==7.4.2
python-multipart==0.0.6
jinja2==3.1.3
""",

    "backend/Dockerfile": """FROM python:3.11-slim

RUN apt-get update && apt-get install -y \\
    build-essential \\
    cmake \\
    g++ \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY cpp-engine /app/cpp-engine
WORKDIR /app/cpp-engine
RUN mkdir build && cd build && cmake .. && make

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app
ENV PYTHONPATH=/app/cpp-engine/build

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Success! All MedFlow project files generated.")