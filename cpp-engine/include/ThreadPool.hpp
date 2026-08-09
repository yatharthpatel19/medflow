#ifndef THREADPOOL_HPP
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
