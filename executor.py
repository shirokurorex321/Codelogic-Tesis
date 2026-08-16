"""Ejecuta código del estudiante en un entorno controlado. Multiplataforma.

Modos de ejecución (elegidos automáticamente):

1. LINUX + bubblewrap (producción) — sandbox completo:
   - filesystem read-only (solo /usr y /etc/alternatives), tmpfs en /tmp,
     --unshare-all (sin red, sin PID host, sin IPC), --die-with-parent,
     --new-session, --cap-drop ALL.
   - rlimits vía preexec_fn: CPU 5s, RAM 256MB, sin core dump, archivos máx 10MB.

2. WINDOWS / Linux sin bwrap (desarrollo) — ejecución directa SIN sandbox:
   - Solo se habilita si EXECUTOR_ALLOW_UNSAFE=true en el .env.
   - Protecciones disponibles: timeout wall-clock, python -I (modo aislado),
     stdout/stderr truncados, proceso terminado al expirar.
   - NO usar este modo si la plataforma está expuesta a internet (túnel).

En ambos modos: wall-clock timeout y stdout/stderr truncados a 10KB.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

IS_WINDOWS = os.name == "nt"

if not IS_WINDOWS:
    import resource  # solo existe en Unix

# Límites
TIMEOUT_RUN = 5            # segundos wall-clock para ejecutar
# En Windows la primera compilación de MinGW es lenta (antivirus escanea
# los binarios y headers); en Linux 10s sobran.
TIMEOUT_COMPILE = 30 if IS_WINDOWS else 10
CPU_SECONDS = 5            # rlimit CPU (solo Linux)
MEMORY_BYTES = 256 * 1024 * 1024   # 256 MB (solo Linux)
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB (solo Linux)
MAX_OUTPUT = 10_000        # truncar stdout/stderr en bytes

ALLOW_UNSAFE = os.getenv("EXECUTOR_ALLOW_UNSAFE", "false").lower() == "true"
HAS_BWRAP = (not IS_WINDOWS) and shutil.which("bwrap") is not None

# En Windows evitamos que aparezcan ventanas de consola por cada ejecución
_WIN_FLAGS = 0x08000000 if IS_WINDOWS else 0  # CREATE_NO_WINDOW


def _find_python() -> str:
    """Intérprete de Python para el código del estudiante."""
    if HAS_BWRAP:
        return "python3"  # dentro del sandbox se resuelve en /usr/bin
    return sys.executable  # el mismo intérprete de la app (Windows/dev)


_TOOL_CACHE: dict = {}


def _find_tool(name: str) -> str | None:
    """Busca php / g++ en el PATH (y en los paquetes de winget en Windows)."""
    if HAS_BWRAP:
        return name  # dentro del sandbox
    if name in _TOOL_CACHE:
        return _TOOL_CACHE[name]
    found = shutil.which(name)
    if not found and IS_WINDOWS:
        # winget agrega sus alias al PATH, pero procesos ya abiertos no lo ven;
        # buscamos también dentro de sus carpetas de paquetes.
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        candidates = [local / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"]
        pkgs = local / "Microsoft" / "WinGet" / "Packages"
        if pkgs.is_dir():
            candidates += sorted(pkgs.glob(f"*/{name}.exe"))
            candidates += sorted(pkgs.glob(f"*/mingw64/bin/{name}.exe"))
        for c in candidates:
            if c.is_file():
                found = str(c)
                break
    _TOOL_CACHE[name] = found
    return found


def _bwrap_args(workdir: str) -> list:
    """Argumentos base de bubblewrap. workdir se monta como /work writable."""
    return [
        "bwrap",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/etc/alternatives", "/etc/alternatives",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
        "--symlink", "usr/bin", "/bin",
        "--symlink", "usr/sbin", "/sbin",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--bind", workdir, "/work",
        "--chdir", "/work",
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--cap-drop", "ALL",
        "--setenv", "PATH", "/usr/bin:/usr/sbin",
        "--setenv", "HOME", "/work",
        "--setenv", "LANG", "C.UTF-8",
    ]


def _set_rlimits():
    """preexec_fn (solo Linux): aplicado al hijo (bwrap) y heredado por nietos.

    OJO: RLIMIT_NPROC es global por UID en el kernel, no por subárbol —
    si lo aplicamos aquí, bwrap mismo falla al fork-ear cuando ya hay
    procesos del usuario corriendo. La defensa anti fork-bomb la dan
    --die-with-parent + el timeout wall-clock: cuando bwrap muere por
    timeout, el kernel SIGKILL a toda la descendencia.
    """
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))


def _truncate(raw: bytes) -> tuple[str, bool]:
    if raw is None:
        return "", False
    if len(raw) > MAX_OUTPUT:
        return raw[:MAX_OUTPUT].decode("utf-8", errors="replace"), True
    return raw.decode("utf-8", errors="replace"), False


def _not_available(msg: str) -> dict:
    return {
        "stdout": "",
        "stderr": msg,
        "exit_code": -1,
        "timed_out": False,
        "truncated": False,
    }


def _run_process(cmd: list, workdir: str, stdin: str = "", timeout: int = TIMEOUT_RUN) -> dict:
    """Ejecuta cmd (ya envuelto en bwrap si aplica) con timeout y truncado."""
    kwargs = {
        "input": (stdin or "").encode("utf-8"),
        "capture_output": True,
        "timeout": timeout,
        "check": False,
        "cwd": workdir,
    }
    if HAS_BWRAP:
        kwargs["preexec_fn"] = _set_rlimits
        kwargs.pop("cwd")  # bwrap ya hace --chdir /work
    if IS_WINDOWS:
        kwargs["creationflags"] = _WIN_FLAGS

    try:
        proc = subprocess.run(cmd, **kwargs)
        out, out_trunc = _truncate(proc.stdout)
        err, err_trunc = _truncate(proc.stderr)
        return {
            "stdout": out,
            "stderr": err,
            "exit_code": proc.returncode,
            "timed_out": False,
            "truncated": out_trunc or err_trunc,
        }
    except subprocess.TimeoutExpired as e:
        out, _ = _truncate(e.stdout)
        err, _ = _truncate(e.stderr)
        suffix = f"\n[⏱ Tiempo de ejecución superado ({timeout}s) — proceso terminado]"
        return {
            "stdout": out,
            "stderr": (err + suffix) if err else suffix.lstrip("\n"),
            "exit_code": -1,
            "timed_out": True,
            "truncated": False,
        }
    except FileNotFoundError as e:
        return _not_available(f"Herramienta no disponible en este servidor: {e}")


def _run_sandboxed(cmd: list, workdir: str, stdin: str = "", timeout: int = TIMEOUT_RUN) -> dict:
    """Punto común: decide sandbox (Linux+bwrap) o ejecución directa (dev)."""
    if HAS_BWRAP:
        return _run_process(_bwrap_args(workdir) + cmd, workdir, stdin=stdin, timeout=timeout)
    if not ALLOW_UNSAFE:
        return _not_available(
            "La ejecución de código está deshabilitada en este servidor "
            "(no hay sandbox disponible). Para desarrollo local, define "
            "EXECUTOR_ALLOW_UNSAFE=true en el archivo .env."
        )
    return _run_process(cmd, workdir, stdin=stdin, timeout=timeout)


def execute_python(code: str, stdin: str = "") -> dict:
    with tempfile.TemporaryDirectory(prefix="codelogic-py-") as tmp:
        if not IS_WINDOWS:
            os.chmod(tmp, 0o755)
        (Path(tmp) / "main.py").write_text(code, encoding="utf-8")
        py = _find_python()
        script = "/work/main.py" if HAS_BWRAP else str(Path(tmp) / "main.py")
        return _run_sandboxed([py, "-I", script], tmp, stdin=stdin)


def execute_php(code: str, stdin: str = "") -> dict:
    php = _find_tool("php")
    if php is None:
        return _not_available(
            "PHP no está instalado en este servidor. "
            "En Windows puedes instalarlo con: winget install PHP.PHP.8.4"
        )
    with tempfile.TemporaryDirectory(prefix="codelogic-php-") as tmp:
        if not IS_WINDOWS:
            os.chmod(tmp, 0o755)
        if not code.lstrip().startswith("<?"):
            code = "<?php\n" + code
        (Path(tmp) / "main.php").write_text(code, encoding="utf-8")
        script = "/work/main.php" if HAS_BWRAP else str(Path(tmp) / "main.php")
        return _run_sandboxed([php, "-d", "display_errors=1", script], tmp, stdin=stdin)


def execute_cpp(code: str, stdin: str = "") -> dict:
    gpp = _find_tool("g++")
    if gpp is None:
        return _not_available(
            "El compilador g++ no está instalado en este servidor. "
            "En Windows puedes instalarlo con: winget install MSYS2.MSYS2 "
            "(y luego instalar mingw-w64-x86_64-gcc) o usar WinLibs."
        )
    with tempfile.TemporaryDirectory(prefix="codelogic-cpp-") as tmp:
        if not IS_WINDOWS:
            os.chmod(tmp, 0o755)
        (Path(tmp) / "main.cpp").write_text(code, encoding="utf-8")

        exe_name = "main.exe" if IS_WINDOWS else "main"
        if HAS_BWRAP:
            src, exe = "/work/main.cpp", "/work/main"
        else:
            src, exe = str(Path(tmp) / "main.cpp"), str(Path(tmp) / exe_name)

        compile_result = _run_sandboxed(
            [gpp, "-O0", "-std=c++17", "-o", exe, src],
            tmp,
            timeout=TIMEOUT_COMPILE,
        )
        if compile_result["timed_out"]:
            return {
                "stdout": "",
                "stderr": f"⏱ La compilación tardó demasiado (>{TIMEOUT_COMPILE}s) y fue cancelada.",
                "exit_code": -1,
                "timed_out": True,
                "truncated": False,
            }
        if compile_result["exit_code"] != 0:
            return {
                "stdout": "",
                "stderr": "❌ Error de compilación:\n" + (compile_result["stderr"] or "(sin detalles)"),
                "exit_code": compile_result["exit_code"],
                "timed_out": False,
                "truncated": compile_result["truncated"],
            }
        if not (Path(tmp) / exe_name).exists():
            return {
                "stdout": "",
                "stderr": "❌ El compilador terminó OK pero no se encontró el binario.",
                "exit_code": -1,
                "timed_out": False,
                "truncated": False,
            }
        return _run_sandboxed([exe], tmp, stdin=stdin)


_RUNNERS = {
    "python": execute_python,
    "cpp": execute_cpp,
    "php": execute_php,
}


def available_languages() -> dict:
    """Qué lenguajes puede ejecutar este servidor (para la UI)."""
    if HAS_BWRAP:
        return {"python": True, "cpp": True, "php": True, "sandboxed": True}
    if not ALLOW_UNSAFE:
        return {"python": False, "cpp": False, "php": False, "sandboxed": False}
    return {
        "python": True,
        "cpp": shutil.which("g++") is not None,
        "php": shutil.which("php") is not None,
        "sandboxed": False,
    }


def run(language: str, code: str, stdin: str = "") -> dict:
    """Punto de entrada público. Devuelve siempre el mismo shape."""
    if language not in _RUNNERS:
        return {
            "stdout": "",
            "stderr": f"Lenguaje no soportado: {language!r}. Usa python, cpp o php.",
            "exit_code": -1,
            "timed_out": False,
            "truncated": False,
        }
    if not code or not code.strip():
        return {
            "stdout": "",
            "stderr": "El código está vacío.",
            "exit_code": -1,
            "timed_out": False,
            "truncated": False,
        }
    return _RUNNERS[language](code, stdin)
