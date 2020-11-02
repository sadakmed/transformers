import os
import shutil
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from cookiecutter.main import cookiecutter
from transformers.commands import BaseTransformersCLICommand

from ..utils import logging


logger = logging.get_logger(__name__)  # pylint: disable=invalid-name


def add_new_model_command_factory(args):
    return AddNewModelCommand()


class AddNewModelCommand(BaseTransformersCLICommand):
    @staticmethod
    def register_subcommand(parser: ArgumentParser):
        download_parser = parser.add_parser("add-new-model")
        download_parser.set_defaults(func=add_new_model_command_factory)

    def run(self):
        # Ensure that there is no other `cookiecutter-template-xxx` directory in the current working directory
        directories = [directory for directory in os.listdir() if "cookiecutter-template-" in directory[:22]]
        if len(directories) > 0:
            raise ValueError(
                "Several directories starting with `cookiecutter-template-` in current working directory. "
                "Please clean your directory by removing all folders startign with `cookiecutter-template-` or "
                "change your working directory."
            )

        path_to_transformer_root = Path(__file__).parent.parent.parent.parent
        path_to_cookiecutter = path_to_transformer_root / "templates" / "cookiecutter"

        # Execute cookiecutter
        cookiecutter(str(path_to_cookiecutter))

        # Find the model name chosen by the user
        directory = [directory for directory in os.listdir() if "cookiecutter-template-" in directory[:22]][0]
        lowercase_model_name = [file for file in os.listdir(directory) if file.endswith(".rst")][0][:-4]

        shutil.move(
            f"{directory}/configuration_{lowercase_model_name}.py",
            f"{path_to_transformer_root}/src/transformers/configuration_{lowercase_model_name}.py",
        )

        shutil.move(
            f"{directory}/modeling_{lowercase_model_name}.py",
            f"{path_to_transformer_root}/src/transformers/modeling_{lowercase_model_name}.py",
        )

        shutil.move(
            f"{directory}/test_modeling_{lowercase_model_name}.py",
            f"{path_to_transformer_root}/tests/test_modeling_{lowercase_model_name}.py",
        )

        shutil.move(
            f"{directory}/modeling_tf_{lowercase_model_name}.py",
            f"{path_to_transformer_root}/src/transformers/modeling_tf_{lowercase_model_name}.py",
        )

        shutil.move(
            f"{directory}/test_modeling_tf_{lowercase_model_name}.py",
            f"{path_to_transformer_root}/tests/test_modeling_tf_{lowercase_model_name}.py",
        )

        shutil.move(
            f"{directory}/{lowercase_model_name}.rst",
            f"{path_to_transformer_root}/docs/source/model_doc/{lowercase_model_name}.rst",
        )

        shutil.move(
            f"{directory}/tokenization_{lowercase_model_name}.py",
            f"{path_to_transformer_root}/src/transformers/tokenization_{lowercase_model_name}.py",
        )

        from os import fdopen, remove
        from shutil import copymode, move
        from tempfile import mkstemp

        def replace(original_file: str, line_to_copy_below: str, lines_to_copy: List[str]):
            # Create temp file
            fh, abs_path = mkstemp()
            line_found = False
            with fdopen(fh, "w") as new_file:
                with open(original_file) as old_file:
                    for line in old_file:
                        new_file.write(line)
                        if line_to_copy_below in line:
                            line_found = True
                            for line_to_copy in lines_to_copy:
                                new_file.write(line_to_copy)

            if not line_found:
                raise ValueError(f"Line {line_to_copy_below} was not found in file.")

            # Copy the file permissions from the old file to the new file
            copymode(original_file, abs_path)
            # Remove original file
            remove(original_file)
            # Move new file
            move(abs_path, original_file)

        def replace_in_files(path_to_datafile):
            with open(path_to_datafile) as datafile:
                lines_to_copy = []
                for line in datafile:
                    if "# To replace in: " in line and "##" not in line:
                        file_to_replace_in = line.split('"')[1]
                    elif "# Below: " in line and "##" not in line:
                        line_to_copy_below = line.split('"')[1]
                    elif "# End." in line and "##" not in line:
                        replace(file_to_replace_in, line_to_copy_below, lines_to_copy)
                        lines_to_copy = []
                    elif "# Replace with" in line and "##" not in line:
                        lines_to_copy = []
                    elif "##" not in line:
                        lines_to_copy.append(line)

            remove(path_to_datafile)

        replace_in_files(f"{directory}/to_replace_{lowercase_model_name}.py")
        os.rmdir(directory)