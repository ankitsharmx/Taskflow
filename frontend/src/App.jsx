import { useEffect, useMemo, useState } from "react";

import { createJob, getJobs } from "./api";


function App() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);

  const [form, setForm] = useState({
    job_type: "email",
    recipient: "",
    priority: "NORMAL",
    max_attempts: 3,
    simulate_failure: false,
  });

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");


  async function loadJobs() {
    try {
      setLoading(true);

      const data = await getJobs();

      setJobs(data);

      // Keep selected job synchronized with the latest API data.
      setSelectedJob((current) => {
        if (!current) {
          return null;
        }

        return (
          data.find((job) => job.id === current.id) ||
          current
        );
      });

      setError("");
    } catch (err) {
      setError("Unable to connect to TaskFlow API.");
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadJobs();

    const interval = setInterval(loadJobs, 2000);

    return () => clearInterval(interval);
  }, []);


  function handleChange(event) {
    const { name, value, type, checked } = event.target;

    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  }


  async function handleSubmit(event) {
    event.preventDefault();

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      await createJob({
        job_type: form.job_type,

        payload: {
          to: form.recipient,
          simulate_failure: form.simulate_failure,
        },

        priority: form.priority,

        max_attempts: Number(form.max_attempts),
      });

      setSuccess("Job submitted successfully.");

      setForm((current) => ({
        ...current,
        recipient: "",
        simulate_failure: false,
      }));

      await loadJobs();
    } catch (err) {
      setError(err.message || "Failed to create job.");
    } finally {
      setSubmitting(false);
    }
  }


  const metrics = useMemo(() => {
    return {
      total: jobs.length,

      queued: jobs.filter(
        (job) => job.status === "QUEUED"
      ).length,

      running: jobs.filter(
        (job) => job.status === "RUNNING"
      ).length,

      done: jobs.filter(
        (job) => job.status === "DONE"
      ).length,

      failed: jobs.filter(
        (job) => job.status === "FAILED"
      ).length,
    };
  }, [jobs]);


  return (
    <div className="app">

      {/* Header */}

      <header className="header">

        <div>
          <div className="brand">
            TaskFlow
          </div>

          <div className="subtitle">
            Distributed Job Processing Platform
          </div>
        </div>


        <div className="system-status">

          <span className="status-dot"></span>

          System Operational

        </div>

      </header>


      <main className="container">

        {/* Hero */}

        <section className="hero">

          <div>

            <p className="eyebrow">
              JOB ORCHESTRATION
            </p>

            <h1>
              Reliable background jobs,
              <br />
              built for scale.
            </h1>

            <p className="hero-text">
              Submit jobs, prioritize workloads,
              monitor execution, and automatically
              retry failed tasks.
            </p>

          </div>

        </section>


        {/* Submit + Metrics */}

        <section className="dashboard-grid">


          {/* Submit Job */}

          <div className="card submit-card">

            <div className="card-header">

              <div>

                <h2>
                  Submit New Job
                </h2>

                <p>
                  Create a background task for TaskFlow.
                </p>

              </div>

            </div>


            <form onSubmit={handleSubmit}>

              <div className="form-grid">


                <div className="form-group">

                  <label htmlFor="job_type">
                    Job Type
                  </label>

                  <select
                    id="job_type"
                    name="job_type"
                    value={form.job_type}
                    onChange={handleChange}
                  >

                    <option value="email">
                      Email
                    </option>

                  </select>

                </div>


                <div className="form-group">

                  <label htmlFor="priority">
                    Priority
                  </label>

                  <select
                    id="priority"
                    name="priority"
                    value={form.priority}
                    onChange={handleChange}
                  >

                    <option value="HIGH">
                      High
                    </option>

                    <option value="NORMAL">
                      Normal
                    </option>

                    <option value="LOW">
                      Low
                    </option>

                  </select>

                </div>

              </div>


              <div className="form-group">

                <label htmlFor="recipient">
                  Recipient
                </label>

                <input
                  id="recipient"
                  name="recipient"
                  type="email"
                  placeholder="user@example.com"
                  value={form.recipient}
                  onChange={handleChange}
                  required
                />

              </div>


              <div className="form-grid">

                <div className="form-group">

                  <label htmlFor="max_attempts">
                    Maximum Attempts
                  </label>

                  <input
                    id="max_attempts"
                    name="max_attempts"
                    type="number"
                    min="1"
                    max="10"
                    value={form.max_attempts}
                    onChange={handleChange}
                  />

                </div>


                <label className="checkbox">

                  <input
                    name="simulate_failure"
                    type="checkbox"
                    checked={form.simulate_failure}
                    onChange={handleChange}
                  />

                  <span>
                    Simulate Failure
                  </span>

                </label>

              </div>


              {error && (
                <div className="message error">
                  {error}
                </div>
              )}


              {success && (
                <div className="message success">
                  {success}
                </div>
              )}


              <button
                className="submit-button"
                type="submit"
                disabled={submitting}
              >

                {submitting
                  ? "Submitting..."
                  : "Submit Job"}

              </button>

            </form>

          </div>


          {/* Metrics */}

          <div className="metrics-column">

            <MetricCard
              label="Total Jobs"
              value={metrics.total}
            />

            <MetricCard
              label="Queued"
              value={metrics.queued}
            />

            <MetricCard
              label="Running"
              value={metrics.running}
            />

            <MetricCard
              label="Completed"
              value={metrics.done}
            />

            <MetricCard
              label="Failed"
              value={metrics.failed}
            />

          </div>

        </section>


        {/* Job History */}

        <section className="card">

          <div className="card-header">

            <div>

              <h2>
                Job History
              </h2>

              <p>
                Live view of jobs processed by TaskFlow.
              </p>

            </div>


            <div className="refresh-indicator">

              <span className="status-dot"></span>

              Auto-refreshing

            </div>

          </div>


          {loading && jobs.length === 0 ? (

            <div className="empty-state">
              Loading jobs...
            </div>

          ) : jobs.length === 0 ? (

            <div className="empty-state">
              No jobs have been submitted yet.
            </div>

          ) : (

            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>

                    <th>Job ID</th>
                    <th>Type</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Attempts</th>
                    <th>Recipient</th>
                    <th></th>

                  </tr>

                </thead>


                <tbody>

                  {jobs.map((job) => (

                    <tr
                      key={job.id}
                      className={
                        selectedJob?.id === job.id
                          ? "selected-row"
                          : ""
                      }
                    >

                      <td>
                        <code>
                          {job.id.slice(0, 8)}...
                        </code>
                      </td>


                      <td>
                        {job.job_type}
                      </td>


                      <td>
                        <PriorityBadge
                          priority={job.priority}
                        />
                      </td>


                      <td>
                        <StatusBadge
                          status={job.status}
                        />
                      </td>


                      <td>
                        {job.attempts} / {job.max_attempts}
                      </td>


                      <td>
                        {job.payload?.to || "-"}
                      </td>


                      <td>

                        <button
                          className="details-button"
                          onClick={() =>
                            setSelectedJob(job)
                          }
                        >
                          Details
                        </button>

                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          )}

        </section>


        {/* Job Details */}

        {selectedJob && (

          <JobDetails
            job={selectedJob}
            onClose={() => setSelectedJob(null)}
          />

        )}


        {/* Architecture */}

        <section className="architecture card">

          <div className="card-header">

            <div>

              <h2>
                TaskFlow Architecture
              </h2>

              <p>
                How a job moves through the system.
              </p>

            </div>

          </div>


          <div className="architecture-flow">

            <ArchitectureNode
              title="Client"
              description="React UI"
            />

            <Arrow />

            <ArchitectureNode
              title="FastAPI"
              description="REST API"
            />

            <Arrow />

            <ArchitectureNode
              title="PostgreSQL"
              description="Jobs + Outbox"
            />

            <Arrow />

            <ArchitectureNode
              title="Dispatcher"
              description="Publishes events"
            />

            <Arrow />

            <ArchitectureNode
              title="Redis"
              description="Priority queues"
            />

            <Arrow />

            <ArchitectureNode
              title="Worker"
              description="Executes jobs"
            />

            <Arrow />

            <ArchitectureNode
              title="Retry"
              description="Reschedules failures"
            />

          </div>

        </section>


      </main>

    </div>
  );
}


/* ---------------- Components ---------------- */


function MetricCard({ label, value }) {

  return (

    <div className="metric-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>

  );
}


function StatusBadge({ status }) {

  return (

    <span
      className={`badge status-${status.toLowerCase()}`}
    >
      {status}
    </span>

  );

}


function PriorityBadge({ priority }) {

  return (

    <span
      className={`badge priority-${priority.toLowerCase()}`}
    >
      {priority}
    </span>

  );

}


function JobDetails({ job, onClose }) {

  const lifecycle = [
    "PENDING",
    "QUEUED",
    "RUNNING",
    "DONE",
  ];


  const failureLifecycle = [
    "PENDING",
    "QUEUED",
    "RUNNING",
    "FAILED",
    "QUEUED",
    "RUNNING",
    "DONE",
  ];


  const isRetry =
    job.attempts > 1;


  const flow = isRetry
    ? failureLifecycle
    : lifecycle;


  return (

    <section className="card details-card">

      <div className="details-header">

        <div>

          <p className="eyebrow">
            JOB DETAILS
          </p>

          <h2>
            {job.job_type} job
          </h2>

          <code className="full-id">
            {job.id}
          </code>

        </div>


        <button
          className="close-button"
          onClick={onClose}
        >
          Close
        </button>

      </div>


      <div className="details-grid">


        <div className="detail-box">

          <span>
            Current Status
          </span>

          <StatusBadge
            status={job.status}
          />

        </div>


        <div className="detail-box">

          <span>
            Priority
          </span>

          <PriorityBadge
            priority={job.priority}
          />

        </div>


        <div className="detail-box">

          <span>
            Attempts
          </span>

          <strong>
            {job.attempts} / {job.max_attempts}
          </strong>

        </div>


        <div className="detail-box">

          <span>
            Recipient
          </span>

          <strong>
            {job.payload?.to || "-"}
          </strong>

        </div>

      </div>


      <div className="timeline-section">

        <div className="timeline-title">

          <div>

            <h3>
              Execution Flow
            </h3>

            <p>
              Current lifecycle state of this job.
            </p>

          </div>

          {isRetry && (

            <span className="retry-label">
              Retry detected
            </span>

          )}

        </div>


        <div className="timeline">

          {flow.map((stage, index) => {

            const isCurrent =
              stage === job.status;

            const isDone =
              getStageProgress(
                job.status,
                stage,
                flow
              );


            return (

              <div
                className="timeline-item"
                key={`${stage}-${index}`}
              >

                <div
                  className={
                    `timeline-node ${
                      isCurrent
                        ? "current"
                        : isDone
                        ? "completed"
                        : ""
                    }`
                  }
                >

                  {isCurrent
                    ? "●"
                    : isDone
                    ? "✓"
                    : "○"}

                </div>


                <div className="timeline-content">

                  <strong>
                    {stage}
                  </strong>

                  {isCurrent && (
                    <span>
                      Current stage
                    </span>
                  )}

                </div>


                {index < flow.length - 1 && (

                  <div className="timeline-line"></div>

                )}

              </div>

            );

          })}

        </div>

      </div>


      {job.next_retry_at && (

        <div className="retry-info">

          <strong>
            Retry scheduled
          </strong>

          <span>
            {new Date(
              job.next_retry_at
            ).toLocaleString()}
          </span>

        </div>

      )}

    </section>

  );

}


function getStageProgress(
  currentStatus,
  stage,
  flow
) {

  const currentIndex =
    flow.lastIndexOf(currentStatus);

  const stageIndex =
    flow.indexOf(stage);

  return (
    currentIndex > stageIndex &&
    stage !== currentStatus
  );

}


function ArchitectureNode({
  title,
  description,
}) {

  return (

    <div className="architecture-node">

      <strong>
        {title}
      </strong>

      <span>
        {description}
      </span>

    </div>

  );

}


function Arrow() {

  return (
    <div className="architecture-arrow">
      →
    </div>
  );

}


export default App;