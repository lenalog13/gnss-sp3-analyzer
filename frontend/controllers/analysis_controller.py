import numpy as np
from database.db_manager import DBManager

class AnalysisController:

    def __init__(self):
        self.db = DBManager()

    def run_analysis(self, sp3_calc_path, sp3_ref_path, clk_path, satellite):

        # Пока это фейковый backend
        t = np.linspace(0, 24, 200)

        dx = 0.1 * np.sin(t) + np.random.normal(0, 0.01, len(t))
        dy = 0.1 * np.cos(t) + np.random.normal(0, 0.01, len(t))
        dz = 0.05 * np.sin(2 * t) + np.random.normal(0, 0.01, len(t))

        dr = 0.05 * np.sin(t)
        dt = 0.08 * np.cos(t)
        dn = 0.03 * np.sin(2 * t)

        clk = np.random.normal(0, 5, len(t))
        
        exp_id = self.db.create_experiment("Test run")

        return {
            "t": t,
            "dx": dx,
            "dy": dy,
            "dz": dz,
            "dr": dr,
            "dt": dt,
            "dn": dn,
            "clk": clk
        }