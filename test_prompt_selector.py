#!/usr/bin/env python3
"""
Test script for PromptSelector class
"""

import sys
import os
from pathlib import Path

# Add service directory to Python path
current_file = Path(__file__)
service_dir = current_file.parent / "service"
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# Change to service directory for imports
os.chdir(service_dir)

from src.doc_agent.common.prompt_selector import PromptSelector, get_prompt
from loguru import logger


def test_prompt_selector():
    """Test the PromptSelector class"""
    logger.info("🧪 Testing PromptSelector class...")

    # Create a PromptSelector instance
    selector = PromptSelector()

    # Test 1: Get writer prompt from prompts module
    logger.info("📝 Test 1: Getting writer prompt from prompts module")
    try:
        writer_prompt = selector.get_prompt("prompts", "writer", "default")
        logger.success("✅ Successfully retrieved writer prompt")
        logger.debug(f"Prompt length: {len(writer_prompt)} characters")
    except Exception as e:
        logger.error(f"❌ Failed to get writer prompt: {e}")

    # Test 2: Get writer prompt from fast_prompts module
    logger.info("📝 Test 2: Getting writer prompt from fast_prompts module")
    try:
        fast_writer_prompt = selector.get_prompt("fast_prompts", "writer",
                                                 "default")
        logger.success("✅ Successfully retrieved fast writer prompt")
        logger.debug(f"Prompt length: {len(fast_writer_prompt)} characters")
    except Exception as e:
        logger.error(f"❌ Failed to get fast writer prompt: {e}")

    # Test 3: Get planner prompt
    logger.info("📝 Test 3: Getting planner prompt")
    try:
        planner_prompt = selector.get_prompt("prompts", "planner", "default")
        logger.success("✅ Successfully retrieved planner prompt")
        logger.debug(f"Prompt length: {len(planner_prompt)} characters")
    except Exception as e:
        logger.error(f"❌ Failed to get planner prompt: {e}")

    # Test 4: Test convenience function
    logger.info("📝 Test 4: Testing convenience function")
    try:
        supervisor_prompt = get_prompt("prompts", "supervisor", "default")
        logger.success(
            "✅ Successfully retrieved supervisor prompt using convenience function"
        )
        logger.debug(f"Prompt length: {len(supervisor_prompt)} characters")
    except Exception as e:
        logger.error(f"❌ Failed to get supervisor prompt: {e}")

    # Test 5: List available workflows
    logger.info("📝 Test 5: Listing available workflows")
    workflows = selector.list_available_workflows()
    logger.info(f"Available workflows: {workflows}")

    # Test 6: List available nodes
    logger.info("📝 Test 6: Listing available nodes")
    for workflow in workflows:
        nodes = selector.list_available_nodes(workflow)
        logger.info(f"Available nodes for {workflow}: {nodes}")

    # Test 7: Test validation
    logger.info("📝 Test 7: Testing prompt validation")
    valid = selector.validate_prompt("prompts", "writer", "default")
    logger.info(f"Writer prompt validation: {valid}")

    # Test 8: Test error handling
    logger.info("📝 Test 8: Testing error handling")
    try:
        invalid_prompt = selector.get_prompt("nonexistent", "writer",
                                             "default")
        logger.error("❌ Should have raised an error for nonexistent module")
    except ImportError:
        logger.success("✅ Correctly handled nonexistent module")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")


def test_specific_prompts():
    """Test specific prompt retrieval"""
    logger.info("🧪 Testing specific prompt retrieval...")

    selector = PromptSelector()

    # Test different prompt types
    prompt_tests = [
        ("prompts", "writer", "default"),
        ("prompts", "planner", "default"),
        ("prompts", "supervisor", "default"),
        ("prompts", "content_processor", "default"),
        ("prompts", "outline_generation", "default"),
        ("fast_prompts", "writer", "default"),
        ("fast_prompts", "planner", "default"),
        ("fast_prompts", "supervisor", "default"),
        ("fast_prompts", "content_processor", "default"),
        ("fast_prompts", "outline_generation", "default"),
    ]

    for workflow_type, node_name, version in prompt_tests:
        logger.info(f"Testing: {workflow_type}.{node_name}.{version}")
        try:
            prompt = selector.get_prompt(workflow_type, node_name, version)
            logger.success(f"✅ Success: {workflow_type}.{node_name}.{version}")
            logger.debug(f"   Length: {len(prompt)} characters")
        except Exception as e:
            logger.error(
                f"❌ Failed: {workflow_type}.{node_name}.{version} - {e}")


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")

    # Run tests
    test_prompt_selector()
    print("\n" + "=" * 50 + "\n")
    test_specific_prompts()

    logger.success("🎉 All tests completed!")
