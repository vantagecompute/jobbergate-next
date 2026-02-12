"""
Example Jobbergate Application with Dynamic Choices

This example demonstrates how to create questions with dynamically generated
choices based on:
1. Filesystem state (listing files/directories)
2. Previous answers (conditional choices)
3. Runtime code execution

The choices are re-evaluated each time questions are loaded, ensuring they
always reflect the current state.
"""

import os
from jobbergate_cli.subapps.applications.application_base import JobbergateApplicationBase
from jobbergate_cli.subapps.applications.questions import List, Text, Confirm


class JobbergateApplication(JobbergateApplicationBase):
    """Application demonstrating dynamic question choices."""

    def mainflow(self, data=None):
        """
        Main workflow with dynamic choices.
        
        Demonstrates:
        - Filesystem-based choices
        - Conditional questions based on previous answers
        """
        if data is None:
            data = {}

        questions = []

        # Example 1: Dynamic choices from filesystem
        def get_directories(answers):
            """Get list of directories in user's home."""
            home = os.path.expanduser("~")
            try:
                items = os.listdir(home)
                dirs = [d for d in items if os.path.isdir(os.path.join(home, d))]
                return dirs[:10]  # Limit to first 10
            except (PermissionError, FileNotFoundError):
                return ["Documents", "Downloads", "Desktop"]  # Fallback

        questions.append(
            List(
                "workdir",
                message="Select a working directory from your home folder:",
                choices=get_directories
            )
        )

        # Example 2: Ask if user wants to process files
        questions.append(
            Confirm(
                "process_files",
                message="Do you want to process specific files?",
                default=False
            )
        )

        # Example 3: Conditional question - only if process_files is True
        if data.get("process_files", False):
            def get_files_in_workdir(answers):
                """Get files from selected working directory."""
                workdir = answers.get("workdir", "~")
                full_path = os.path.expanduser(os.path.join("~", workdir))
                try:
                    items = os.listdir(full_path)
                    files = [f for f in items if os.path.isfile(os.path.join(full_path, f))]
                    return files if files else ["(no files found)"]
                except (PermissionError, FileNotFoundError):
                    return ["(unable to read directory)"]

            questions.append(
                List(
                    "selected_file",
                    message="Select a file to process:",
                    choices=get_files_in_workdir
                )
            )

        # Example 4: Environment-based choices
        def get_available_partitions(answers):
            """Get available SLURM partitions (simulated)."""
            # In a real scenario, you might run: sinfo -o "%P" --noheader
            # For this example, we'll simulate based on environment
            if os.path.exists("/etc/slurm"):
                return ["compute", "gpu", "highmem", "debug"]
            else:
                return ["local", "standard"]

        questions.append(
            List(
                "partition",
                message="Select a compute partition:",
                choices=get_available_partitions
            )
        )

        # Example 5: Choices based on previous answer
        if data.get("partition") == "gpu":
            def get_gpu_types(answers):
                """Get available GPU types."""
                # This could query actual hardware
                return ["v100", "a100", "h100"]

            questions.append(
                List(
                    "gpu_type",
                    message="Select GPU type:",
                    choices=get_gpu_types
                )
            )

        return questions
