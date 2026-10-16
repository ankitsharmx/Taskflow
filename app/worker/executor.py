import asyncio

async def execute_job(
    job_type: str,
    payload: dict,
    attempt: int = 1,
) -> None:
    if payload.get("simulate_failure") and attempt == 1:
        print("[executor] simulate failure")
        raise RuntimeError("Simulated job failure")

    if job_type == "email":
        print(
            f"[executor] sending email "
            f"to {payload.get('to')}"
        )

        await asyncio.sleep(1)
        print("[executor] email completed")
        return
    raise ValueError(f"Unsupported job type: {job_type}")