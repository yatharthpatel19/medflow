#ifndef JOB_HPP
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
