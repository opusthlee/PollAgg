module.exports = {
  apps: [
    {
      name: "pollagg-api",
      script: "python3",
      args: "-m uvicorn api:app --host 0.0.0.0 --port 8002 --reload",
      cwd: "/Users/up_main/Desktop/T_Antigravity/PollAgg",
      interpreter: "none",
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 2000,
      log_file: "/Users/up_main/Desktop/T_Antigravity/PollAgg/logs/api.log",
      out_file: "/Users/up_main/Desktop/T_Antigravity/PollAgg/logs/api-out.log",
      error_file: "/Users/up_main/Desktop/T_Antigravity/PollAgg/logs/api-err.log",
      merge_logs: true,
      env: {
        NODE_ENV: "development",
        PYTHONPATH: "/Users/up_main/Desktop/T_Antigravity/PollAgg"
      }
    },
    {
      name: "pollagg-frontend",
      script: "npm",
      args: "run dev -- -p 3000",
      cwd: "/Users/up_main/Desktop/T_Antigravity/PollAgg/frontend",
      interpreter: "none",
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      log_file: "/Users/up_main/Desktop/T_Antigravity/PollAgg/logs/frontend.log",
      out_file: "/Users/up_main/Desktop/T_Antigravity/PollAgg/logs/frontend-out.log",
      error_file: "/Users/up_main/Desktop/T_Antigravity/PollAgg/logs/frontend-err.log",
      merge_logs: true,
      env: {
        NODE_ENV: "development"
      }
    }
  ]
};
