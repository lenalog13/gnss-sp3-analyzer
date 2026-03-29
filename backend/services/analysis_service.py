import numpy as np

class AnalysisService:

    def __init__(self, db):
        self.db = db

    def run_analysis(self, calc_path, ref_path, clk_path, satellite):
        # тут позже подключим парсер

        # пока фейк

        t = np.linspace(0, 24, 200)

        dx = 0.1 * np.sin(t)
        dy = 0.1 * np.cos(t)
        dz = 0.05 * np.sin(2 * t)

        return {
            "t": t,
            "dx": dx,
            "dy": dy,
            "dz": dz
        }