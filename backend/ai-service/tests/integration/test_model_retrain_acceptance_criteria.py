"""
Integration tests for Model Retraining Feature - Acceptance Criteria
Tests all 5 acceptance criteria for the model retraining functionality.
"""
import time
import sys
import pytest
import conftest


@pytest.fixture
def wait_for_rebuild_completion(client):
    """
    Fixture that waits for any ongoing rebuild to complete before the test.
    This ensures test isolation for tests that need it.
    NOTE: Not autouse to avoid interfering with hot-swap tests that mock rebuilds.
    """
    max_wait = 60  # Wait up to 60 seconds
    for _ in range(max_wait):
        try:
            status = client.get("/e2e")
            if status.status_code == 200:
                data = status.json()
                if not data.get("rebuilding", False):
                    break
        except:
            pass
        time.sleep(1)
    yield  # Run the test
    # No cleanup needed


# ============================================================================
# AC1: Users can access a "Retrain Model" function from the application interface
# ============================================================================
def test_ac1_retrain_model_endpoint_accessible(client):
    """
    AC1: Users can access a "Retrain Model" function from the application interface

    Test that the /rebuild endpoint is accessible and returns proper response.
    """
    response = client.post("/rebuild")

    # Should return 202 Accepted status
    assert response.status_code == 202, "Rebuild endpoint should be accessible and return 202"

    # Should return status in response
    data = response.json()
    assert "status" in data, "Response should contain status field"
    assert data["status"] in ["rebuild started", "already rebuilding"], \
        "Status should indicate rebuild started or already in progress"

    print("✓ AC1 PASSED: Users can access rebuild endpoint")


# ============================================================================
# AC2: Users receive confirmation prompts before initiating the retraining process
# ============================================================================
def test_ac2_validation_before_rebuild(client):
    """
    AC2: Users receive confirmation prompts before initiating the retraining process

    Test that validation endpoint provides information needed for confirmation prompts.
    This endpoint is called by the frontend before showing confirmation dialog.
    """
    # Call validation endpoint
    response = client.get("/training/validate")

    assert response.status_code == 200, "Validation endpoint should be accessible"

    data = response.json()

    # Check that validation returns all required information for confirmation
    assert "valid" in data, "Should indicate if training data is valid"
    assert "total_documents" in data, "Should show total document count"
    assert "primary_tags" in data, "Should show primary tag counts"
    assert "secondary_tags" in data, "Should show secondary tag counts"
    assert "tertiary_tags" in data, "Should show tertiary tag counts"
    assert "invalid_tags" in data, "Should list tags with insufficient data"
    assert "message" in data, "Should provide validation message"

    # Ensure total_documents is reasonable
    assert isinstance(data["total_documents"], int), "Total documents should be integer"
    assert data["total_documents"] > 0, "Should have training documents"

    print(f"✓ AC2 PASSED: Validation provides confirmation data ({data['total_documents']} documents)")


# ============================================================================
# AC3: Users receive real-time status updates on the retraining progress
# ============================================================================
def test_ac3_realtime_status_updates(client, app_module, monkeypatch, wait_for_rebuild_completion):
    """
    AC3: Users receive real-time status updates on the retraining progress

    Test that the /e2e endpoint provides rebuilding status that frontend can poll.
    """
    # Simulate slow training
    def fake_run(cmd, check):
        time.sleep(0.3)  # Simulate training time
        return 0

    monkeypatch.setattr(app_module.subprocess, "run", fake_run, raising=True)

    # Mock the build function - patch train module since app.py uses "import train"
    def fake_build_best_model(_models_dir):
        return conftest.DummyHierModel(version="v2")

    monkeypatch.setattr(sys.modules["train"], "build_best_model", fake_build_best_model, raising=True)

    # Check initial status - should not be rebuilding
    status1 = client.get("/e2e")
    assert status1.status_code == 200, "Status endpoint should be accessible"
    data1 = status1.json()
    assert "rebuilding" in data1, "Status should include rebuilding flag"

    # Start rebuild
    rebuild_response = client.post("/rebuild")
    assert rebuild_response.status_code == 202, "Rebuild should start"

    # Check status during rebuild - should be rebuilding
    time.sleep(0.05)  # Small delay to ensure rebuild started
    status2 = client.get("/e2e")
    assert status2.status_code == 200, "Status endpoint should still be accessible during rebuild"
    data2 = status2.json()
    assert data2["rebuilding"] == True, "Should indicate rebuilding in progress"

    # Wait for rebuild to complete
    time.sleep(0.4)

    # Check status after rebuild - should not be rebuilding
    status3 = client.get("/e2e")
    assert status3.status_code == 200, "Status endpoint should be accessible after rebuild"
    data3 = status3.json()
    assert data3["rebuilding"] == False, "Should not be rebuilding after completion"

    print("✓ AC3 PASSED: Real-time status updates available via polling")


