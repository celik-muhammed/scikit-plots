"""Airspeed Velocity benchmark utilities"""

import itertools
import os
import random
import re
import subprocess
import sys
import textwrap
import time


class Benchmark:
    """Base class with sensible options"""


def is_xslow():
    try:
        return int(os.environ.get("SCIPY_XSLOW", "0"))
    except ValueError:
        return False


class LimitedParamBenchmark(Benchmark):
    """
    Limits parameter combinations to `max_number` choices, chosen
    pseudo-randomly with fixed seed.
    Raises NotImplementedError (skip) if not in active set.
    """

    num_param_combinations = 0

    def setup(self, *args, **kwargs):
        slow = is_xslow()

        if slow:
            # no need to skip
            return

        param_seed = kwargs.pop("param_seed", None)
        if param_seed is None:
            param_seed = 1

        params = kwargs.pop("params", None)
        if params is None:
            params = self.params

        num_param_combinations = kwargs.pop("num_param_combinations", None)
        if num_param_combinations is None:
            num_param_combinations = self.num_param_combinations

        all_choices = list(itertools.product(*params))

        rng = random.Random(param_seed)
        rng.shuffle(all_choices)
        active_choices = all_choices[:num_param_combinations]

        if args not in active_choices:
            raise NotImplementedError("skipped")


def get_max_rss_bytes(rusage):
    """Extract the max RSS value in bytes."""
    if not rusage:
        return None

    if sys.platform.startswith("linux"):
        # On Linux getrusage() returns ru_maxrss in kilobytes
        # https://man7.org/linux/man-pages/man2/getrusage.2.html
        return rusage.ru_maxrss * 1024
    if sys.platform == "darwin":
        # on macOS ru_maxrss is in bytes
        return rusage.ru_maxrss
    # Unknown, just return whatever is here.
    return rusage.ru_maxrss


def run_monitored_wait4(code):
    """
    Run code in a new Python process, and monitor peak memory usage.

    Returns
    -------
    duration : float
        Duration in seconds (including Python startup time)
    peak_memusage : int
        Peak memory usage in bytes of the child Python process

    Notes
    -----
    Works on Unix platforms (Linux, macOS) that have `os.wait4()`.

    """
    code = textwrap.dedent(code)

    start = time.time()
    process = subprocess.Popen([sys.executable, "-c", code])
    pid, returncode, rusage = os.wait4(process.pid, 0)
    duration = time.time() - start
    max_rss_bytes = get_max_rss_bytes(rusage)

    if returncode != 0:
        raise AssertionError("Running failed:\n%s" % code)

    return duration, max_rss_bytes


def run_monitored_proc(code):
    """
    Run code in a new Python process, and monitor peak memory usage.

    Returns
    -------
    duration : float
        Duration in seconds (including Python startup time)
    peak_memusage : float
        Peak memory usage (rough estimate only) in bytes

    """
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Peak memory monitoring only works on Linux")

    code = textwrap.dedent(code)
    process = subprocess.Popen([sys.executable, "-c", code])

    peak_memusage = -1

    start = time.time()
    while True:
        ret = process.poll()
        if ret is not None:
            break

        with open("/proc/%d/status" % process.pid) as f:
            procdata = f.read()

        m = re.search(r"VmRSS:\s*(\d+)\s*kB", procdata, re.DOTALL | re.IGNORECASE)
        if m is not None:
            memusage = float(m.group(1)) * 1e3
            peak_memusage = max(memusage, peak_memusage)

        time.sleep(0.01)

    process.wait()

    duration = time.time() - start

    if process.returncode != 0:
        raise AssertionError("Running failed:\n%s" % code)

    return duration, peak_memusage


def run_monitored(code):
    """
    Run code in a new Python process, and monitor peak memory usage.

    Returns
    -------
    duration : float
        Duration in seconds (including Python startup time)
    peak_memusage : float or int
        Peak memory usage (rough estimate only) in bytes

    """
    if hasattr(os, "wait4"):
        return run_monitored_wait4(code)
    return run_monitored_proc(code)


def get_mem_info():
    """Get information about available memory"""
    import psutil

    vm = psutil.virtual_memory()
    return {
        "memtotal": vm.total,
        "memavailable": vm.available,
    }


def set_mem_rlimit(max_mem=None):
    """Set address space rlimit"""
    import resource

    if max_mem is None:
        mem_info = get_mem_info()
        max_mem = int(mem_info["memtotal"] * 0.7)
    cur_limit = resource.getrlimit(resource.RLIMIT_AS)
    if cur_limit[0] > 0:
        max_mem = min(max_mem, cur_limit[0])

    try:
        resource.setrlimit(resource.RLIMIT_AS, (max_mem, cur_limit[1]))
    except ValueError:
        # on macOS may raise: current limit exceeds maximum limit
        pass


def with_attributes(**attrs):
    def decorator(func):
        for key, value in attrs.items():
            setattr(func, key, value)
        return func

    return decorator


class safe_import:
    def __enter__(self):
        self.error = False
        return self

    def __exit__(self, type_, value, traceback):
        if type_ is not None:
            self.error = True
            suppress = not (
                os.getenv("SCIPY_ALLOW_BENCH_IMPORT_ERRORS", "1").lower()
                in ("0", "false")
                or not issubclass(type_, ImportError)
            )
            return suppress
