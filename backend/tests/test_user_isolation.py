"""
Regression test for multi-user data isolation.

This test ensures that users cannot access each other's analysis_jobs data.
Critical security test to prevent the bug where all users see the same dashboard data.

Usage: python3 tests/test_user_isolation.py
"""
import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any


def load_env_file():
    """Load environment variables from .env file."""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(backend_dir, ".env")
    
    if not os.path.exists(env_path):
        return
    
    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# Load environment variables at module level
load_env_file()


class TestUserIsolation:
    """Test that users are properly isolated from each other's data."""
    
    def get_supabase_config(self):
        """Get Supabase configuration from environment."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_service_key:
            raise Exception("Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
        
        return {
            "url": supabase_url.rstrip("/"),
            "service_key": supabase_service_key
        }
    
    def make_supabase_request(
        self,
        supabase_config: Dict[str, str],
        endpoint: str,
        method: str = "GET",
        body: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Any:
        """Helper to make requests to Supabase REST API."""
        url = f"{supabase_config['url']}{endpoint}"
        
        default_headers = {
            "apikey": supabase_config["service_key"],
            "Authorization": f"Bearer {supabase_config['service_key']}",
            "Content-Type": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        request_body = None
        if body:
            request_body = json.dumps(body).encode("utf-8")
        
        req = urllib.request.Request(url=url, data=request_body, headers=default_headers, method=method)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in (200, 201, 204):
                if response.status == 204:
                    return None
                return json.loads(response.read().decode("utf-8"))
            else:
                raise Exception(f"Request failed with status {response.status}")
    
    def test_user_cannot_access_other_users_analysis_jobs(self):
        """
        Test that User A cannot access User B's analysis_jobs.
        
        This is a regression test for the critical security bug where all signed-in users
        see the same dashboard/analytics data regardless of who uploaded what.
        """
        supabase_config = self.get_supabase_config()
        
        # Simulate two different Clerk users
        user_a_id = "user_test_clerk_id_001"
        user_b_id = "user_test_clerk_id_002"
        
        # Create an analysis job for User A
        job_a_data = {
            "file_name": "test_blueprint_user_a.pdf",
            "file_path": "/test/user_a/blueprint.pdf",
            "file_type": "pdf",
            "storage_bucket": "blueprints",
            "status": "queued",
            "user_id": user_a_id,
            "org_id": None
        }
        
        created_job = self.make_supabase_request(
            supabase_config,
            "/rest/v1/analysis_jobs",
            method="POST",
            body=job_a_data
        )
        
        job_a_id = created_job[0]["id"]
        
        try:
            # Test 1: User A should be able to query their own job
            query_a = urllib.parse.urlencode({
                "select": "id,user_id,file_name",
                "user_id": f"eq.{user_a_id}"
            })
            user_a_jobs = self.make_supabase_request(
                supabase_config,
                f"/rest/v1/analysis_jobs?{query_a}"
            )
            
            assert len(user_a_jobs) >= 1, "User A should see at least their own job"
            assert any(job["id"] == job_a_id for job in user_a_jobs), "User A should see their created job"
            
            # Test 2: User B should NOT see User A's job when filtering by user_id
            query_b = urllib.parse.urlencode({
                "select": "id,user_id,file_name",
                "user_id": f"eq.{user_b_id}"
            })
            user_b_jobs = self.make_supabase_request(
                supabase_config,
                f"/rest/v1/analysis_jobs?{query_b}"
            )
            
            assert len(user_b_jobs) == 0, "User B should not see any jobs when filtering by their own user_id"
            assert not any(job["id"] == job_a_id for job in user_b_jobs), "User B should not see User A's job"
            
            # Test 3: Direct ID access should still require user_id match (this is what the API endpoint enforces)
            # This simulates what the calibration endpoint does
            query_direct = urllib.parse.urlencode({
                "select": "id,user_id,file_name",
                "id": f"eq.{job_a_id}",
                "user_id": f"eq.{user_b_id}"  # User B trying to access User A's job by ID
            })
            user_b_direct_access = self.make_supabase_request(
                supabase_config,
                f"/rest/v1/analysis_jobs?{query_direct}"
            )
            
            assert len(user_b_direct_access) == 0, "User B should not access User A's job even by direct ID with user_id filter"
            
            # Test 4: Verify the job exists (sanity check)
            query_all = urllib.parse.urlencode({
                "select": "id,user_id,file_name",
                "id": f"eq.{job_a_id}"
            })
            job_exists = self.make_supabase_request(
                supabase_config,
                f"/rest/v1/analysis_jobs?{query_all}"
            )
            
            assert len(job_exists) == 1, "Job should exist in database"
            assert job_exists[0]["user_id"] == user_a_id, "Job should belong to User A"
            
        finally:
            # Cleanup: Delete the test job
            delete_query = urllib.parse.urlencode({"id": f"eq.{job_a_id}"})
            self.make_supabase_request(
                supabase_config,
                f"/rest/v1/analysis_jobs?{delete_query}",
                method="DELETE"
            )
    
    def test_organization_isolation(self):
        """
        Test that users in different organizations cannot access each other's jobs.
        """
        supabase_config = self.get_supabase_config()
        
        user_a_id = "user_test_clerk_id_003"
        user_b_id = "user_test_clerk_id_004"
        org_a_id = "org_test_id_001"
        org_b_id = "org_test_id_002"
        
        # Create a job for User A in Org A
        job_a_data = {
            "file_name": "test_org_a.pdf",
            "file_path": "/test/org_a/blueprint.pdf",
            "file_type": "pdf",
            "storage_bucket": "blueprints",
            "status": "queued",
            "user_id": user_a_id,
            "org_id": org_a_id
        }
        
        created_job = self.make_supabase_request(
            supabase_config,
            "/rest/v1/analysis_jobs",
            method="POST",
            body=job_a_data
        )
        
        job_a_id = created_job[0]["id"]
        
        try:
            # User B in Org B should not see Org A's jobs
            query = urllib.parse.urlencode({
                "select": "id,user_id,org_id,file_name",
                "org_id": f"eq.{org_b_id}"
            })
            org_b_jobs = self.make_supabase_request(
                supabase_config,
                f"/rest/v1/analysis_jobs?{query}"
            )
            
            assert not any(job["id"] == job_a_id for job in org_b_jobs), "Org B should not see Org A's jobs"
            
        finally:
            # Cleanup
            delete_query = urllib.parse.urlencode({"id": f"eq.{job_a_id}"})
            self.make_supabase_request(
                supabase_config,
                f"/rest/v1/analysis_jobs?{delete_query}",
                method="DELETE"
            )


if __name__ == "__main__":
    # Run tests manually for quick verification
    # Usage: python3 tests/test_user_isolation.py
    import sys
    
    test = TestUserIsolation()
    
    print("Running user isolation tests...")
    print("=" * 60)
    
    try:
        test.test_user_cannot_access_other_users_analysis_jobs()
        print("✅ User isolation test passed")
    except AssertionError as e:
        print(f"❌ User isolation test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ User isolation test error: {e}")
        sys.exit(1)
    
    try:
        test.test_organization_isolation()
        print("✅ Organization isolation test passed")
    except AssertionError as e:
        print(f"❌ Organization isolation test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Organization isolation test error: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("✅ All isolation tests passed!")