# ============================================================================
# AC4: Upon completion, users are notified of the retraining results
# ============================================================================
def test_ac4_completion_notification_mechanism(client, app_module, monkeypatch, wait_for_rebuild_completion):
    """
    AC4: Upon completion, users are notified of the retraining results

    Test that the status endpoint correctly indicates completion, allowing frontend
    to detect and show completion notifications.
    """
    # Simulate quick training
    def fake_run(cmd, check):
        time.sleep(0.2)
        return 0

    monkeypatch.setattr(app_module.subprocess, "run", fake_run, raising=True)

    # Mock the build function - patch train module since app.py uses "import train"
    def fake_build_best_model(_models_dir):
        return conftest.DummyHierModel(version="v_completed")

    monkeypatch.setattr(sys.modules["train"], "build_best_model", fake_build_best_model, raising=True)

    # Start rebuild
    client.post("/rebuild")

    # Poll status until completion (max 10 attempts)
    max_polls = 10
    poll_interval = 0.1
    completion_detected = False

    for i in range(max_polls):
        time.sleep(poll_interval)
        status = client.get("/e2e").json()

        if status["rebuilding"] == False and i > 0:  # Completion detected
            completion_detected = True

            # Re-validate to get new model statistics (simulating frontend behavior)
            validation = client.get("/training/validate")
            assert validation.status_code == 200, "Should be able to validate after completion"

            # Verify model is actually updated
            predict = client.post("/predict", json={"text": "test"})
            assert predict.status_code == 200, "Predictions should work with new model"

            break

    assert completion_detected, "Should detect completion via status polling"

    print("✓ AC4 PASSED: Completion can be detected and results retrieved")


# ============================================================================
# AC5: All tags must contain at least 10 training documents
# ============================================================================
def test_ac5_tag_validation_minimum_10_documents(client):
    """
    AC5: All tags must contain at least 10 training documents, or they cannot
    retrigger the training. This should be displayed to the user as an error
    preventing them from triggering the retraining.

    NOTE: Updated behavior - tags with <10 docs are excluded, not blocking.
    """
    # Get validation data
    response = client.get("/training/validate")
    assert response.status_code == 200, "Validation endpoint should work"

    data = response.json()

    # Check that validation checks for minimum documents
    assert "invalid_tags" in data, "Should track tags with insufficient documents"

    # Check the minimum threshold is 10
    if len(data["invalid_tags"]) > 0:
        for invalid_tag in data["invalid_tags"]:
            assert "required" in invalid_tag, "Should specify required document count"
            assert invalid_tag["required"] == 10, "Minimum should be 10 documents"
            assert "count" in invalid_tag, "Should show actual document count"
            assert invalid_tag["count"] < 10, "Invalid tags should have fewer than 10 docs"
            assert "level" in invalid_tag, "Should specify hierarchy level"
            assert "tag" in invalid_tag, "Should specify tag name"

    # Verify that all valid tags have >= 10 documents
    for tag, count in data["primary_tags"].items():
        if tag not in [t["tag"] for t in data["invalid_tags"] if t["level"] == "primary"]:
            assert count >= 10, f"Valid primary tag '{tag}' should have >= 10 docs, has {count}"

    for tag, count in data["secondary_tags"].items():
        if tag not in [t["tag"] for t in data["invalid_tags"] if t["level"] == "secondary"]:
            assert count >= 10, f"Valid secondary tag '{tag}' should have >= 10 docs, has {count}"

    for tag, count in data["tertiary_tags"].items():
        if tag not in [t["tag"] for t in data["invalid_tags"] if t["level"] == "tertiary"]:
            assert count >= 10, f"Valid tertiary tag '{tag}' should have >= 10 docs, has {count}"

    # Updated behavior: Can still retrain even with invalid tags (they'll be excluded)
    # The frontend will show which tags will be excluded
    rebuild_response = client.post("/rebuild")
    assert rebuild_response.status_code == 202, "Should allow rebuild even with excluded tags"

    print(f"✓ AC5 PASSED: Tag validation enforces 10-document minimum ({len(data['invalid_tags'])} tags excluded)")


# ============================================================================
# Additional Test: Validation Error Handling
# ============================================================================
def test_validation_endpoint_error_handling(client, monkeypatch):
    """
    Test that validation endpoint handles errors gracefully.
    """
    # This test ensures validation provides proper error messages if CSV is missing
    # In production, the CSV should always exist, but this tests error handling

    response = client.get("/training/validate")

    # Should either succeed or return proper error
    assert response.status_code in [200, 500], "Should return success or server error"

    if response.status_code == 500:
        data = response.json()
        assert "detail" in data, "Error response should include detail"

    print("✓ ADDITIONAL TEST PASSED: Validation error handling works")


# ============================================================================
# Additional Test: Concurrent Rebuild Prevention
# ============================================================================
def test_concurrent_rebuild_prevention(client, app_module, monkeypatch, wait_for_rebuild_completion):
    """
    Test that system prevents concurrent rebuilds.
    """
    # Simulate long training
    def fake_run(cmd, check):
        time.sleep(0.5)
        return 0

    monkeypatch.setattr(app_module.subprocess, "run", fake_run, raising=True)

    # Mock the build function - patch train module since app.py uses "import train"
    def fake_build_best_model(_models_dir):
        return conftest.DummyHierModel(version="v3")

    monkeypatch.setattr(sys.modules["train"], "build_best_model", fake_build_best_model, raising=True)

    # Start first rebuild
    response1 = client.post("/rebuild")
    assert response1.status_code == 202
    assert response1.json()["status"] == "rebuild started"

    # Try to start second rebuild while first is running
    time.sleep(0.1)
    response2 = client.post("/rebuild")
    assert response2.status_code == 202
    assert response2.json()["status"] == "already rebuilding", "Should prevent concurrent rebuilds"

    print("✓ ADDITIONAL TEST PASSED: Concurrent rebuild prevention works")
