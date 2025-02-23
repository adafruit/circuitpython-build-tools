import pathlib
from difflib import unified_diff
import click
from ..munge import munge


@click.command
@click.option("--diff/--no-diff", "show_diff", default=False)
@click.option("--munged-version", default="munged-version")
@click.argument("input", type=click.Path(exists=True))
@click.argument("output", type=click.File("w", encoding="utf-8"), default="-")
def main(show_diff, munged_version, input, output):
    input_path = pathlib.Path(input)
    munged = munge(input, munged_version)
    if show_diff:
        old_lines = input_path.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = munged.splitlines(keepends=True)
        output.writelines(
            unified_diff(
                old_lines,
                new_lines,
                fromfile=input,
                tofile=str(input_path.with_suffix(".munged.py")),
            )
        )
    else:
        output.write(munged)
