"""
Prompt Selector Module

This module provides a PromptSelector class for dynamically importing prompt modules
and selecting specific versions of prompts.
"""

import importlib
from typing import Dict, Any, Optional
from loguru import logger


class PromptSelector:
    """
    A class for dynamically importing prompt modules and selecting specific versions of prompts.
    
    This class allows for flexible prompt management by dynamically importing
    prompt modules based on workflow type, node name, and version.
    """

    def __init__(self):
        """
        Initialize the PromptSelector.
        
        Currently empty, but can be extended with configuration options
        or caching mechanisms in the future.
        """
        pass

    def get_prompt(self, workflow_type: str, node_name: str,
                   version: str) -> str:
        """
        Get a specific prompt based on workflow type, node name, and version.
        
        Args:
            workflow_type (str): The type of workflow (e.g., "chapter_workflow", "fast_prompts")
            node_name (str): The name of the node (e.g., "writer", "planner", "supervisor")
            version (str): The version of the prompt (e.g., "v1_default", "simple")
            
        Returns:
            str: The requested prompt template
            
        Raises:
            ImportError: If the module cannot be imported
            KeyError: If the version does not exist in the module
            AttributeError: If the PROMPTS dictionary does not exist in the module
        """
        try:
            # Construct the module path
            module_path = f"src.doc_agent.{workflow_type}.{node_name}"

            logger.debug(f"Attempting to import module: {module_path}")

            # Dynamically import the module
            module = importlib.import_module(module_path)

            # First, try to get the PROMPTS dictionary from the module
            if hasattr(module, 'PROMPTS'):
                prompts_dict = module.PROMPTS

                # Check if the version exists
                if version not in prompts_dict:
                    available_versions = list(prompts_dict.keys())
                    raise KeyError(
                        f"Version '{version}' not found in module {module_path}. Available versions: {available_versions}"
                    )

                # Return the requested prompt
                prompt = prompts_dict[version]
                logger.debug(
                    f"Successfully retrieved prompt for {workflow_type}.{node_name}.{version}"
                )
                return prompt
            else:
                # Fallback: look for individual prompt variables
                prompt_vars = self._get_prompt_variables(module, version)
                if prompt_vars:
                    return prompt_vars
                else:
                    # Try to get any available prompt from the module
                    available_prompts = self._get_all_prompt_variables(module)
                    if available_prompts:
                        # Return the first available prompt
                        first_prompt = list(available_prompts.values())[0]
                        logger.debug(
                            f"Using first available prompt for {workflow_type}.{node_name}"
                        )
                        return first_prompt
                    else:
                        raise AttributeError(
                            f"Module {module_path} does not contain PROMPTS dictionary or compatible prompt variables"
                        )

        except ImportError as e:
            logger.error(f"Failed to import module {module_path}: {e}")
            raise ImportError(
                f"Module {module_path} could not be imported: {e}")
        except AttributeError as e:
            logger.error(
                f"Module {module_path} does not have required attributes: {e}")
            raise
        except KeyError as e:
            logger.error(
                f"Version {version} not found in module {module_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting prompt: {e}")
            raise

    def _get_prompt_variables(self, module: Any,
                              version: str) -> Optional[str]:
        """
        Fallback method to get prompt variables from module.
        
        This method looks for individual prompt variables in the module
        when the PROMPTS dictionary is not available.
        
        Args:
            module: The imported module
            version (str): The version to look for
            
        Returns:
            Optional[str]: The prompt if found, None otherwise
        """
        # Common prompt variable patterns
        patterns = [
            f"{version.upper()}_PROMPT",
            f"{version.upper()}_WRITER_PROMPT",
            f"{version.upper()}_PLANNER_PROMPT",
            f"{version.upper()}_SUPERVISOR_PROMPT",
            f"{version.upper()}_CONTENT_PROCESSOR_PROMPT",
            f"{version.upper()}_OUTLINE_GENERATION_PROMPT",
            "WRITER_PROMPT",
            "PLANNER_PROMPT",
            "SUPERVISOR_PROMPT",
            "CONTENT_PROCESSOR_PROMPT",
            "OUTLINE_GENERATION_PROMPT",
            "FAST_WRITER_PROMPT",
            "FAST_PLANNER_PROMPT",
            "FAST_SUPERVISOR_PROMPT",
            "FAST_CONTENT_PROCESSOR_PROMPT",
            "FAST_OUTLINE_GENERATION_PROMPT",
            # Content processor specific patterns
            "RESEARCH_DATA_SUMMARY_PROMPT",
            "KEY_POINTS_EXTRACTION_PROMPT",
            "CONTENT_COMPRESSION_PROMPT",
            # Fast content processor specific patterns
            "FAST_RESEARCH_DATA_SUMMARY_PROMPT",
            "FAST_KEY_POINTS_EXTRACTION_PROMPT",
            "FAST_CONTENT_COMPRESSION_PROMPT"
        ]

        for pattern in patterns:
            if hasattr(module, pattern):
                prompt = getattr(module, pattern)
                logger.debug(f"Found prompt variable: {pattern}")
                return prompt

        return None

    def _get_all_prompt_variables(self, module: Any) -> Dict[str, str]:
        """
        Get all available prompt variables from a module.
        
        Args:
            module: The imported module
            
        Returns:
            Dict[str, str]: Dictionary of prompt variable names and their values
        """
        prompts = {}

        # Common prompt variable patterns
        patterns = [
            "WRITER_PROMPT",
            "PLANNER_PROMPT",
            "SUPERVISOR_PROMPT",
            "CONTENT_PROCESSOR_PROMPT",
            "OUTLINE_GENERATION_PROMPT",
            "FAST_WRITER_PROMPT",
            "FAST_PLANNER_PROMPT",
            "FAST_SUPERVISOR_PROMPT",
            "FAST_CONTENT_PROCESSOR_PROMPT",
            "FAST_OUTLINE_GENERATION_PROMPT",
            # Content processor specific patterns
            "RESEARCH_DATA_SUMMARY_PROMPT",
            "KEY_POINTS_EXTRACTION_PROMPT",
            "CONTENT_COMPRESSION_PROMPT",
            # Fast content processor specific patterns
            "FAST_RESEARCH_DATA_SUMMARY_PROMPT",
            "FAST_KEY_POINTS_EXTRACTION_PROMPT",
            "FAST_CONTENT_COMPRESSION_PROMPT"
        ]

        for pattern in patterns:
            if hasattr(module, pattern):
                prompt = getattr(module, pattern)
                prompts[pattern] = prompt

        return prompts

    def list_available_workflows(self) -> list:
        """
        List available workflow types.
        
        Returns:
            list: List of available workflow types
        """
        return ["prompts", "fast_prompts"]

    def list_available_nodes(self, workflow_type: str) -> list:
        """
        List available nodes for a given workflow type.
        
        Args:
            workflow_type (str): The workflow type
            
        Returns:
            list: List of available nodes
        """
        if workflow_type == "prompts":
            return [
                "writer", "planner", "supervisor", "content_processor",
                "outline_generation"
            ]
        elif workflow_type == "fast_prompts":
            return [
                "writer", "planner", "supervisor", "content_processor",
                "outline_generation"
            ]
        else:
            return []

    def list_available_versions(self, workflow_type: str,
                                node_name: str) -> list:
        """
        List available versions for a given workflow type and node.
        
        Args:
            workflow_type (str): The workflow type
            node_name (str): The node name
            
        Returns:
            list: List of available versions
        """
        try:
            module_path = f"src.doc_agent.{workflow_type}.{node_name}"
            module = importlib.import_module(module_path)

            if hasattr(module, 'PROMPTS'):
                return list(module.PROMPTS.keys())
            else:
                # Return common version patterns
                return ["v1_default", "simple", "detailed", "default"]
        except ImportError:
            return []

    def validate_prompt(self, workflow_type: str, node_name: str,
                        version: str) -> bool:
        """
        Validate if a prompt exists for the given parameters.
        
        Args:
            workflow_type (str): The workflow type
            node_name (str): The node name
            version (str): The version
            
        Returns:
            bool: True if the prompt exists, False otherwise
        """
        try:
            self.get_prompt(workflow_type, node_name, version)
            return True
        except (ImportError, KeyError, AttributeError):
            return False


# Convenience function for easy access
def get_prompt(workflow_type: str, node_name: str, version: str) -> str:
    """
    Convenience function to get a prompt without creating a PromptSelector instance.
    
    Args:
        workflow_type (str): The workflow type
        node_name (str): The node name
        version (str): The version
        
    Returns:
        str: The requested prompt template
    """
    selector = PromptSelector()
    return selector.get_prompt(workflow_type, node_name, version)
