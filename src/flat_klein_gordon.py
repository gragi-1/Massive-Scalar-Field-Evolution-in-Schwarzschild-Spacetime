"""Validación modal de Klein--Gordon plana, en variables adimensionales.

Phi_tt = Phi_xx - mu**2 Phi, con periodicidad y velocidad inicial cero.
El esquema usa diferencias centradas de orden dos en espacio y tiempo.
"""

from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import minimize_scalar


@dataclass
class ModeRun:
    n: int
    mode: int
    h: float
    dt: float
    stability_number: float
    omega_exact: float
    omega_discrete: float
    x: np.ndarray
    time: np.ndarray
    modal: np.ndarray
    l2_error: np.ndarray
    final_field: np.ndarray
    initial_field: np.ndarray


def evolve_mode(n, mode, *, mu=0.7, length=2 * math.pi,
                amplitude=1.0, final_time=20.0, safety=0.8):
    """Evoluciona una malla periódica completa; no integra solo su amplitud.

    El primer paso se inicializa con Taylor y la aceleración semidiscreta.
    safety limita dt*sqrt(mu**2 + 4/h**2) a menos de 2.
    """
    if not isinstance(n, int) or n < 8:
        raise ValueError("n debe ser un entero >= 8")
    if not isinstance(mode, int) or not 0 <= mode < n / 2:
        raise ValueError("El modo debe estar resuelto y por debajo de Nyquist")
    if not all(math.isfinite(v) for v in (mu, length, amplitude, final_time, safety)):
        raise ValueError("Los parámetros deben ser finitos")
    if mu <= 0 or length <= 0 or final_time <= 0 or not 0 < safety < 1:
        raise ValueError("Se requieren mu,L,T>0 y 0<safety<1")
    h = length / n
    x = np.arange(n) * h
    k = 2 * math.pi * mode / length
    dt_bound = 2 / math.sqrt(mu * mu + 4 / (h * h))
    steps = max(2, math.ceil(final_time / (safety * dt_bound)))
    dt = final_time / steps
    stability_number = dt * math.sqrt(mu * mu + 4 / (h * h))
    if not stability_number < 2:
        raise ValueError("Paso temporal fuera de la región estable estricta")
    time = np.arange(steps + 1) * dt
    basis = np.cos(k * x)
    basis_norm2 = float(basis @ basis)
    initial = amplitude * basis
    omega_exact = math.sqrt(k * k + mu * mu)
    omega_h = math.sqrt(mu * mu + 4 * math.sin(k * h / 2) ** 2 / (h * h))
    omega_discrete = 2 / dt * math.asin(dt * omega_h / 2)
    modal = np.empty(steps + 1)
    errors = np.empty(steps + 1)

    def acceleration(field):
        return (np.roll(field, -1) - 2 * field + np.roll(field, 1)) / h**2 - mu**2 * field

    def diagnose(index, field):
        modal[index] = float(field @ basis / basis_norm2)
        exact = initial * math.cos(omega_exact * time[index])
        errors[index] = math.sqrt(h * float((field - exact) @ (field - exact)))

    previous = initial.copy()
    current = previous + 0.5 * dt * dt * acceleration(previous)
    diagnose(0, previous)
    diagnose(1, current)
    for index in range(1, steps):
        following = 2 * current - previous + dt * dt * acceleration(current)
        previous, current = current, following
        diagnose(index + 1, current)
    return ModeRun(n, mode, h, dt, stability_number, omega_exact,
                   omega_discrete, x, time, modal, errors, current.copy(), initial)


def estimate_frequency(time, values):
    """Estima omega desde la señal, sin recibir su frecuencia teórica.

    La FFT selecciona una banda de búsqueda; dentro de ella se minimiza
    el residuo de a*cos(omega*t)+b*sin(omega*t)+d por mínimos cuadrados.
    """
    dt = float(time[1] - time[0])
    spectrum = np.abs(np.fft.rfft(values - np.mean(values)))
    frequencies = 2 * math.pi * np.fft.rfftfreq(len(values), dt)
    peak = int(np.argmax(spectrum[1:]) + 1)
    spacing = float(frequencies[1])
    center = float(frequencies[peak])
    lower = max(spacing * 0.1, center - spacing)
    upper = min(math.pi / dt * 0.99, center + spacing)

    def linear_fit(omega):
        design = np.column_stack((np.cos(omega * time), np.sin(omega * time),
                                  np.ones_like(time)))
        coefficients = np.linalg.lstsq(design, values, rcond=None)[0]
        residual = values - design @ coefficients
        return float(residual @ residual), coefficients

    fit = minimize_scalar(lambda omega: linear_fit(omega)[0],
                          bounds=(lower, upper), method="bounded",
                          options={"xatol": 1e-13, "maxiter": 200})
    if not fit.success:
        raise RuntimeError("No convergió el ajuste de frecuencia")
    cost, coefficients = linear_fit(float(fit.x))
    return {"omega_fit": float(fit.x), "fit_rms": math.sqrt(cost / len(values)),
            "fit_cos": float(coefficients[0]), "fit_sin": float(coefficients[1]),
            "fit_offset": float(coefficients[2]), "fft_omega": center,
            "fit_lower": lower, "fit_upper": upper}
