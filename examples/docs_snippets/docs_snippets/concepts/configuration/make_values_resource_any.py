import os

from dagster import job, make_values_resource, op

# start_file_example
from dagster._core.definitions.resource_output import ResourceOutput


@op
def add_file(context, file_dir: ResourceOutput[str]):
    filename = f"{file_dir}/new_file.txt"
    open(filename, "x", encoding="utf8").close()

    context.log.info(f"Created file: {filename}")


@op
def total_num_files(context, file_dir: ResourceOutput[str]):
    files_in_dir = os.listdir(file_dir)

    context.log.info(f"Total number of files: {len(files_in_dir)}")


@job(resource_defs={"file_dir": make_values_resource()})
def file_dir_job():
    add_file()
    total_num_files()


# end_file_example
