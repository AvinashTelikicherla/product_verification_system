"""End-to-end smoke test of the API using an in-process ASGI client."""

import asyncio
import io
import os

# Use an isolated in-memory DB for the test run.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./smoke_test.db"

import httpx

from src.app import app


async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        # lifespan startup
        async with app.router.lifespan_context(app):
            # health
            r = await c.get("/health")
            assert r.status_code == 200, r.text
            print("health:", r.json()["status"])

            # login as seeded admin
            r = await c.post("/auth/login", json={"username": "admin", "password": "admin12345"})
            assert r.status_code == 200, r.text
            token = r.json()["access_token"]
            auth = {"Authorization": f"Bearer {token}"}
            print("login: ok")

            # register an operator
            r = await c.post(
                "/auth/register",
                headers=auth,
                json={
                    "username": "op1",
                    "email": "op1@example.com",
                    "password": "operator123",
                    "role": "operator",
                    "full_name": "Op One",
                },
            )
            assert r.status_code == 201, r.text
            print("register operator:", r.json()["username"])

            # operator login
            r = await c.post("/auth/login", json={"username": "op1", "password": "operator123"})
            op_auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

            # upload CSV (admin) — sample data in the WID/EAN/Manufacturing_Date/Expiry_Date
            # format, with US-style M/D/YYYY dates.
            csv_data = (
                "WID,EAN,Manufacturing_Date,Expiry_Date\n"
                "18739945,8429164054229,5/16/2020,3/19/2021\n"
                "76786340,4573060126209,9/2/2025,4/14/2026\n"
                "22585362,3802444696471,9/28/2022,12/10/2024\n"
            )
            files = {"file": ("products.csv", io.BytesIO(csv_data.encode()), "text/csv")}
            r = await c.post("/products/upload", headers=auth, files=files)
            assert r.status_code == 202, r.text
            job_id = r.json()["id"]
            print("upload accepted, job:", job_id)

            # poll status until complete
            for _ in range(50):
                r = await c.get(f"/products/upload/{job_id}/status", headers=auth)
                assert r.status_code == 200, r.text
                status = r.json()["status"]
                if status == "completed":
                    break
                await asyncio.sleep(0.05)
            assert status == "completed", f"job did not complete: {r.json()}"
            print("upload completed, processed:", r.json()["processed_rows"])

            # list products
            r = await c.get("/products", headers=auth)
            assert r.status_code == 200 and len(r.json()) == 3, r.text
            print("products listed:", len(r.json()))

            # operator verifies a product by WID
            r = await c.post(
                "/verify", headers=op_auth, json={"wid": "18739945", "notes": "looks good"}
            )
            assert r.status_code == 201, r.text
            body = r.json()
            assert body["product"]["wid"] == "18739945"
            log_id = body["verification_log"]["id"]
            print("verify: created log", log_id)

            # operator cannot access reports (RBAC)
            r = await c.get(
                "/reports",
                headers=op_auth,
                params={"start_date": "2024-01-01", "end_date": "2030-01-01"},
            )
            assert r.status_code == 403, f"expected 403, got {r.status_code}"
            print("rbac: operator blocked from reports (403)")

            # admin report
            r = await c.get(
                "/reports",
                headers=auth,
                params={"start_date": "2024-01-01", "end_date": "2030-01-01"},
            )
            assert r.status_code == 200, r.text
            print("report total_verifications:", r.json()["total_verifications"])

            # admin export
            r = await c.get(
                "/reports/export",
                headers=auth,
                params={"start_date": "2024-01-01", "end_date": "2030-01-01"},
            )
            assert r.status_code == 200 and "log_id" in r.text, r.text
            print("export: csv bytes", len(r.text))

            # verify unknown WID -> 404
            r = await c.post("/verify", headers=op_auth, json={"wid": "NOPE"})
            assert r.status_code == 404, r.text
            print("verify unknown WID -> 404")

    print("\nALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
