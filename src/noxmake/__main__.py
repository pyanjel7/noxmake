import argparse
import sys

from nox import workflow, tasks, _options
from .noxmake import create_session, create_parser

argparse.Namespace


def get_noxmake_version() -> str:
    import importlib.metadata

    return importlib.metadata.version("noxmake")


def load_noxmake(global_config):
    import noxmake.noxmake

    return noxmake.noxmake


def main():
    _options.options.parser_kwargs["description"] = "Noxmake is a nox wrapper for automatic project file generation."

    args = _options.options.parse_args()

    if args.help:
        _options.options.print_help()

        p = create_parser()
        p.usage = argparse.SUPPRESS
        p.description = "\nNoxmake global session options."
        p.print_help()

        return

    if args.version:
        print(get_noxmake_version(), file=sys.stderr)
        return

    create_session(args.posargs)

    return workflow.execute(
        global_config=args,
        workflow=(
            load_noxmake,
            tasks.merge_noxfile_options,
            tasks.discover_manifest,
            tasks.filter_manifest,
            tasks.honor_list_request,
            tasks.run_manifest,
            tasks.print_summary,
            tasks.create_report,
            tasks.final_reduce,
        ),
    )


if __name__ == "__main__":
    main()
