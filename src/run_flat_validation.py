"""Ejecuta los experimentos planos y genera datos, tablas y figuras.

Uso desde la raíz: python src/run_flat_validation.py
"""

import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from flat_klein_gordon import evolve_mode, estimate_frequency

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "flat"
CONFIG = {"mu_hat": 0.7, "L_hat": 2 * math.pi, "A_hat": 1.0,
          "T_hat": 20.0, "safety": 0.8, "dispersion_N": 256,
          "dispersion_modes": [1, 2, 3, 4],
          "convergence_mode": 2, "convergence_N": [64, 128, 256, 512]}


def save_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def scientific(value):
    mantissa, exponent = f"{value:.3e}".split("e")
    return rf"${mantissa}\times10^{{{int(exponent)}}}$"


def save_figure(fig, name):
    fig.savefig(OUT / "figures" / (name + ".pdf"), bbox_inches="tight")
    fig.savefig(OUT / "figures" / (name + ".webp"), dpi=200,
                bbox_inches="tight", pil_kwargs={"lossless": True, "method": 6})
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)
    (OUT / "traces").mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    specifications = sorted(set([(256, j) for j in CONFIG["dispersion_modes"]]
                                + [(n, 2) for n in CONFIG["convergence_N"]]))
    runs, rows = {}, {}
    for n, mode in specifications:
        run = evolve_mode(n, mode, mu=CONFIG["mu_hat"], length=CONFIG["L_hat"],
                          amplitude=CONFIG["A_hat"], final_time=CONFIG["T_hat"],
                          safety=CONFIG["safety"])
        fit = estimate_frequency(run.time, run.modal)
        predicted_trace = CONFIG["A_hat"] * np.cos(run.omega_discrete * run.time)
        recurrence_error = float(np.max(np.abs(run.modal - predicted_trace)))
        frequency_prediction_error = abs(fit["omega_fit"] - run.omega_discrete)
        # Predicción derivada del análisis de Fourier, independiente de la evolución.
        if recurrence_error > 1e-9 or frequency_prediction_error > 1e-6:
            raise AssertionError((n, mode, recurrence_error, frequency_prediction_error))
        row = {"N": n, "j": mode, "h_hat": run.h, "dt_hat": run.dt,
               "steps": len(run.time) - 1, "stability_number": run.stability_number,
               "omega_exact_hat": run.omega_exact,
               "omega_discrete_hat": run.omega_discrete, **fit,
               "frequency_relative_error": abs(fit["omega_fit"] / run.omega_exact - 1),
               "fit_discrete_difference": frequency_prediction_error,
               "modal_recurrence_error": recurrence_error,
               "l2_final": float(run.l2_error[-1]),
               "l2_max": float(np.max(run.l2_error))}
        runs[n, mode], rows[n, mode] = run, row
        np.savetxt(OUT / "traces" / f"N{n}_j{mode}.csv",
                   np.column_stack((run.time, run.modal,
                                    np.cos(run.omega_exact * run.time), run.l2_error)),
                   delimiter=",", header="t_hat,a_numeric,a_exact,l2_error", comments="")

    dispersion = [rows[256, j] for j in CONFIG["dispersion_modes"]]
    convergence = [dict(rows[n, 2]) for n in CONFIG["convergence_N"]]
    for i, row in enumerate(convergence):
        row["observed_order"] = (None if i == 0 else
            math.log(convergence[i-1]["l2_max"] / row["l2_max"], 2))
    if not all(1.9 < row["observed_order"] < 2.1 for row in convergence[1:]):
        raise AssertionError("La prueba modal no muestra el orden dos esperado")
    save_csv(OUT / "dispersion.csv", dispersion)
    save_csv(OUT / "convergence.csv", convergence)

    # Tablas LaTeX generadas desde las mismas filas que los CSV.
    lines = [r"\begin{tabular}{rccc}", r"\toprule",
             r"$j$ & Frecuencia exacta & Frecuencia medida & Error relativo \\",
             r"\midrule"]
    for row in dispersion:
        lines.append(f"{row['j']} & {row['omega_exact_hat']:.8f} & "
                     f"{row['omega_fit']:.8f} & {scientific(row['frequency_relative_error'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "dispersion_table.tex").write_text("\n".join(lines)+"\n", encoding="utf-8")
    lines = [r"\begin{tabular}{rccc}", r"\toprule",
             r"$N$ & Paso temporal & Error máximo & Orden observado \\",
             r"\midrule"]
    for row in convergence:
        order = "---" if row["observed_order"] is None else f"{row['observed_order']:.4f}"
        lines.append(f"{row['N']} & {row['dt_hat']:.6f} & "
                     f"{scientific(row['l2_max'])} & {order} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT / "convergence_table.tex").write_text("\n".join(lines)+"\n", encoding="utf-8")

    base = runs[256, 2]
    fig, axes = plt.subplots(2, 1, figsize=(6.2, 4.7), sharex=True,
                             layout="constrained")
    axes[0].plot(base.time, np.cos(base.omega_exact * base.time),
                 color="#202020", label="Solución exacta", linewidth=1.2)
    stride = max(1, len(base.time) // 110)
    axes[0].plot(base.time[::stride], base.modal[::stride], ".", ms=3,
                 color="#214B87", label="Evolución numérica")
    axes[0].set_ylabel(r"Amplitud del modo $j=2$")
    axes[0].legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), fontsize=8, ncol=2)
    axes[1].plot(base.time, base.modal-np.cos(base.omega_exact*base.time),
                 color="#214B87")
    axes[1].set(xlabel=r"Tiempo adimensional $\widehat t$", ylabel="Diferencia de amplitud")
    save_figure(fig, "evolution")

    modes = np.array(CONFIG["dispersion_modes"])
    measured = np.array([r["omega_fit"] for r in dispersion])
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 3.0), layout="constrained")
    kk = np.linspace(0, modes[-1] ** 2, 100)
    axes[0].plot(kk, kk+CONFIG["mu_hat"]**2, color="#202020", label="Dispersión exacta")
    axes[0].plot(modes**2, measured**2, "o", mfc="none", color="#214B87", label="Medición")
    axes[0].set(xlabel=r"$\widehat k_j^2$", ylabel=r"$\widehat\omega_j^2$")
    axes[0].legend(fontsize=8)
    axes[1].semilogy(modes, [r["frequency_relative_error"] for r in dispersion],
                     "o-", color="#214B87")
    axes[1].set(xlabel="Modo j", ylabel="Error relativo de frecuencia", xticks=modes)
    save_figure(fig, "dispersion")

    hs = np.array([r["h_hat"] for r in convergence])
    errors = np.array([r["l2_max"] for r in convergence])
    fig, ax = plt.subplots(figsize=(5.6, 3.6), layout="constrained")
    ax.loglog(hs, errors, "o-", color="#214B87", label="Error medido")
    ax.loglog(hs, errors[-1]*(hs/hs[-1])**2, "--", color="#555555", label=r"Referencia $h^2$")
    ax.set(xlabel=r"Paso espacial $h=\Delta\widehat x$",
           ylabel="Error máximo del campo")
    ax.set_xticks(hs, labels=[f"{v:.3f}" for v in hs])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.legend()
    save_figure(fig, "convergence")

    source_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [ROOT/"src/flat_klein_gordon.py", Path(__file__)]}
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       text=True).strip()
    manifest = {"run_utc": datetime.now(timezone.utc).isoformat(),
                "configuration": CONFIG, "python": sys.version,
                "platform": platform.platform(),
                "versions": {n: importlib.metadata.version(n)
                             for n in ["numpy", "scipy", "matplotlib", "pillow"]},
                "figure_formats": {"vector": "pdf", "raster": "webp",
                                   "raster_lossless": True, "raster_dpi": 200},
                "base_git_revision": revision, "source_sha256": source_hashes,
                "source_status": "Fuentes locales identificadas por hash; la revisión Git indica el commit de base.",
                "command": "python src/run_flat_validation.py", "runs": len(rows),
                "maximum_modal_recurrence_error": max(r["modal_recurrence_error"] for r in rows.values()),
                "maximum_fit_discrete_difference": max(r["fit_discrete_difference"] for r in rows.values()),
                "observed_orders": [r["observed_order"] for r in convergence[1:]],
                "scope": "Validación plana de modos puros; no valida Schwarzschild ni datos generales."}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (ROOT/"requirements.txt").write_text("\n".join(
        f"{n}=={importlib.metadata.version(n)}" for n in ["numpy", "scipy", "matplotlib", "pillow"])+"\n",
        encoding="utf-8")
    print(json.dumps({"runs": len(rows), "observed_orders": manifest["observed_orders"],
                      "max_fit_discrete_error": manifest["maximum_fit_discrete_difference"],
                      "max_modal_recurrence_error": manifest["maximum_modal_recurrence_error"],
                      "dispersion": [{"j": r["j"], "relative_error": r["frequency_relative_error"]}
                                     for r in dispersion]}, indent=2))


if __name__ == "__main__":
    main()
