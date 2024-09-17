import pipreqs.pipreqs
import nox.logger

from . import _requests

# monkey patches
pipreqs.pipreqs.logging = nox.logger.logger
pipreqs.pipreqs.requests = _requests


def requirements(path=".", local_only=False, mode=">="):
    try:
        candidates = pipreqs.pipreqs.get_all_imports(path)
        candidates = pipreqs.pipreqs.get_pkg_names(candidates)

        packages = pipreqs.pipreqs.get_import_local(candidates) if local_only else pipreqs.pipreqs.get_imports_info(candidates)

        return [(pkg["name"], f"{pkg['version']}") for pkg in packages]
    except Exception:
        pass

    return []
